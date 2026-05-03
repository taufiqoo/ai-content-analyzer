"""
Celery Tasks — Pipeline steps that run in background workers.
"""
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
from app.celery_app import celery_app
from app.config import settings
from app.models import Tweet, Script, NicheConfig, PipelineJob
from app.services import (
    TwitterScraper,
    extract_article,
    score_relevance,
    generate_scripts_for_content,
)
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool


def make_session():
    """
    Create a fresh async DB session for each Celery task.

    We intentionally create a new engine per task (using NullPool) to avoid
    the 'Event loop is closed' error that occurs when Celery forks worker
    processes — the parent's asyncpg connections become unusable in the fork.
    """
    engine = create_async_engine(
        settings.DATABASE_URL,
        poolclass=NullPool,
    )
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def run_async(coro):
    """Run async coroutine in sync Celery context."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()
        asyncio.set_event_loop(None)


@celery_app.task(bind=True, name="tasks.run_full_pipeline")
def run_full_pipeline(self, job_id: str, source: str = "bookmarks", limit: int = 30):
    """
    Full pipeline: Scrape → Extract → Score → Generate Scripts.
    """
    async def _run():
        async with make_session()() as db:
            logger.info(f"[Pipeline] ▶ Job {job_id[:8]}... started | source={source} limit={limit}")

            # Update job status
            await db.execute(
                update(PipelineJob)
                .where(PipelineJob.id == job_id)
                .values(celery_task_id=self.request.id, step="scraping", status="running")
            )
            await db.commit()

            # Get active niche config
            result = await db.execute(
                select(NicheConfig).where(NicheConfig.is_active == True).limit(1)
            )
            niche = result.scalar_one_or_none()
            if not niche:
                logger.error("[Pipeline] ✗ No active niche config found. Aborting.")
                await db.execute(
                    update(PipelineJob)
                    .where(PipelineJob.id == job_id)
                    .values(status="failed", error_message="No active niche config found")
                )
                await db.commit()
                return

            logger.info(f"[Pipeline] 🎯 Active niche: {niche.name}")

            # Step 1: Scrape Twitter
            logger.info(f"[Pipeline] 🐦 STEP 1/4 — Scraping Twitter {source} (max {limit} tweets)...")
            logger.info("[Pipeline]    → Opening headless browser & logging in to Twitter/X...")
            scraper = TwitterScraper()
            if source == "bookmarks":
                raw_tweets = await scraper.scrape_bookmarks(limit=limit)
            else:
                raw_tweets = await scraper.scrape_home_timeline(limit=limit)

            logger.info(f"[Pipeline]    → Scraped {len(raw_tweets)} tweets from Twitter")

            tweets_fetched = 0
            duplicates_skipped = 0
            for raw in raw_tweets:
                # Check duplicate
                existing = await db.execute(
                    select(Tweet).where(Tweet.tweet_id == raw["tweet_id"])
                )
                if existing.scalar_one_or_none():
                    duplicates_skipped += 1
                    continue

                tweet = Tweet(
                    tweet_id=raw["tweet_id"],
                    author_username=raw.get("author_username"),
                    content=raw.get("content"),
                    url=raw.get("url"),
                    has_article_link=raw.get("has_article_link", False),
                    article_url=raw.get("article_url"),
                    niche_config_id=niche.id,
                    status="pending",
                )
                db.add(tweet)
                tweets_fetched += 1

            await db.commit()
            logger.info(f"[Pipeline]    ✓ {tweets_fetched} new tweets saved | {duplicates_skipped} duplicates skipped")

            # Update progress
            await db.execute(
                update(PipelineJob)
                .where(PipelineJob.id == job_id)
                .values(step="extracting_articles", tweets_fetched=tweets_fetched)
            )
            await db.commit()

            # Step 2: Extract articles for tweets with links
            result = await db.execute(
                select(Tweet).where(
                    Tweet.niche_config_id == niche.id,
                    Tweet.status == "pending",
                    Tweet.has_article_link == True,
                    Tweet.article_content == None,
                )
            )
            pending_tweets = result.scalars().all()
            logger.info(f"[Pipeline] 📰 STEP 2/4 — Extracting articles ({len(pending_tweets)} tweets have article links)...")

            articles_extracted = 0
            for i, tweet in enumerate(pending_tweets):
                if tweet.article_url:
                    logger.info(f"[Pipeline]    → [{i+1}/{len(pending_tweets)}] Fetching: {tweet.article_url[:80]}")
                    article_text = await extract_article(tweet.article_url)
                    if article_text:
                        tweet.article_content = article_text
                        articles_extracted += 1
                        logger.info(f"[Pipeline]       ✓ Extracted {len(article_text)} chars")
                    else:
                        logger.warning(f"[Pipeline]       ⚠ Could not extract article content")

            await db.commit()
            logger.info(f"[Pipeline]    ✓ {articles_extracted} articles extracted")

            # Update progress
            await db.execute(
                update(PipelineJob)
                .where(PipelineJob.id == job_id)
                .values(step="scoring_relevance")
            )
            await db.commit()

            # Step 3: Score relevance
            result = await db.execute(
                select(Tweet).where(
                    Tweet.niche_config_id == niche.id,
                    Tweet.status == "pending",
                )
            )
            pending_tweets = result.scalars().all()
            logger.info(f"[Pipeline] 🧠 STEP 3/4 — Scoring relevance for {len(pending_tweets)} tweets with AI...")

            tweets_relevant = 0
            for i, tweet in enumerate(pending_tweets):
                content_to_score = tweet.article_content or tweet.content or ""
                if not content_to_score.strip():
                    tweet.status = "irrelevant"
                    logger.info(f"[Pipeline]    → [{i+1}/{len(pending_tweets)}] @{tweet.author_username}: SKIP (no content)")
                    continue

                try:
                    score, reason = score_relevance(
                        content=content_to_score,
                        niche_name=niche.name,
                        keywords=niche.keywords or [],
                    )
                    tweet.relevance_score = score
                    tweet.relevance_reason = reason
                    if score >= 0.65:
                        tweet.status = "relevant"
                        tweets_relevant += 1
                        logger.info(f"[Pipeline]    → [{i+1}/{len(pending_tweets)}] @{tweet.author_username}: ✅ RELEVANT (score={score:.2f}) — {reason[:60]}")
                    else:
                        tweet.status = "irrelevant"
                        logger.info(f"[Pipeline]    → [{i+1}/{len(pending_tweets)}] @{tweet.author_username}: ❌ IRRELEVANT (score={score:.2f}) — {reason[:60]}")
                except Exception as e:
                    logger.error(f"[Pipeline]    → [{i+1}/{len(pending_tweets)}] @{tweet.author_username}: ✗ Scoring failed: {e}")
                    # Biarkan status tetap 'pending' agar bisa di-retry di run berikutnya
                    # tweet.status = "irrelevant"  ← jangan mark irrelevant jika hanya rate limit

                # Jeda natural antar request AI agar tidak kena rate limit
                await asyncio.sleep(5)

            await db.commit()
            logger.info(f"[Pipeline]    ✓ {tweets_relevant}/{len(pending_tweets)} tweets passed relevance filter")

            # Update progress
            await db.execute(
                update(PipelineJob)
                .where(PipelineJob.id == job_id)
                .values(step="generating_scripts", tweets_relevant=tweets_relevant)
            )
            await db.commit()

            # Step 4: Generate scripts for relevant tweets
            result = await db.execute(
                select(Tweet).where(
                    Tweet.niche_config_id == niche.id,
                    Tweet.status == "relevant",
                )
            )
            relevant_tweets = result.scalars().all()
            logger.info(f"[Pipeline] ✍️  STEP 4/4 — Generating scripts for {len(relevant_tweets)} relevant tweets...")

            scripts_generated = 0
            for i, tweet in enumerate(relevant_tweets):
                content_for_script = tweet.article_content or tweet.content or ""
                if not content_for_script.strip():
                    continue

                logger.info(f"[Pipeline]    → [{i+1}/{len(relevant_tweets)}] @{tweet.author_username}: calling AI (3 angles)...")
                try:
                    scripts_data = generate_scripts_for_content(
                        article_content=content_for_script,
                        niche_name=niche.name,
                        niche_keywords=niche.keywords or [],
                        custom_rules=niche.script_rules,
                        angles=["hero", "tips_trick", "controversial"],
                        duration_seconds=niche.target_duration_seconds or 60,
                    )

                    for sd in scripts_data:
                        script = Script(
                            tweet_id=tweet.id,
                            angle=sd.get("angle"),
                            hook=sd.get("hook", ""),
                            body=sd.get("body", ""),
                            cta=sd.get("cta", ""),
                            full_script=sd.get("full_script", ""),
                            hook_formula_used=sd.get("hook_formula_used"),
                            duration_estimate=sd.get("estimated_duration_seconds"),
                            naturalness_score=sd.get("naturalness_score"),
                            claude_model=sd.get("claude_model"),
                            status="draft",
                        )
                        db.add(script)
                        scripts_generated += 1
                        logger.info(f"[Pipeline]       ✓ [{sd.get('angle')}] hook_formula={sd.get('hook_formula_used')} naturalness={sd.get('naturalness_score')}")

                    if scripts_data:
                        tweet.status = "scripted"
                        await db.commit()
                    else:
                        logger.warning(f"[Pipeline]    → [{i+1}/{len(relevant_tweets)}] @{tweet.author_username}: ⚠ All angles failed to generate valid scripts. Keeping status as 'relevant'.")

                except Exception as e:
                    logger.error(f"[Pipeline]    → [{i+1}/{len(relevant_tweets)}] @{tweet.author_username}: ✗ Script generation failed: {e}")

                # Jeda natural antar tweet agar tidak kena rate limit
                await asyncio.sleep(5)

            # Complete job
            logger.info(f"[Pipeline] 🎉 DONE — {scripts_generated} scripts generated from {tweets_fetched} tweets fetched")
            await db.execute(
                update(PipelineJob)
                .where(PipelineJob.id == job_id)
                .values(
                    status="completed",
                    step="done",
                    scripts_generated=scripts_generated,
                    completed_at=datetime.utcnow(),
                )
            )
            await db.commit()

    run_async(_run())


@celery_app.task(bind=True, name="tasks.generate_scripts_for_tweet")
def generate_scripts_for_tweet(self, tweet_id: str):
    """Generate scripts for a single tweet (on-demand)."""
    async def _run():
        async with make_session()() as db:
            result = await db.execute(select(Tweet).where(Tweet.id == tweet_id))
            tweet = result.scalar_one_or_none()
            if not tweet:
                return {"error": "Tweet not found"}

            niche_result = await db.execute(
                select(NicheConfig).where(NicheConfig.is_active == True).limit(1)
            )
            niche = niche_result.scalar_one_or_none()

            content = tweet.article_content or tweet.content or ""
            if not content.strip():
                return {"error": "No content to generate script from"}

            scripts_data = generate_scripts_for_content(
                article_content=content,
                niche_name=niche.name if niche else "General",
                niche_keywords=niche.keywords if niche else [],
                custom_rules=niche.script_rules if niche else None,
                angles=["hero", "tips_trick", "controversial"],
                duration_seconds=niche.target_duration_seconds if niche else 60,
            )

            created = []
            for sd in scripts_data:
                script = Script(
                    tweet_id=tweet.id,
                    angle=sd.get("angle"),
                    hook=sd.get("hook", ""),
                    body=sd.get("body", ""),
                    cta=sd.get("cta", ""),
                    full_script=sd.get("full_script", ""),
                    hook_formula_used=sd.get("hook_formula_used"),
                    duration_estimate=sd.get("estimated_duration_seconds"),
                    naturalness_score=sd.get("naturalness_score"),
                    claude_model=sd.get("claude_model"),
                    status="draft",
                )
                db.add(script)
                created.append(sd.get("angle"))

            tweet.status = "scripted"
            await db.commit()
            return {"scripts_created": created}

    return run_async(_run())
