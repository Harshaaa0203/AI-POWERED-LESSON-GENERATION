"""
Database manager for SQLite operations.
Provides thread-safe access and robust CRUD operations for lessons, research, and QC reports.
"""

import sqlite3
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from database.schema import CREATE_LESSONS_TABLE, CREATE_INDEXES


class DatabaseManager:
    """Manages SQLite storage for lessons and associated artifacts."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.getenv("DATABASE_PATH", "lessons.db")
        self.init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Create a database connection with dict-like row factory."""
        conn = sqlite3.connect(self.db_path, timeout=30.0, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        """Initialize the database schema and indexes."""
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(CREATE_LESSONS_TABLE)
            for idx_sql in CREATE_INDEXES:
                cursor.execute(idx_sql)
            conn.commit()

    def create_lesson(
        self,
        title: str,
        learning_objective: str,
        lesson_id: Optional[str] = None,
        status: str = "processing",
        research_sources: Optional[Dict[str, Any]] = None,
        youtube_resources: Optional[List[Dict[str, Any]]] = None,
        book_sources: Optional[List[Dict[str, Any]]] = None,
        generated_lesson: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create a new lesson record and return its ID."""
        lid = lesson_id or str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO lessons (
                    id, title, learning_objective, status,
                    research_sources, youtube_resources, book_sources,
                    generated_lesson, edited_lesson, factual_qc_report,
                    instructional_qc_report, applied_recommendations,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    lid,
                    title.strip(),
                    learning_objective.strip(),
                    status,
                    json.dumps(research_sources or {}, ensure_ascii=False),
                    json.dumps(youtube_resources or [], ensure_ascii=False),
                    json.dumps(book_sources or [], ensure_ascii=False),
                    json.dumps(generated_lesson or {}, ensure_ascii=False),
                    json.dumps(None),
                    json.dumps(None),
                    json.dumps(None),
                    json.dumps([]),
                    now,
                    now,
                ),
            )
            conn.commit()
        return lid

    def get_lesson(self, lesson_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a lesson by ID, deserializing JSON fields."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM lessons WHERE id = ?", (lesson_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_dict(row)

    def update_lesson(self, lesson_id: str, updates: Dict[str, Any]) -> bool:
        """Update selected fields of a lesson."""
        allowed_fields = {
            "title",
            "learning_objective",
            "status",
            "research_sources",
            "youtube_resources",
            "book_sources",
            "generated_lesson",
            "edited_lesson",
            "factual_qc_report",
            "instructional_qc_report",
            "applied_recommendations",
        }

        set_clauses = []
        params = []
        now = datetime.now(timezone.utc).isoformat()

        for k, v in updates.items():
            if k in allowed_fields:
                set_clauses.append(f"{k} = ?")
                if isinstance(v, (dict, list)):
                    params.append(json.dumps(v, ensure_ascii=False))
                else:
                    params.append(v)

        if not set_clauses:
            return False

        set_clauses.append("updated_at = ?")
        params.append(now)
        params.append(lesson_id)

        sql = f"UPDATE lessons SET {', '.join(set_clauses)} WHERE id = ?"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, tuple(params))
            conn.commit()
            return cursor.rowcount > 0

    def delete_lesson(self, lesson_id: str) -> bool:
        """Delete a lesson by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM lessons WHERE id = ?", (lesson_id,))
            conn.commit()
            return cursor.rowcount > 0

    def list_lessons(
        self,
        limit: int = 50,
        offset: int = 0,
        status_filter: Optional[str] = None,
        search_query: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List lessons ordered by created_at DESC with optional filtering."""
        sql = "SELECT * FROM lessons WHERE 1=1"
        params: List[Any] = []

        if status_filter and status_filter != "all":
            sql += " AND status = ?"
            params.append(status_filter)

        if search_query:
            sql += " AND (title LIKE ? OR learning_objective LIKE ?)"
            term = f"%{search_query.strip()}%"
            params.extend([term, term])

        sql += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, tuple(params))
            rows = cursor.fetchall()
            return [self._row_to_dict(r) for r in rows]

    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Calculate dashboard statistics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Total count
            cursor.execute("SELECT COUNT(*) FROM lessons")
            total = cursor.fetchone()[0]

            # Completed count
            cursor.execute("SELECT COUNT(*) FROM lessons WHERE status = 'completed'")
            completed = cursor.fetchone()[0]

            # Needs review count
            cursor.execute("SELECT COUNT(*) FROM lessons WHERE status = 'needs_review'")
            needs_review = cursor.fetchone()[0]

            # Processing count
            cursor.execute("SELECT COUNT(*) FROM lessons WHERE status = 'processing'")
            processing = cursor.fetchone()[0]

            # Average scores from QC reports
            cursor.execute("SELECT factual_qc_report, instructional_qc_report FROM lessons")
            all_reports = cursor.fetchall()

            factual_scores = []
            instructional_scores = []

            for row in all_reports:
                f_rep = row[0]
                i_rep = row[1]
                if f_rep:
                    try:
                        d = json.loads(f_rep)
                        if isinstance(d, dict) and "overall_score" in d:
                            factual_scores.append(float(d["overall_score"]))
                    except Exception:
                        pass
                if i_rep:
                    try:
                        d = json.loads(i_rep)
                        if isinstance(d, dict) and "overall_score" in d:
                            instructional_scores.append(float(d["overall_score"]))
                    except Exception:
                        pass

            avg_factual = round(sum(factual_scores) / len(factual_scores), 1) if factual_scores else 0.0
            avg_instructional = round(sum(instructional_scores) / len(instructional_scores), 1) if instructional_scores else 0.0

            # Recent lessons
            cursor.execute("SELECT * FROM lessons ORDER BY created_at DESC LIMIT 5")
            recent = [self._row_to_dict(r) for r in cursor.fetchall()]

            return {
                "total_lessons": total,
                "completed_lessons": completed,
                "needs_review_lessons": needs_review,
                "processing_lessons": processing,
                "avg_factual_score": avg_factual,
                "avg_instructional_score": avg_instructional,
                "recent_lessons": recent,
            }

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert a sqlite3.Row to a deserialized dictionary."""
        d = dict(row)
        for json_col in [
            "research_sources",
            "youtube_resources",
            "book_sources",
            "generated_lesson",
            "edited_lesson",
            "factual_qc_report",
            "instructional_qc_report",
            "applied_recommendations",
        ]:
            val = d.get(json_col)
            if val is not None and isinstance(val, str):
                try:
                    d[json_col] = json.loads(val)
                except Exception:
                    d[json_col] = None
        return d
