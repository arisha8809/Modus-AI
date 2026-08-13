"""
Web search tool used by the Search agent.

Uses Tavily (https://tavily.com) -- a search API purpose-built for AI agents,
with a genuinely free tier (1,000 searches/month, no credit card). This is
deliberately not a scraping-based approach (e.g. hitting Bing/DuckDuckGo
directly): scraping is fragile against rate-limiting and layout changes,
which is exactly the kind of failure that can't happen during a live demo.
Tavily also returns already-extracted page content in the same response, so
there's no separate "fetch and parse HTML" step to fail either.
"""

import os
from tavily import TavilyClient

_client = None


def _get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("TAVILY_API_KEY")
        if not api_key:
            raise RuntimeError(
                "TAVILY_API_KEY is not set. Get a free key at https://tavily.com "
                "and put it in your .env file (see .env.example)."
            )
        _client = TavilyClient(api_key=api_key)
    return _client


def search_web(query: str, max_results: int = 5) -> list[dict]:
    """Returns a list of {title, url, content} dicts. `content` is Tavily's
    already-extracted main page text, ready for the Extraction agent -- no
    separate page-fetch step needed."""
    client = _get_client()
    response = client.search(
        query=query,
        max_results=max_results,
        include_raw_content=False,  # Tavily's cleaned "content" field is enough
    )
    results = []
    for r in response.get("results", []):
        results.append({
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "content": (r.get("content") or "")[:6000],
        })
    return results
