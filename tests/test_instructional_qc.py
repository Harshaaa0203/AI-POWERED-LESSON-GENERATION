"""
Tests for QC Agent 2: Instructional Quality and 45-Minute Time Allocation Auditor.
"""

import pytest
from agents.instructional_qc_agent import InstructionalQCAgent
from services.ai_service import AIService


def test_instructional_qc_audit():
    """Verify instructional quality audit report, sub-scores, and 45-min timing audit."""
    ai = AIService()
    qc_agent = InstructionalQCAgent(ai_service=ai)

    sample_lesson = {
        "lesson_title": "HTTP Requests and Responses",
        "learning_objective": "Explain GET and POST methods and distinguish between 2xx, 4xx, and 5xx status codes.",
        "introduction": "3 minutes intro",
        "introduction_minutes": 3,
        "prerequisites_and_key_concepts_minutes": 5,
        "detailed_explanations": "15 minutes explanation of GET and POST",
        "detailed_explanations_minutes": 15,
        "real_world_examples_minutes": 7,
        "practical_activity_minutes": 7,
        "knowledge_check_minutes": 5,
        "lesson_summary_minutes": 3,
        "estimated_total_minutes": 45
    }

    report = qc_agent.audit(sample_lesson)

    assert "overall_score" in report
    assert 0 <= report["overall_score"] <= 100
    assert "status" in report
    assert "objective_alignment_score" in report
    assert "explanation_clarity_score" in report
    assert "activity_effectiveness_score" in report
    assert "time_allocation_audit" in report
    assert report["time_allocation_audit"]["total_allocated_minutes"] <= 45
    assert report["time_allocation_audit"]["is_within_limit"] is True

