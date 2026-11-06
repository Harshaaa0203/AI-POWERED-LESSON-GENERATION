"""
Unit and integration tests for SQLite Database operations.
"""

import os
import pytest
from database.db_manager import DatabaseManager


@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test_lessons.db"
    manager = DatabaseManager(db_path=str(db_file))
    return manager


def test_create_and_get_lesson(temp_db):
    """Test creating and retrieving a lesson."""
    lid = temp_db.create_lesson(
        title="Test Lesson Title",
        learning_objective="Demonstrate database persistence.",
        status="processing"
    )
    assert lid is not None

    lesson = temp_db.get_lesson(lid)
    assert lesson is not None
    assert lesson["title"] == "Test Lesson Title"
    assert lesson["learning_objective"] == "Demonstrate database persistence."
    assert lesson["status"] == "processing"


def test_update_lesson(temp_db):
    """Test updating lesson status and generated JSON fields."""
    lid = temp_db.create_lesson(title="Initial Title", learning_objective="Initial Objective")

    updates = {
        "title": "Updated Title",
        "status": "completed",
        "generated_lesson": {"lesson_title": "Updated Title", "introduction": "Test intro"}
    }
    success = temp_db.update_lesson(lid, updates)
    assert success is True

    updated = temp_db.get_lesson(lid)
    assert updated["title"] == "Updated Title"
    assert updated["status"] == "completed"
    assert updated["generated_lesson"]["introduction"] == "Test intro"


def test_delete_lesson(temp_db):
    """Test deleting a lesson."""
    lid = temp_db.create_lesson(title="To Delete", learning_objective="Will be removed")
    assert temp_db.get_lesson(lid) is not None

    deleted = temp_db.delete_lesson(lid)
    assert deleted is True
    assert temp_db.get_lesson(lid) is None


def test_dashboard_stats(temp_db):
    """Test calculation of dashboard KPIs and averages."""
    lid1 = temp_db.create_lesson(title="Lesson 1", learning_objective="Obj 1", status="completed")
    lid2 = temp_db.create_lesson(title="Lesson 2", learning_objective="Obj 2", status="needs_review")

    temp_db.update_lesson(lid1, {
        "factual_qc_report": {"overall_score": 90.0},
        "instructional_qc_report": {"overall_score": 95.0}
    })
    temp_db.update_lesson(lid2, {
        "factual_qc_report": {"overall_score": 80.0},
        "instructional_qc_report": {"overall_score": 85.0}
    })

    stats = temp_db.get_dashboard_stats()
    assert stats["total_lessons"] == 2
    assert stats["completed_lessons"] == 1
    assert stats["needs_review_lessons"] == 1
    assert stats["avg_factual_score"] == 85.0
    assert stats["avg_instructional_score"] == 90.0

