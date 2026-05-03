from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models import Script, ScriptPerformance, Tweet, NicheConfig, PipelineJob
from app.schemas import ScriptOut, ScriptUpdate, ScriptPerformanceCreate, ScriptPerformanceOut, ManualArticleIn
from app.services.script_generator import generate_scripts_for_content
from datetime import datetime
import uuid
from typing import Optional

router = APIRouter(prefix="/api/scripts", tags=["scripts"])


@router.get("", response_model=list[ScriptOut])
async def list_scripts(
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Script)
        .options(selectinload(Script.tweet), selectinload(Script.performance))
        .order_by(Script.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if status:
        query = query.where(Script.status == status)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{script_id}", response_model=ScriptOut)
async def get_script(script_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Script)
        .options(selectinload(Script.tweet), selectinload(Script.performance))
        .where(Script.id == script_id)
    )
    script = result.scalar_one_or_none()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    return script


@router.patch("/{script_id}", response_model=ScriptOut)
async def update_script(
    script_id: uuid.UUID,
    body: ScriptUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Script)
        .options(selectinload(Script.tweet), selectinload(Script.performance))
        .where(Script.id == script_id)
    )
    script = result.scalar_one_or_none()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")

    updates = body.model_dump(exclude_none=True)

    # Auto-rebuild full_script if hook/body/cta changed
    if any(k in updates for k in ["hook", "body", "cta"]):
        hook = updates.get("hook", script.hook)
        body_text = updates.get("body", script.body)
        cta = updates.get("cta", script.cta)
        updates["full_script"] = f"{hook}\n\n{body_text}\n\n{cta}"

    if updates.get("status") == "approved" and not script.approved_at:
        updates["approved_at"] = datetime.utcnow()

    for field, value in updates.items():
        setattr(script, field, value)

    await db.commit()
    await db.refresh(script)
    return script


@router.delete("/{script_id}")
async def delete_script(script_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Script).where(Script.id == script_id))
    script = result.scalar_one_or_none()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    await db.delete(script)
    await db.commit()
    return {"ok": True}


@router.post("/generate/manual", response_model=list[ScriptOut])
async def generate_from_manual_article(
    body: ManualArticleIn,
    db: AsyncSession = Depends(get_db),
):
    """Generate scripts from manually pasted article content."""
    # Get niche config
    if body.niche_config_id:
        niche_result = await db.execute(
            select(NicheConfig).where(NicheConfig.id == body.niche_config_id)
        )
        niche = niche_result.scalar_one_or_none()
    else:
        niche_result = await db.execute(
            select(NicheConfig).where(NicheConfig.is_active == True).limit(1)
        )
        niche = niche_result.scalar_one_or_none()

    # Create a synthetic tweet for the manual article
    synthetic_tweet = Tweet(
        tweet_id=f"manual_{uuid.uuid4().hex[:12]}",
        author_username="manual_input",
        content=body.content[:500],
        has_article_link=False,
        article_content=body.content,
        status="relevant",
        niche_config_id=niche.id if niche else None,
    )
    db.add(synthetic_tweet)
    await db.commit()
    await db.refresh(synthetic_tweet)

    # Generate scripts
    scripts_data = generate_scripts_for_content(
        article_content=body.content,
        niche_name=niche.name if niche else "General",
        niche_keywords=niche.keywords if niche else [],
        custom_rules=niche.script_rules if niche else None,
        angles=["hero", "tips_trick", "controversial", "storytelling"],
        duration_seconds=niche.target_duration_seconds if niche else 60,
    )

    created_scripts = []
    for sd in scripts_data:
        script = Script(
            tweet_id=synthetic_tweet.id,
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
        created_scripts.append(script)

    synthetic_tweet.status = "scripted"
    await db.commit()

    # Refresh with relationships
    result = await db.execute(
        select(Script)
        .options(selectinload(Script.tweet), selectinload(Script.performance))
        .where(Script.tweet_id == synthetic_tweet.id)
        .order_by(Script.created_at.desc())
    )
    return result.scalars().all()


@router.post("/{script_id}/performance", response_model=ScriptPerformanceOut)
async def log_performance(
    script_id: uuid.UUID,
    body: ScriptPerformanceCreate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Script).where(Script.id == script_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Script not found")

    # Check if performance already exists
    perf_result = await db.execute(
        select(ScriptPerformance).where(ScriptPerformance.script_id == script_id)
    )
    existing = perf_result.scalar_one_or_none()

    if existing:
        for field, value in body.model_dump().items():
            setattr(existing, field, value)
        existing.recorded_at = datetime.utcnow()
        await db.commit()
        await db.refresh(existing)
        return existing
    else:
        perf = ScriptPerformance(script_id=script_id, **body.model_dump())
        db.add(perf)
        await db.commit()
        await db.refresh(perf)
        return perf
