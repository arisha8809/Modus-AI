"""
Free web search + page fetching tools used by the Search and Extraction agents.

- Search: `ddgs` (DuckDuckGo Search) -- free, no API key, no rate-limit signup.
- Fetch: `trafilatura` -- free, open-source, extracts clean main-content text
  from a raw HTML page (strips nav/ads/boilerplate) so the LLM extraction step
  gets readable article text instead of a wall of HTML.
"""

import trafilatura
from ddgs import DDGS


def search_web(query: str, max_results: int = 5) -> list[dict]:
    """Returns a list of {title, url, snippet} dicts."""
    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results):
            results.append({
                "title": r.get("title", ""),
                "url": r.get("href", ""),
                "snippet": r.get("body", ""),
            })
    return results


def fetch_page_text(url: str, max_chars: int = 6000) -> str | None:
    """Downloads a URL and extracts clean readable text. Returns None if the
    page can't be fetched or has no extractable content (dead link, paywall,
    non-HTML file, etc.) -- callers should skip such sources gracefully."""
    try:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return None
        text = trafilatura.extract(downloaded)
        if not text:
            return None
        return text[:max_chars]
    except Exception:
        return None
