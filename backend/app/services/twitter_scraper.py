"""
Twitter/X Scraper using Playwright.
"""
import asyncio
import json
import re
from typing import Optional
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
import logging
import os

logger = logging.getLogger(__name__)
from app.config import settings

try:
    from playwright_stealth import stealth_async
except ImportError:
    stealth_async = None

STATE_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "twitter_state.json")

class TwitterScraper:
    def __init__(self):
        self.username = settings.TWITTER_USERNAME
        self.password = settings.TWITTER_PASSWORD
        self.auth_token = settings.TWITTER_AUTH_TOKEN
        self.ct0 = settings.TWITTER_CT0
    def _extract_tweet_data(self, tweet_element_text: str, tweet_url: str) -> dict:
        """Extract structured data from tweet text."""
        # Find URLs in tweet text
        urls = re.findall(r'https?://[^\s]+', tweet_element_text)
        article_urls = [u for u in urls if not u.startswith("https://x.com") and not u.startswith("https://twitter.com")]

        return {
            "content": tweet_element_text[:2000],
            "url": tweet_url,
            "has_article_link": len(article_urls) > 0,
            "article_url": article_urls[0] if article_urls else None,
        }

    async def scrape_bookmarks(self, limit: int = 30) -> list[dict]:
        """Scrape Twitter bookmarks using injected cookies."""
        tweets = []

        if not self.auth_token or not self.ct0:
            logger.error("[Scraper] TWITTER_AUTH_TOKEN or TWITTER_CT0 is missing in .env!")
            raise Exception("No Twitter cookies found in .env. Please provide auth_token and ct0.")

        # Set headless to False as requested to avoid detection
        IS_HEADLESS = False

        async with async_playwright() as p:
            logger.info("[Scraper] Launching browser with injected cookies...")
            browser = await p.chromium.launch(
                headless=IS_HEADLESS,
                args=["--disable-blink-features=AutomationControlled"]
            )
            import random
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800},
                locale="en-US",
                timezone_id="Asia/Jakarta"
            )

            # Inject the authentication cookies
            await context.add_cookies([
                {
                    "name": "auth_token",
                    "value": self.auth_token,
                    "domain": ".x.com",
                    "path": "/",
                    "secure": True,
                    "httpOnly": True
                },
                {
                    "name": "ct0",
                    "value": self.ct0,
                    "domain": ".x.com",
                    "path": "/",
                    "secure": True,
                    "httpOnly": False
                }
            ])
            page = await context.new_page()
            if stealth_async:
                await stealth_async(page)
            else:
                logger.warning("[Scraper] playwright_stealth not available, skipping stealth mode.")

            try:
                logger.info("[Scraper] Navigating to bookmarks directly...")
                await page.goto("https://x.com/i/bookmarks", wait_until="domcontentloaded")
                await asyncio.sleep(4)

                # Check if we were redirected to login (meaning session expired)
                if "login" in page.url:
                    logger.error("[Scraper] Redirected to login. Session has expired or is invalid.")
                    raise Exception("Twitter session expired. Please run 'python scripts/login_twitter.py' again.")

                seen_ids = set()
                scroll_attempts = 0
                max_scrolls = 20

                while len(tweets) < limit and scroll_attempts < max_scrolls:
                    tweet_elements = await page.query_selector_all('[data-testid="tweet"]')

                    for elem in tweet_elements:
                        try:
                            # Get tweet text
                            text_elem = await elem.query_selector('[data-testid="tweetText"]')
                            if not text_elem:
                                continue
                            text = await text_elem.inner_text()

                            # Get tweet URL / ID
                            time_elem = await elem.query_selector("time")
                            tweet_url = ""
                            tweet_id = ""
                            if time_elem:
                                parent = await time_elem.evaluate_handle("el => el.closest('a')")
                                href = await parent.evaluate("el => el ? el.href : ''")
                                tweet_url = href
                                id_match = re.search(r'/status/(\d+)', href)
                                tweet_id = id_match.group(1) if id_match else ""

                            if not tweet_id or tweet_id in seen_ids:
                                continue

                            # Get author username
                            user_elem = await elem.query_selector('[data-testid="User-Name"]')
                            author = ""
                            if user_elem:
                                author_text = await user_elem.inner_text()
                                lines = author_text.strip().split("\n")
                                author = lines[-1].strip("@") if lines else ""

                            seen_ids.add(tweet_id)
                            tweet_data = self._extract_tweet_data(text, tweet_url)
                            tweet_data["tweet_id"] = tweet_id
                            tweet_data["author_username"] = author
                            tweets.append(tweet_data)

                            if len(tweets) >= limit:
                                break

                        except Exception:
                            continue

                    # Scroll down
                    scroll_amount = random.randint(800, 1500)
                    await page.evaluate(f"window.scrollBy(0, {scroll_amount})")
                    
                    # Human-like random delay between 2 to 5 seconds
                    await asyncio.sleep(random.uniform(2.0, 5.0))
                    scroll_attempts += 1

            except PlaywrightTimeout as e:
                print(f"[Scraper] Timeout error: {e}")
            except Exception as e:
                print(f"[Scraper] Error: {e}")
            finally:
                await browser.close()

        return tweets

    async def scrape_home_timeline(self, limit: int = 20) -> list[dict]:
        """Scrape home timeline (FYP)."""
        tweets = []

        # --- DEBUG MODE ---
        # Jika gagal login/timeout, ubah IS_HEADLESS = False
        # untuk bisa melihat browser dan menyelesaikan CAPTCHA manual.
        # Jika sudah berhasil dan normal, kembalikan ke True.
        IS_HEADLESS = False

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=IS_HEADLESS)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await context.new_page()

            try:
                await self._login(page)
                await asyncio.sleep(3)

                seen_ids = set()
                scroll_attempts = 0

                while len(tweets) < limit and scroll_attempts < 15:
                    tweet_elements = await page.query_selector_all('[data-testid="tweet"]')

                    for elem in tweet_elements:
                        try:
                            text_elem = await elem.query_selector('[data-testid="tweetText"]')
                            if not text_elem:
                                continue
                            text = await text_elem.inner_text()

                            time_elem = await elem.query_selector("time")
                            tweet_url = ""
                            tweet_id = ""
                            if time_elem:
                                parent = await time_elem.evaluate_handle("el => el.closest('a')")
                                href = await parent.evaluate("el => el ? el.href : ''")
                                tweet_url = href
                                id_match = re.search(r'/status/(\d+)', href)
                                tweet_id = id_match.group(1) if id_match else ""

                            if not tweet_id or tweet_id in seen_ids:
                                continue

                            user_elem = await elem.query_selector('[data-testid="User-Name"]')
                            author = ""
                            if user_elem:
                                author_text = await user_elem.inner_text()
                                lines = author_text.strip().split("\n")
                                author = lines[-1].strip("@") if lines else ""

                            seen_ids.add(tweet_id)
                            tweet_data = self._extract_tweet_data(text, tweet_url)
                            tweet_data["tweet_id"] = tweet_id
                            tweet_data["author_username"] = author
                            tweets.append(tweet_data)

                            if len(tweets) >= limit:
                                break

                        except Exception:
                            continue

                    await page.evaluate("window.scrollBy(0, 1200)")
                    await asyncio.sleep(2)
                    scroll_attempts += 1

            except Exception as e:
                print(f"[Scraper] Timeline error: {e}")
            finally:
                await browser.close()

        return tweets
