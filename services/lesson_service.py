"""
Lesson Service: Central business logic orchestrating the end-to-end pipeline:
validation -> research -> generation -> QC layers -> instructor edits -> persistence.
"""

import logging
from typing import Dict, Any, Optional, Callable
from agents.research_agent import ResearchAgent
from agents.lesson_generator import LessonGenerator
from agents.recommendation_agent import RecommendationAgent
from services.qc_service import QCService
from services.ai_service import AIService
from database.db_manager import DatabaseManager
from utils.validators import validate_lesson_inputs
from utils.error_handler import ValidationError, LessonCreatorError

logger = logging.getLogger("AILessonCreator.LessonService")


class LessonService:
    """Coordinates lesson creation, research, quality control, and instructor review."""

    def __init__(
        self,
        ai_service: Optional[AIService] = None,
        db_manager: Optional[DatabaseManager] = None
    ):
        self.ai_service = ai_service or AIService()
        self.db = db_manager or DatabaseManager()
        self.research_agent = ResearchAgent()
        self.lesson_generator = LessonGenerator(ai_service=self.ai_service)
        self.qc_service = QCService(ai_service=self.ai_service, db_manager=self.db)
        self.rec_agent = RecommendationAgent(ai_service=self.ai_service)

    def create_lesson_pipeline(
        self,
        title: str,
        learning_objective: str,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> Dict[str, Any]:
        """
        Execute full end-to-end lesson creation workflow:
        1. Validate inputs
        2. Create DB record (status=processing)
        3. Multi-source research (web, books, YouTube)
        4. Structured 45-minute lesson generation (14 sections)
        5. Independent Factual Accuracy QC audit
        6. Independent Instructional Quality QC audit
        7. Persist all artifacts to SQLite database
        """
        # Step 1: Validation
        valid, msg = validate_lesson_inputs(title, learning_objective)
        if not valid:
            raise ValidationError(msg)

        if progress_callback:
            progress_callback(0.1, "Initializing lesson database record...")

        # Step 2: Database Initialization
        lesson_id = self.db.create_lesson(
            title=title.strip(),
            learning_objective=learning_objective.strip(),
            status="processing"
        )

        try:
            # Step 3: Research
            if progress_callback:
                progress_callback(0.25, "Gathering verified research from websites, books, and YouTube...")
            research_data = self.research_agent.conduct_research(title, learning_objective)

            self.db.update_lesson(lesson_id, {
                "research_sources": research_data,
                "youtube_resources": research_data.get("youtube_resources", []),
                "book_sources": research_data.get("book_sources", [])
            })

            # Step 4: Lesson Generation
            if progress_callback:
                progress_callback(0.55, "Synthesizing 45-minute structured educational lesson (14 sections)...")
            generated_lesson = self.lesson_generator.generate(title, learning_objective, research_data)

            self.db.update_lesson(lesson_id, {
                "generated_lesson": generated_lesson
            })

            # Step 5 & 6: Independent Dual-Layer Quality Control
            if progress_callback:
                progress_callback(0.75, "Running QC Agent 1: Research & Factual Accuracy Audit...")
            factual_qc = self.qc_service.run_factual_qc(generated_lesson, research_data)

            if progress_callback:
                progress_callback(0.88, "Running QC Agent 2: Instructional Quality & 45-min Pacing Audit...")
            instructional_qc = self.qc_service.run_instructional_qc(generated_lesson)

            # Determine status based on QC scores
            f_score = factual_qc.get("overall_score", 0)
            i_score = instructional_qc.get("overall_score", 0)
            status = "completed" if (f_score >= 80 and i_score >= 80) else "needs_review"

            # Update DB with final reports
            self.db.update_lesson(lesson_id, {
                "factual_qc_report": factual_qc,
                "instructional_qc_report": instructional_qc,
                "status": status
            })

            if progress_callback:
                progress_callback(1.0, "Lesson creation and dual QC verification complete!")

            return self.db.get_lesson(lesson_id)

        except Exception as e:
            logger.error(f"Pipeline failure for lesson {lesson_id}: {e}")
            self.db.update_lesson(lesson_id, {"status": "failed"})
            raise e

    def retry_stage(self, lesson_id: str, stage: str) -> Dict[str, Any]:
        """
        Retry an individual stage without throwing away the rest of the lesson.
        Supports: 'research', 'generation', 'qc'.
        """
        lesson = self.db.get_lesson(lesson_id)
        if not lesson:
            raise LessonCreatorError(f"Lesson {lesson_id} not found.")

        title = lesson.get("title", "")
        objective = lesson.get("learning_objective", "")

        if stage == "research":
            research_data = self.research_agent.conduct_research(title, objective)
            self.db.update_lesson(lesson_id, {
                "research_sources": research_data,
                "youtube_resources": research_data.get("youtube_resources", []),
                "book_sources": research_data.get("book_sources", [])
            })
        elif stage == "generation":
            research_data = lesson.get("research_sources") or self.research_agent.conduct_research(title, objective)
            generated_lesson = self.lesson_generator.generate(title, objective, research_data)
            self.db.update_lesson(lesson_id, {"generated_lesson": generated_lesson})
        elif stage == "qc":
            self.qc_service.rerun_qc_for_lesson(lesson_id)

        return self.db.get_lesson(lesson_id)

    def save_instructor_edits(self, lesson_id: str, edited_lesson: Dict[str, Any]) -> bool:
        """
        Save modified lesson content without overwriting the original generated version.
        """
        return self.db.update_lesson(lesson_id, {"edited_lesson": edited_lesson})

    def apply_qc_recommendation(self, lesson_id: str, recommendation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply a specific recommendation to the lesson's edited copy and mark it applied.
        """
        lesson = self.db.get_lesson(lesson_id)
        if not lesson:
            raise LessonCreatorError("Lesson not found.")

        active_lesson = lesson.get("edited_lesson") or lesson.get("generated_lesson")
        updated_lesson = self.rec_agent.apply_recommendation(active_lesson, recommendation)

        applied_list = lesson.get("applied_recommendations") or []
        rec_id = recommendation.get("id")
        if rec_id and rec_id not in applied_list:
            applied_list.append(rec_id)

        self.db.update_lesson(lesson_id, {
            "edited_lesson": updated_lesson,
            "applied_recommendations": applied_list
        })
        return self.db.get_lesson(lesson_id)

    def regenerate_lesson_section(
        self,
        lesson_id: str,
        section_name: str,
        custom_instructions: str = ""
    ) -> Dict[str, Any]:
        """
        Regenerate a single section using AI, preserving the rest of the lesson.
        """
        lesson = self.db.get_lesson(lesson_id)
        if not lesson:
            raise LessonCreatorError("Lesson not found.")

        active_lesson = lesson.get("edited_lesson") or lesson.get("generated_lesson")
        updated_lesson = self.rec_agent.regenerate_section(active_lesson, section_name, custom_instructions)

        self.db.update_lesson(lesson_id, {"edited_lesson": updated_lesson})
        return self.db.get_lesson(lesson_id)
