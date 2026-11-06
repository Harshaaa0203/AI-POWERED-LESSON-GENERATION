"""
Tests for Lesson Generator Agent and 45-minute constraint enforcement.
"""

import pytest
from agents.lesson_generator import LessonGenerator
from services.ai_service import AIService
from utils.validators import validate_lesson_structure, validate_lesson_inputs, MANDATORY_LESSON_SECTIONS
from utils.error_handler import ValidationError


def test_validate_lesson_inputs():
    """Test input field validation."""
    # Valid
    ok, err = validate_lesson_inputs("Valid Title", "This is a valid educational objective.")
    assert ok is True
    assert err == ""

    # Empty title
    ok, err = validate_lesson_inputs("", "Valid objective here")
    assert ok is False
    assert "Title cannot be empty" in err

    # Empty objective
    ok, err = validate_lesson_inputs("Valid Title", "")
    assert ok is False
    assert "Objective cannot be empty" in err

    # Too short objective
    ok, err = validate_lesson_inputs("Valid Title", "Short")
    assert ok is False


def test_lesson_generator_produces_all_14_sections():
    """Verify that every generated lesson contains all 14 mandatory sections."""
    ai = AIService()
    generator = LessonGenerator(ai_service=ai)

    dummy_research = {
        "web_sources": [{"title": "MDN HTTP", "url": "https://developer.mozilla.org"}],
        "book_sources": [{"title": "HTTP Guide", "authors": ["Author"], "publication_year": "2002"}],
        "youtube_resources": [{"title": "HTTP Video", "channel": "Traversy Media", "url": "https://youtube.com"}],
        "key_factual_claims": []
    }

    lesson = generator.generate(
        title="HTTP Requests and Responses",
        learning_objective="Explain GET and POST methods and distinguish between 2xx, 4xx, and 5xx status codes.",
        research_data=dummy_research
    )

    # Check all 14 mandatory sections
    for sec in MANDATORY_LESSON_SECTIONS:
        assert sec in lesson, f"Mandatory section '{sec}' missing from generated lesson."
        assert lesson[sec], f"Section '{sec}' must not be empty."

    # Verify duration does not exceed 45 minutes
    assert lesson["estimated_total_minutes"] <= 45
    assert lesson["target_duration_minutes"] == 45

    # Run structure validator
    is_valid, issues = validate_lesson_structure(lesson)
    assert is_valid is True, f"Lesson structure validation failed: {issues}"
