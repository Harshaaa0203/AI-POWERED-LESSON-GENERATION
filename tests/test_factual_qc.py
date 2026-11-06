"""
Tests for QC Agent 1: Research and Factual Accuracy Auditor.
"""

import pytest
from agents.factual_qc_agent import FactualQCAgent
from services.ai_service import AIService


def test_factual_qc_audit():
    """Verify factual accuracy audit report structure and scoring."""
    ai = AIService()
    qc_agent = FactualQCAgent(ai_service=ai)

    sample_lesson = {
        "lesson_title": "HTTP Requests and Responses",
        "learning_objective": "Explain GET and POST methods and distinguish between 2xx, 4xx, and 5xx status codes.",
        "introduction": "HTTP is the foundational protocol of the web.",
        "detailed_explanations": "GET is safe and idempotent. POST creates resources. 2xx indicates success, 4xx client errors, 5xx server errors."
    }

    sample_research = {
        "web_sources": [{"title": "MDN HTTP", "url": "https://developer.mozilla.org", "snippet": "GET is idempotent."}],
        "book_sources": [{"title": "HTTP The Definitive Guide", "authors": ["David Gourley"], "publication_year": "2002"}],
        "key_factual_claims": [{"claim": "GET is idempotent", "source": "MDN"}]
    }

    report = qc_agent.audit(sample_lesson, sample_research)

    assert "overall_score" in report
    assert 0 <= report["overall_score"] <= 100
    assert "verification_status" in report
    assert "claims_evaluated_count" in report
    assert "supported_claims_count" in report
    assert "unsupported_claims_count" in report
    assert "identified_issues" in report
    assert isinstance(report["identified_issues"], list)
    assert "final_summary" in report

