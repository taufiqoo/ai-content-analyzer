"""
Article Extractor — menggunakan trafilatura untuk extract full article content dari URL.
"""
import httpx
import trafilatura
from typing import Optional


async def extract_article(url: str) -> Optional[str]:
    """
    Fetch and extract article text from a URL.
    Returns extracted text or None if failed.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            html = response.text

        # Resolve t.co short URLs via response URL
        text = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=False,
            no_fallback=False,
            favor_recall=True,
        )

        if text and len(text) > 200:
            return text[:8000]  # Cap at 8k chars

        return None

    except Exception as e:
        print(f"[ArticleExtractor] Failed to extract {url}: {e}")
        return None
