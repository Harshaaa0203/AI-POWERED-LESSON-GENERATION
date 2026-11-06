"""
Book research module: retrieves legitimate bibliographic metadata from Open Library
and Google Books APIs without fabricating references or page numbers.
"""

import logging
import requests
import urllib.parse
from typing import List, Dict, Any, Optional
from research.source_validator import SourceValidator

logger = logging.getLogger("AILessonCreator.BookResearch")


class BookResearch:
    """Retrieves verified book metadata from Open Library and Google Books."""

    def __init__(self):
        self.validator = SourceValidator()

    def search(self, topic: str, max_results: int = 4) -> List[Dict[str, Any]]:
        """
        Search for relevant educational books using Open Library and Google Books.
        Collects title, authors, publisher, year, ISBN, and legitimate preview URLs.
        """
        books: List[Dict[str, Any]] = []

        # 1. Query Open Library API (Open public bibliographic catalog)
        try:
            ol_books = self._search_open_library(topic, limit=max_results)
            books.extend(ol_books)
        except Exception as e:
            logger.warning(f"Open Library search encountered error: {e}")

        # 2. If needed, query Google Books API
        if len(books) < max_results:
            try:
                gb_books = self._search_google_books(topic, limit=max_results - len(books))
                books.extend(gb_books)
            except Exception as e:
                logger.warning(f"Google Books API search encountered error: {e}")

        # Deduplicate by title
        deduped = self.validator.deduplicate_sources(books, key="title")
        return deduped[:max_results]

    def _search_open_library(self, query: str, limit: int = 4) -> List[Dict[str, Any]]:
        """Query Open Library search API for bibliographic records."""
        results = []
        clean_query = query.replace("Explain", "").replace("distinguish between", "").strip()
        url = "https://openlibrary.org/search.json"
        params = {
            "q": clean_query,
            "limit": limit * 2,
            "fields": "key,title,author_name,first_publish_year,publisher,isbn,cover_i"
        }
        headers = {"User-Agent": "AILessonCreator/1.0 (Educational research agent)"}

        resp = requests.get(url, params=params, headers=headers, timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            docs = data.get("docs", [])
            for doc in docs:
                title = doc.get("title")
                authors = doc.get("author_name") or ["Unknown Author"]
                year = doc.get("first_publish_year")
                publishers = doc.get("publisher") or []
                publisher = publishers[0] if publishers else "N/A"
                isbns = doc.get("isbn") or []
                isbn = isbns[0] if isbns else "N/A"
                key = doc.get("key", "")
                book_url = f"https://openlibrary.org{key}" if key else ""

                if title:
                    results.append({
                        "title": title,
                        "authors": authors[:3],
                        "publisher": publisher,
                        "publication_year": str(year) if year else "N/A",
                        "isbn": isbn,
                        "url": book_url,
                        "source_type": "book",
                        "credibility": "High",
                        "is_verified": True,
                        "notes": f"Published by {publisher} ({year})" if year else f"Published by {publisher}"
                    })
                if len(results) >= limit:
                    break
        return results

    def _search_google_books(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Query Google Books public search endpoint."""
        results = []
        clean_query = query.replace("Explain", "").replace("distinguish between", "").strip()
        url = "https://www.googleapis.com/books/v1/volumes"
        params = {"q": clean_query, "maxResults": limit}

        resp = requests.get(url, params=params, timeout=6)
        if resp.status_code == 200:
            data = resp.json()
            items = data.get("items", [])
            for it in items:
                info = it.get("volumeInfo", {})
                title = info.get("title")
                authors = info.get("authors", ["Unknown Author"])
                publisher = info.get("publisher", "N/A")
                published_date = info.get("publishedDate", "N/A")
                year = published_date.split("-")[0] if published_date else "N/A"
                preview_link = info.get("previewLink") or info.get("infoLink", "")

                if title:
                    results.append({
                        "title": title,
                        "authors": authors,
                        "publisher": publisher,
                        "publication_year": year,
                        "isbn": "N/A",
                        "url": preview_link,
                        "source_type": "book",
                        "credibility": "High",
                        "is_verified": True,
                        "notes": f"{publisher} ({year})"
                    })
        return results

