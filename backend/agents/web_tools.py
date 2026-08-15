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
    """Returns normalized source records with content and publication metadata.

    Tavily may expose ``published_date`` for news and dated pages. It is kept
    as optional metadata so downstream analytics never invent a timeline when
    a publisher did not provide one.
    """
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
            "published_date": r.get("published_date"),
        })
    return results
