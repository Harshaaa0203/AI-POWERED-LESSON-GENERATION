"""
Mandatory Test Cases 1 and 2 Runner.
Validates the complete end-to-end workflow on the exact assignment benchmarks:
- Test Case 1: HTTP Requests and Responses
- Test Case 2: Binary Search Algorithm
"""

import os
import pytest
from services.lesson_service import LessonService
from database.db_manager import DatabaseManager
from exports.pdf_exporter import PDFExporter
from exports.markdown_exporter import MarkdownExporter
from utils.validators import validate_lesson_structure, MANDATORY_LESSON_SECTIONS


@pytest.fixture
def clean_service(tmp_path):
    db_path = str(tmp_path / "mandatory_test.db")
    db = DatabaseManager(db_path=db_path)
    service = LessonService(db_manager=db)
    return service, db


def test_mandatory_case_1_http(clean_service):
    """
    TEST CASE 1:
    Title: HTTP Requests and Responses
    Objective: Explain GET and POST methods and distinguish between 2xx, 4xx, and 5xx response status categories.
    """
    service, db = clean_service
    title = "HTTP Requests and Responses"
    objective = "Explain GET and POST methods and distinguish between 2xx, 4xx, and 5xx response status categories."

    # 1. Run complete pipeline
    lesson_record = service.create_lesson_pipeline(title, objective)
    assert lesson_record is not None
    lid = lesson_record["id"]

    # 2. Check research
    research = lesson_record.get("research_sources")
    assert research is not None
    assert lesson_record.get("youtube_resources") is not None
    assert len(lesson_record.get("youtube_resources")) > 0

    # 3. Check lesson generation
    gen_lesson = lesson_record.get("generated_lesson")
    assert gen_lesson is not None
    for sec in MANDATORY_LESSON_SECTIONS:
        assert sec in gen_lesson, f"Missing section: {sec}"
    assert gen_lesson.get("estimated_total_minutes") <= 45

    # Check content contains GET, POST, and status categories
    text_corpus = (
        gen_lesson.get("detailed_explanations", "") + " " +
        str(gen_lesson.get("real_world_examples", ""))
    )
    assert "GET" in text_corpus
    assert "POST" in text_corpus
    assert "2xx" in text_corpus or "200" in text_corpus
    assert "4xx" in text_corpus or "404" in text_corpus
    assert "5xx" in text_corpus or "500" in text_corpus

    # 4. Check Factual QC Agent 1
    f_qc = lesson_record.get("factual_qc_report")
    assert f_qc is not None
    assert "overall_score" in f_qc
    assert f_qc["overall_score"] >= 80.0
    assert "verification_status" in f_qc
    assert f_qc.get("claims_evaluated_count", 0) > 0

    # 5. Check Instructional QC Agent 2
    i_qc = lesson_record.get("instructional_qc_report")
    assert i_qc is not None
    assert "overall_score" in i_qc
    assert i_qc["overall_score"] >= 80.0
    assert "time_allocation_audit" in i_qc
    assert i_qc["time_allocation_audit"]["total_allocated_minutes"] <= 45

    # 6. Test Instructor Edits & Recommendations
    recs = service.rec_agent.extract_recommendations(f_qc, i_qc)
    assert isinstance(recs, list)
    if recs:
        # Apply first recommendation
        updated = service.apply_qc_recommendation(lid, recs[0])
        assert updated.get("edited_lesson") is not None
        assert recs[0]["id"] in updated.get("applied_recommendations", [])

    # 7. Test PDF and Markdown exports
    active_lesson = db.get_lesson(lid).get("edited_lesson") or gen_lesson
    pdf_exporter = PDFExporter()
    pdf_out = os.path.join("exports", f"Test1_Lesson_{lid[:8]}.pdf")
    pdf_path = pdf_exporter.export_lesson_pdf(active_lesson, pdf_out)
    assert os.path.exists(pdf_path)
    assert os.path.getsize(pdf_path) > 1000

    md_exporter = MarkdownExporter()
    md_out = md_exporter.export_lesson(active_lesson)
    assert len(md_out) > 500
    assert title in md_out


def test_mandatory_case_2_binary_search(clean_service):
    """
    TEST CASE 2:
    Title: Binary Search Algorithm
    Objective: Explain the divide-and-conquer principle of binary search and analyze its logarithmic O(log n) time complexity.
    """
    service, db = clean_service
    title = "Binary Search Algorithm"
    objective = "Explain the divide-and-conquer principle of binary search and analyze its logarithmic O(log n) time complexity."

    # 1. Run complete pipeline
    lesson_record = service.create_lesson_pipeline(title, objective)
    assert lesson_record is not None
    lid = lesson_record["id"]

    # 2. Check research
    research = lesson_record.get("research_sources")
    assert research is not None

    # 3. Check lesson generation
    gen_lesson = lesson_record.get("generated_lesson")
    assert gen_lesson is not None
    for sec in MANDATORY_LESSON_SECTIONS:
        assert sec in gen_lesson, f"Missing section: {sec}"
    assert gen_lesson.get("estimated_total_minutes") <= 45

    # 4. Check Dual QC reports
    f_qc = lesson_record.get("factual_qc_report")
    assert f_qc is not None
    assert f_qc["overall_score"] >= 80.0

    i_qc = lesson_record.get("instructional_qc_report")
    assert i_qc is not None
    assert i_qc["overall_score"] >= 80.0

    # 5. Test Exports
    pdf_exporter = PDFExporter()
    pdf_out = os.path.join("exports", f"Test2_Lesson_{lid[:8]}.pdf")
    pdf_path = pdf_exporter.export_lesson_pdf(gen_lesson, pdf_out)
    assert os.path.exists(pdf_path)
    assert os.path.getsize(pdf_path) > 1000

