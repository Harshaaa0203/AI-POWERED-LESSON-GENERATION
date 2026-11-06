"""
Unit and integration tests for research modules (Web, Books, YouTube, and Source Validator).
"""

import pytest
from research.source_validator import SourceValidator
from research.web_research import WebResearch
from research.book_research import BookResearch
from research.youtube_research import YouTubeResearch
from agents.research_agent import ResearchAgent


def test_source_validator_credibility():
    """Test domain categorization and credibility ranking."""
    validator = SourceValidator()

    # Academic
    cred_mit = validator.assess_domain_credibility("https://ocw.mit.edu/courses/electrical-engineering")
    assert cred_mit["credibility"] == "High"
    assert "Academic" in cred_mit["category"]

    # Official Standards
    cred_ietf = validator.assess_domain_credibility("https://datatracker.ietf.org/doc/html/rfc7231")
    assert cred_ietf["credibility"] == "High"

    # MDN
    cred_mdn = validator.assess_domain_credibility("https://developer.mozilla.org/en-US/docs/Web/HTTP")
    assert cred_mdn["credibility"] == "High"


def test_source_validator_deduplication():
    """Test URL deduplication."""
    validator = SourceValidator()
    sources = [
        {"title": "Doc 1", "url": "https://developer.mozilla.org/HTTP"},
        {"title": "Doc 1 Duplicate", "url": "https://developer.mozilla.org/HTTP/"},
        {"title": "Doc 2", "url": "https://ietf.org/rfc7231"}
    ]
    deduped = validator.deduplicate_sources(sources)
    assert len(deduped) == 2


def test_book_research_open_library():
    """Test querying verified book bibliographic data."""
    book_research = BookResearch()
    books = book_research.search("HTTP The Definitive Guide", max_results=2)
    assert isinstance(books, list)
    assert len(books) > 0
    first_book = books[0]
    assert "title" in first_book
    assert "authors" in first_book
    assert "source_type" in first_book
    assert first_book["source_type"] == "book"


def test_youtube_research_discovery():
    """Test discovery of educational YouTube videos."""
    yt_research = YouTubeResearch()
    videos = yt_research.search("HTTP Requests and Responses GET POST", max_results=3)
    assert isinstance(videos, list)
    assert len(videos) > 0
    first_video = videos[0]
    assert "title" in first_video
    assert "url" in first_video
    assert "youtube.com" in first_video["url"]
    assert "channel" in first_video


def test_research_agent_end_to_end():
    """Test ResearchAgent synthesizing web, book, and video research."""
    agent = ResearchAgent()
    results = agent.conduct_research(
        title="HTTP Requests and Responses",
        learning_objective="Explain GET and POST methods and distinguish between 2xx, 4xx, and 5xx status codes."
    )
    assert results["total_sources_count"] > 0
    assert len(results["web_sources"]) > 0 or len(results["youtube_resources"]) > 0
    assert "research_summary" in results
    assert "key_factual_claims" in results
