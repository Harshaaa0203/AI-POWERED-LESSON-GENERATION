"""
Source validator: validates URLs, assesses credibility, de-duplicates,
and categorizes web, book, and video resources.
"""

import re
import urllib.parse
from typing import Dict, Any, List, Optional
import requests
from utils.validators import validate_url

TRUSTED_DOMAINS = {
    # Official Standards & Docs
    "w3.org": ("Official Standards", "High"),
    "ietf.org": ("Official RFC Standards", "High"),
    "developer.mozilla.org": ("MDN Web Docs", "High"),
    "python.org": ("Official Python Documentation", "High"),
    "learn.microsoft.com": ("Microsoft Official Documentation", "High"),
    "oracle.com": ("Oracle Official Documentation", "High"),
    "apache.org": ("Apache Software Foundation", "High"),
    "rfc-editor.org": ("RFC Editor", "High"),
    "kubernetes.io": ("Kubernetes Docs", "High"),
    "docker.com": ("Docker Official Docs", "High"),

    # Academic & Research
    "stanford.edu": ("Stanford University", "High"),
    "mit.edu": ("MIT OpenCourseWare", "High"),
    "harvard.edu": ("Harvard University", "High"),
    "berkeley.edu": ("UC Berkeley", "High"),
    "cmu.edu": ("Carnegie Mellon University", "High"),
    "arxiv.org": ("Cornell arXiv Repository", "High"),

    # Trusted Educational Publications & Platforms
    "geeksforgeeks.org": ("GeeksforGeeks", "Medium"),
    "freecodecamp.org": ("freeCodeCamp", "Medium"),
    "khanacademy.org": ("Khan Academy", "High"),
    "coursera.org": ("Coursera", "Medium"),
    "edx.org": ("edX", "Medium"),
    "baeldung.com": ("Baeldung Computer Science", "Medium"),
    "digitalocean.com": ("DigitalOcean Community Tutorials", "Medium"),
    "wikipedia.org": ("Wikipedia Encyclopedia", "Medium"),
    "openlibrary.org": ("Open Library", "High"),
    "books.google.com": ("Google Books", "High"),
    "youtube.com": ("YouTube Video", "Medium"),
    "youtu.be": ("YouTube Video", "Medium"),
}


class SourceValidator:
    """Validates and enriches research sources."""

    @staticmethod
    def assess_domain_credibility(url: str) -> Dict[str, str]:
        """
        Assess credibility of domain based on recognized academic/official sources.
        Returns dict with category and credibility level.
        """
        try:
            parsed = urllib.parse.urlparse(url)
            netloc = parsed.netloc.lower()
            if netloc.startswith("www."):
                netloc = netloc[4:]

            # Check TLD (.edu, .gov, .org)
            if netloc.endswith(".edu") or netloc.endswith(".ac.uk"):
                return {"category": "Academic / University", "credibility": "High", "domain": netloc}
            if netloc.endswith(".gov"):
                return {"category": "Government / Official", "credibility": "High", "domain": netloc}

            # Check known trusted domains
            for domain_key, (cat, cred) in TRUSTED_DOMAINS.items():
                if domain_key in netloc:
                    return {"category": cat, "credibility": cred, "domain": netloc}

            return {"category": "General Web Resource", "credibility": "Medium", "domain": netloc}
        except Exception:
            return {"category": "Unverified", "credibility": "Low", "domain": "unknown"}

    @staticmethod
    def verify_and_clean_url(url: str, check_live: bool = False) -> Optional[str]:
        """Check URL syntax and optionally probe availability."""
        if not url or not isinstance(url, str):
            return None
        url = url.strip()
        if not (url.startswith("http://") or url.startswith("https://")):
            return None
        if not validate_url(url, check_reachable=check_live):
            return None
        return url

    @staticmethod
    def deduplicate_sources(sources: List[Dict[str, Any]], key: str = "url") -> List[Dict[str, Any]]:
        """
        Deduplicate a list of source dictionaries based on normalized URL or Title.
        """
        seen = set()
        unique = []
        for s in sources:
            val = s.get(key)
            if not val:
                val = s.get("title", "")
            norm = str(val).lower().strip().rstrip("/")
            if norm and norm not in seen:
                seen.add(norm)
                unique.append(s)
        return unique
