"""
YouTube research module: discovers relevant, high-quality educational videos
using either the YouTube Data API v3 or intelligent web discovery fallback.
"""

import os
import re
import json
import logging
import requests
import urllib.parse
from typing import List, Dict, Any, Optional
from research.source_validator import SourceValidator

logger = logging.getLogger("AILessonCreator.YouTubeResearch")

# Channels recognized for excellent computer science and educational pedagogy
TOP_EDUCATIONAL_CHANNELS = [
    "Gate Smashers", "Traversy Media", "freeCodeCamp.org", "CS50",
    "Computerphile", "NetworkChuck", "Hussein Nasser", "Fireship",
    "MIT OpenCourseWare", "CrashCourse", "Khan Academy", "3Blue1Brown",
    "ByteByteGo", "Bro Code", "Programming with Mosh", "Tech With Tim"
]


class YouTubeResearch:
    """Discovers verified educational videos relevant to the lesson."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("YOUTUBE_API_KEY")
        self.validator = SourceValidator()

    def search(self, query: str, max_results: int = 4) -> List[Dict[str, Any]]:
        """
        Search for educational YouTube videos.
        Uses YouTube Data API v3 if API key is configured; otherwise uses
        intelligent web extraction.
        """
        videos: List[Dict[str, Any]] = []

        if self.api_key and self.api_key.strip():
            try:
                videos = self._search_via_api(query, max_results)
                if videos:
                    logger.info(f"Retrieved {len(videos)} videos via YouTube Data API v3.")
                    return videos
            except Exception as e:
                logger.warning(f"YouTube Data API failed: {e}. Falling back to web extraction.")

        # Fallback to direct web parser
        try:
            videos = self._search_via_web(query, max_results)
        except Exception as e:
            logger.warning(f"YouTube web search failed: {e}")

        # Deduplicate
        return self.validator.deduplicate_sources(videos, key="url")[:max_results]

    def _search_via_api(self, query: str, max_results: int = 4) -> List[Dict[str, Any]]:
        """Query official YouTube Data API v3."""
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "key": self.api_key,
            "q": f"{query} tutorial explanation",
            "part": "snippet",
            "type": "video",
            "videoEmbeddable": "true",
            "maxResults": max_results,
            "relevanceLanguage": "en"
        }
        resp = requests.get(url, params=params, timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            items = data.get("items", [])
            results = []
            for item in items:
                vid = item.get("id", {}).get("videoId")
                snippet = item.get("snippet", {})
                if vid:
                    results.append({
                        "title": snippet.get("title", ""),
                        "channel": snippet.get("channelTitle", "Unknown Channel"),
                        "url": f"https://www.youtube.com/watch?v={vid}",
                        "video_id": vid,
                        "description": snippet.get("description", ""),
                        "published_at": snippet.get("publishedAt", ""),
                        "source_type": "youtube",
                        "credibility": "High" if any(c.lower() in snippet.get("channelTitle", "").lower() for c in TOP_EDUCATIONAL_CHANNELS) else "Medium",
                        "is_verified": True
                    })
            return results
        else:
            raise Exception(f"YouTube API returned status {resp.status_code}: {resp.text}")

    def _search_via_web(self, query: str, max_results: int = 4) -> List[Dict[str, Any]]:
        """Directly parse YouTube search results page for authentic video metadata."""
        results = []
        search_term = urllib.parse.quote_plus(f"{query} educational tutorial")
        url = f"https://www.youtube.com/results?search_query={search_term}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        }

        resp = requests.get(url, headers=headers, timeout=8)
        if resp.status_code == 200:
            match = re.search(r"ytInitialData\s*=\s*({.+?});</script>", resp.text)
            if match:
                try:
                    data = json.loads(match.group(1))
                    sections = (
                        data.get("contents", {})
                        .get("twoColumnSearchResultsRenderer", {})
                        .get("primaryContents", {})
                        .get("sectionListRenderer", {})
                        .get("contents", [])
                    )

                    for sec in sections:
                        items = sec.get("itemSectionRenderer", {}).get("contents", [])
                        for item in items:
                            v = item.get("videoRenderer")
                            if v and "videoId" in v:
                                vid = v.get("videoId")
                                title = v.get("title", {}).get("runs", [{}])[0].get("text", "")
                                channel = v.get("ownerText", {}).get("runs", [{}])[0].get("text", "Educational Channel")
                                desc_snippets = v.get("detailedMetadataSnippets", [{}])
                                desc = ""
                                if desc_snippets:
                                    desc = desc_snippets[0].get("snippetText", {}).get("runs", [{}])[0].get("text", "")

                                # Prioritize educational credibility
                                is_top = any(c.lower() in channel.lower() for c in TOP_EDUCATIONAL_CHANNELS)

                                if vid and title and len(title) > 3:
                                    results.append({
                                        "title": title,
                                        "channel": channel,
                                        "url": f"https://www.youtube.com/watch?v={vid}",
                                        "video_id": vid,
                                        "description": desc or f"Educational video on {query} by {channel}",
                                        "source_type": "youtube",
                                        "credibility": "High" if is_top else "Medium",
                                        "is_verified": True
                                    })
                                if len(results) >= max_results * 2:
                                    break
                except Exception as e:
                    logger.warning(f"Error parsing YouTube initial data: {e}")

        # Sort top educational channels first
        results.sort(key=lambda x: 0 if x.get("credibility") == "High" else 1)
        return results[:max_results]
