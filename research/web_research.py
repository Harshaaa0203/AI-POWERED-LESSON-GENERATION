"""
Web research module: searches trusted educational websites and official documentation.
"""

import logging
import requests
from typing import List, Dict, Any, Optional
from research.source_validator import SourceValidator
from utils.error_handler import retry_with_backoff

logger = logging.getLogger("AILessonCreator.WebResearch")


class WebResearch:
    """Performs web research across educational and official documentation sites."""

    def __init__(self):
        self.validator = SourceValidator()

    def search(self, query: str, max_results: int = 6) -> List[Dict[str, Any]]:
        """
        Execute web search for the query, validating and categorizing results.
        Prefers official docs, RFCs, educational portals, and academic resources.
        """
        sources: List[Dict[str, Any]] = []

        # 1. Primary: DuckDuckGo Search
        try:
            from duckduckgo_search import DDGS
            ddg = DDGS()
            # Craft educational search queries
            queries = [
                f"{query} educational tutorial documentation",
                f"{query} official guide site:edu OR site:org OR site:mozilla.org"
            ]

            raw_results = []
            for q in queries:
                try:
                    res = list(ddg.text(q, max_results=max_results))
                    if res:
                        raw_results.extend(res)
                except Exception as ex:
                    logger.warning(f"DDGS sub-query '{q}' failed: {ex}")

            for item in raw_results:
                href = item.get("href") or item.get("link")
                title = item.get("title", "")
                snippet = item.get("body") or item.get("snippet", "")

                if href and title:
                    cred_info = self.validator.assess_domain_credibility(href)
                    sources.append({
                        "title": title.strip(),
                        "url": href.strip(),
                        "snippet": snippet.strip(),
                        "category": cred_info["category"],
                        "credibility": cred_info["credibility"],
                        "domain": cred_info["domain"],
                        "source_type": "website",
                        "is_verified": True
                    })

        except Exception as e:
            logger.warning(f"DuckDuckGo search error: {e}")

        # 2. Secondary fallback: Wikipedia API for grounded encyclopedia definitions
        if len(sources) < 3:
            wiki_sources = self._search_wikipedia(query)
            sources.extend(wiki_sources)

        # Deduplicate
        deduped = self.validator.deduplicate_sources(sources, key="url")
        return deduped[:max_results]

    def _search_wikipedia(self, query: str) -> List[Dict[str, Any]]:
        """Query Wikipedia API as a verified factual anchor."""
        results = []
        try:
            api_url = "https://en.wikipedia.org/w/api.php"
            params = {
                "action": "query",
                "list": "search",
                "srsearch": query,
                "format": "json",
                "utf8": 1,
                "srlimit": 3
            }
            headers = {"User-Agent": "AILessonCreator/1.0 (Educational research agent)"}
            resp = requests.get(api_url, params=params, headers=headers, timeout=6)
            if resp.status_code == 200:
                data = resp.json()
                search_items = data.get("query", {}).get("search", [])
                for item in search_items:
                    page_id = item.get("pageid")
                    title = item.get("title")
                    snippet = item.get("snippet", "").replace('<span class="searchmatch">', "").replace("</span>", "")
                    url = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
                    results.append({
                        "title": f"{title} - Wikipedia",
                        "url": url,
                        "snippet": snippet,
                        "category": "Wikipedia Encyclopedia",
                        "credibility": "High",
                        "domain": "en.wikipedia.org",
                        "source_type": "website",
                        "is_verified": True
                    })
        except Exception as e:
            logger.warning(f"Wikipedia API search failed: {e}")
        return results
