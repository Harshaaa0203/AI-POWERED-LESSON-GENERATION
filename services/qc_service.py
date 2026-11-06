"""
QC Service: Orchestrates independent execution of both Quality Control agents,
handles report formatting, score aggregation, and QC reruns.
"""

import logging
from typing import Dict, Any, Optional, Tuple
from agents.factual_qc_agent import FactualQCAgent
from agents.instructional_qc_agent import InstructionalQCAgent
from database.db_manager import DatabaseManager
from services.ai_service import AIService

logger = logging.getLogger("AILessonCreator.QCService")


class QCService:
    """Manages independent execution and persistence of Quality Control audits."""

    def __init__(self, ai_service: Optional[AIService] = None, db_manager: Optional[DatabaseManager] = None):
        self.ai_service = ai_service or AIService()
        self.factual_qc = FactualQCAgent(ai_service=self.ai_service)
        self.instructional_qc = InstructionalQCAgent(ai_service=self.ai_service)
        self.db = db_manager or DatabaseManager()

    def run_factual_qc(self, lesson_data: Dict[str, Any], research_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run independent factual accuracy audit."""
        return self.factual_qc.audit(lesson_data, research_data)

    def run_instructional_qc(self, lesson_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run independent instructional quality audit."""
        return self.instructional_qc.audit(lesson_data)

    def run_both_qc(
        self,
        lesson_data: Dict[str, Any],
        research_data: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Run both QC layers independently and return (factual_report, instructional_report).
        Ensures neither agent depends on or copies from the other.
        """
        logger.info("Executing dual-layer independent QC audits...")
        factual_report = self.run_factual_qc(lesson_data, research_data)
        instructional_report = self.run_instructional_qc(lesson_data)
        return factual_report, instructional_report

    def rerun_qc_for_lesson(self, lesson_id: str) -> Optional[Dict[str, Any]]:
        """
        Rerun both QC audits on the latest version of a lesson (preferring edited version if present),
        and persist updated reports to SQLite.
        """
        lesson = self.db.get_lesson(lesson_id)
        if not lesson:
            return None

        # Prefer edited lesson over generated lesson
        active_lesson = lesson.get("edited_lesson") or lesson.get("generated_lesson")
        if not active_lesson:
            return None

        # Build research dict
        research_data = {
            "web_sources": lesson.get("research_sources", {}).get("web_sources", []),
            "book_sources": lesson.get("book_sources", []),
            "youtube_resources": lesson.get("youtube_resources", []),
            "key_factual_claims": lesson.get("research_sources", {}).get("key_factual_claims", [])
        }

        f_rep, i_rep = self.run_both_qc(active_lesson, research_data)

        # Update status based on scores
        f_score = f_rep.get("overall_score", 0)
        i_score = i_rep.get("overall_score", 0)
        new_status = "completed" if (f_score >= 80 and i_score >= 80) else "needs_review"

        self.db.update_lesson(lesson_id, {
            "factual_qc_report": f_rep,
            "instructional_qc_report": i_rep,
            "status": new_status
        })

        return self.db.get_lesson(lesson_id)
