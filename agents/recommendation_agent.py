"""
QC Recommendation Agent: synthesizes actionable improvements from both QC reports,
enables selective application of recommendations, section-level regeneration,
and version tracking (original generated vs instructor-revised).
"""

import copy
import logging
from typing import Dict, Any, List, Optional
from services.ai_service import AIService

logger = logging.getLogger("AILessonCreator.RecommendationAgent")


class RecommendationAgent:
    """Combines QC findings into actionable recommendations and manages selective section updates."""

    def __init__(self, ai_service: Optional[AIService] = None):
        self.ai_service = ai_service or AIService()

    def extract_recommendations(
        self,
        factual_qc_report: Optional[Dict[str, Any]],
        instructional_qc_report: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Merge and categorize issues from both QC agents into individual, actionable recommendations.
        """
        recs: List[Dict[str, Any]] = []

        # 1. From Factual Accuracy QC
        if factual_qc_report:
            issues = factual_qc_report.get("identified_issues", [])
            for idx, issue in enumerate(issues):
                severity = issue.get("severity", "Medium")
                claim = issue.get("claim", "")
                corr = issue.get("suggested_correction") or issue.get("explanation", "")
                recs.append({
                    "id": f"fact_rec_{idx + 1}",
                    "source": "Factual Accuracy QC",
                    "category": "Factual Correction",
                    "severity": severity,
                    "target_section": "detailed_explanations",
                    "title": f"Factual Issue: {issue.get('issue_type', 'Correction Needed')}",
                    "description": claim,
                    "recommendation": corr,
                    "evidence": issue.get("evidence", ""),
                    "source_url": issue.get("source_url", ""),
                    "applied": False
                })

            # Missing info from factual QC
            missing = factual_qc_report.get("missing_information", [])
            for idx, item in enumerate(missing):
                recs.append({
                    "id": f"fact_missing_{idx + 1}",
                    "source": "Factual Accuracy QC",
                    "category": "Missing Context",
                    "severity": "Low",
                    "target_section": "detailed_explanations",
                    "title": "Incorporate Missing Technical Nuance",
                    "description": item,
                    "recommendation": f"Add brief reference to: {item}",
                    "evidence": "Recommended by standards / documentation",
                    "source_url": "",
                    "applied": False
                })

        # 2. From Instructional Quality QC
        if instructional_qc_report:
            gaps = instructional_qc_report.get("instructional_gaps", [])
            for idx, gap in enumerate(gaps):
                sec = gap.get("section", "detailed_explanations")
                # Map to standard section key if needed
                sec_key = self._map_section_name(sec)
                recs.append({
                    "id": f"inst_gap_{idx + 1}",
                    "source": "Instructional Quality QC",
                    "category": "Pedagogical Improvement",
                    "severity": gap.get("severity", "Medium"),
                    "target_section": sec_key,
                    "title": f"Pedagogical Gap in {sec}",
                    "description": gap.get("gap", ""),
                    "recommendation": gap.get("suggested_improvement", ""),
                    "evidence": "Pedagogical alignment audit",
                    "source_url": "",
                    "applied": False
                })

        # Sort with Critical / High first
        severity_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
        recs.sort(key=lambda x: severity_order.get(x.get("severity"), 4))
        return recs

    def apply_recommendation(
        self,
        current_lesson: Dict[str, Any],
        recommendation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Safely apply a specific recommendation into the lesson content, preserving original data.
        Returns a new copy of the updated lesson dictionary.
        """
        updated = copy.deepcopy(current_lesson)
        target_sec = recommendation.get("target_section", "detailed_explanations")
        rec_text = recommendation.get("recommendation", "")

        if not rec_text:
            return updated

        if target_sec == "detailed_explanations":
            current_text = updated.get("detailed_explanations", "")
            note = f"\n\n> **Instructor QC Revision**: {rec_text}\n"
            updated["detailed_explanations"] = current_text + note

        elif target_sec == "learning_activities":
            activities = updated.get("learning_activities", [])
            if isinstance(activities, list) and len(activities) > 0:
                act = activities[0]
                act["instructions"] = act.get("instructions", "") + f"\n- **QC Enhancement**: {rec_text}"
            else:
                updated["learning_activities"] = [{
                    "activity_title": "Enhanced Practice Activity",
                    "instructions": rec_text,
                    "expected_outcome": "Improved student comprehension.",
                    "duration_minutes": 7
                }]

        elif target_sec == "introduction":
            intro = updated.get("introduction", "")
            updated["introduction"] = f"{intro} ({rec_text})"

        elif target_sec == "lesson_summary":
            summ = updated.get("lesson_summary", "")
            updated["lesson_summary"] = f"{summ} [Note: {rec_text}]"

        logger.info(f"Applied recommendation '{recommendation.get('id')}' to section '{target_sec}'.")
        return updated

    def regenerate_section(
        self,
        current_lesson: Dict[str, Any],
        section_name: str,
        custom_instructions: str = ""
    ) -> Dict[str, Any]:
        """
        Regenerate ONLY the selected section using the AI service while keeping the
        remaining 13 sections identical.
        """
        updated = copy.deepcopy(current_lesson)
        title = updated.get("lesson_title", "Lesson")
        objective = updated.get("learning_objective", "")
        current_section_val = updated.get(section_name, "")

        prompt = f"""
You are revising ONLY a single section of the lesson titled '{title}'.
Learning Objective: {objective}

Target Section: '{section_name}'
Current Section Content:
{current_section_val}

Instructor Revision Instructions / QC Feedback:
{custom_instructions or 'Enhance clarity, accuracy, and pedagogical engagement while maintaining timing constraints.'}

Generate an improved replacement for ONLY this '{section_name}' section.
Return pure JSON with a single key '{section_name}' containing the improved text or list.
"""
        logger.info(f"Regenerating section '{section_name}'...")
        res = self.ai_service.generate_json(prompt)
        if section_name in res:
            updated[section_name] = res[section_name]
            logger.info(f"Section '{section_name}' regenerated successfully.")
        else:
            logger.warning(f"Failed to find key '{section_name}' in LLM response: {res}")

        return updated

    def _map_section_name(self, name: str) -> str:
        """Map human or freeform section names to internal dict keys."""
        norm = name.lower().replace(" ", "_")
        for valid in [
            "introduction", "key_concepts", "detailed_explanations",
            "real_world_examples", "learning_activities",
            "knowledge_check_questions", "lesson_summary"
        ]:
            if valid in norm or norm in valid:
                return valid
        return "detailed_explanations"

