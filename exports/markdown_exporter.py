"""
Markdown Exporter: Formats lessons, QC reports, and research dossiers into
clean, standard GitHub-Flavored Markdown documents.
"""

from typing import Dict, Any, List


class MarkdownExporter:
    """Generates standard Markdown outputs for lessons and audit reports."""

    @staticmethod
    def export_lesson(lesson: Dict[str, Any]) -> str:
        """Render complete 14-section 45-minute lesson to Markdown."""
        md = []
        title = lesson.get("lesson_title", "Untitled Lesson")
        obj = lesson.get("learning_objective", "")
        level = lesson.get("difficulty_level", "Intermediate")
        dur = lesson.get("estimated_total_minutes", 45)

        md.append(f"# {title}\n")
        md.append(f"**Target Duration:** {dur} Minutes | **Difficulty Level:** {level}\n")
        md.append(f"### 🎯 Learning Objective\n> {obj}\n")

        # 3. Introduction
        md.append(f"## 1. Introduction (⏱️ {lesson.get('introduction_minutes', 3)} mins)\n")
        md.append(f"{lesson.get('introduction', '')}\n")

        # 4 & 5. Prerequisites & Key Concepts
        md.append(f"## 2. Prerequisites & Key Concepts (⏱️ {lesson.get('prerequisites_and_key_concepts_minutes', 5)} mins)\n")
        md.append("### Prerequisites\n")
        for prereq in lesson.get("prerequisites", []):
            md.append(f"- {prereq}")
        md.append("\n### Key Concepts\n")
        for kc in lesson.get("key_concepts", []):
            md.append(f"- **{kc.get('concept')}**: {kc.get('definition')}")
        md.append("")

        # 6. Detailed Explanations
        md.append(f"## 3. Detailed Explanations (⏱️ {lesson.get('detailed_explanations_minutes', 15)} mins)\n")
        md.append(f"{lesson.get('detailed_explanations', '')}\n")

        # 7. Real-World Examples
        md.append(f"## 4. Real-World Examples (⏱️ {lesson.get('real_world_examples_minutes', 7)} mins)\n")
        for ex in lesson.get("real_world_examples", []):
            md.append(f"### 💡 {ex.get('scenario')}")
            if ex.get("method_used"):
                md.append(f"**Method/Context:** `{ex.get('method_used')}`\n")
            md.append(f"{ex.get('explanation')}\n")

        # 8. Practical Applications
        md.append("## 5. Practical Applications\n")
        md.append(f"{lesson.get('practical_applications', '')}\n")

        # 9. Learning Activities
        md.append(f"## 6. Learning Activities (⏱️ {lesson.get('practical_activity_minutes', 7)} mins)\n")
        for act in lesson.get("learning_activities", []):
            md.append(f"### 🛠️ {act.get('activity_title')}")
            md.append(f"**Instructions:**\n{act.get('instructions')}\n")
            md.append(f"**Expected Outcome:** {act.get('expected_outcome')}\n")
            md.append(f"**Duration:** {act.get('duration_minutes', 7)} minutes\n")

        # 10 & 11. Knowledge Check Questions, Answers & Explanations
        md.append(f"## 7. Knowledge Check Questions (⏱️ {lesson.get('knowledge_check_minutes', 5)} mins)\n")
        for q in lesson.get("knowledge_check_questions", []):
            md.append(f"**Q{q.get('question_id', '')}: {q.get('question')}**\n")
            for opt in q.get("options", []):
                md.append(f"- [ ] {opt}")
            md.append(f"\n*Correct Answer:* **{q.get('correct_answer')}**")
            md.append(f"*Explanation:* {q.get('explanation')}\n")

        md.append("### Answers & Pedagogical Explanations\n")
        md.append(f"{lesson.get('answers_and_explanations', '')}\n")

        # 12. Lesson Summary
        md.append(f"## 8. Lesson Summary (⏱️ {lesson.get('lesson_summary_minutes', 3)} mins)\n")
        md.append(f"{lesson.get('lesson_summary', '')}\n")

        # 13. Additional Resources
        md.append("## 9. Additional Learning Resources\n")
        for r in lesson.get("additional_learning_resources", []):
            md.append(f"- [{r.get('title')}]({r.get('url')}) - *{r.get('type', 'Resource')}*")
        md.append("")

        # 14. References & Source Links
        md.append("## 10. References & Source Links\n")
        for ref in lesson.get("references_and_source_links", []):
            md.append(f"- [{ref.get('source')}]({ref.get('url')})")
        md.append("")

        return "\n".join(md)

    @staticmethod
    def export_factual_qc(report: Dict[str, Any], title: str = "Lesson") -> str:
        """Render Factual Accuracy QC report to Markdown."""
        md = []
        score = report.get("overall_score", 0)
        status = report.get("verification_status", "N/A")

        md.append(f"# Quality Control Audit: Research & Factual Accuracy\n")
        md.append(f"**Audited Lesson:** {title}\n")
        md.append(f"**Overall Accuracy Score:** `{score}/100` | **Status:** `{status}`\n")
        md.append("### Summary Statistics\n")
        md.append(f"- **Claims Evaluated:** {report.get('claims_evaluated_count', 0)}")
        md.append(f"- **Supported Claims:** {report.get('supported_claims_count', 0)}")
        md.append(f"- **Unsupported Claims:** {report.get('unsupported_claims_count', 0)}")
        md.append(f"- **Questionable Claims:** {report.get('questionable_claims_count', 0)}\n")

        md.append("### Identified Issues & Suggested Corrections\n")
        issues = report.get("identified_issues", [])
        if issues:
            for idx, iss in enumerate(issues, 1):
                md.append(f"#### {idx}. [{iss.get('severity', 'Medium')}] {iss.get('issue_type', 'Issue')}")
                md.append(f"- **Claim:** {iss.get('claim')}")
                md.append(f"- **Explanation:** {iss.get('explanation')}")
                if iss.get("evidence"):
                    md.append(f"- **Evidence:** {iss.get('evidence')}")
                if iss.get("source_url"):
                    md.append(f"- **Source URL:** [{iss.get('source_url')}]({iss.get('source_url')})")
                md.append(f"- **Suggested Correction:** *{iss.get('suggested_correction')}*\n")
        else:
            md.append("✅ No critical factual inaccuracies or unsupported claims discovered.\n")

        md.append("### Source Credibility Audit\n")
        for sc in report.get("source_credibility_audit", []):
            md.append(f"- **{sc.get('domain')}**: Credibility `{sc.get('credibility')}` | Relevance `{sc.get('relevance')}`")

        md.append("\n### Auditor Summary\n")
        md.append(f"{report.get('final_summary', '')}\n")
        return "\n".join(md)

    @staticmethod
    def export_instructional_qc(report: Dict[str, Any], title: str = "Lesson") -> str:
        """Render Instructional Quality QC report to Markdown."""
        md = []
        score = report.get("overall_score", 0)
        status = report.get("status", "N/A")

        md.append(f"# Quality Control Audit: Instructional Quality & Pacing\n")
        md.append(f"**Audited Lesson:** {title}\n")
        md.append(f"**Overall Quality Score:** `{score}/100` | **Status:** `{status}`\n")

        md.append("### Pedagogical Sub-Scores\n")
        md.append(f"- **Learning Objective Alignment:** `{report.get('objective_alignment_score', 0)}/100`")
        md.append(f"- **Explanation Clarity:** `{report.get('explanation_clarity_score', 0)}/100`")
        md.append(f"- **Example Relevance:** `{report.get('example_relevance_score', 0)}/100`")
        md.append(f"- **Activity Effectiveness:** `{report.get('activity_effectiveness_score', 0)}/100`")
        md.append(f"- **Knowledge Check Quality:** `{report.get('knowledge_check_quality_score', 0)}/100`\n")

        md.append("### Time Allocation Audit (45-Minute Limit)\n")
        t_audit = report.get("time_allocation_audit", {})
        md.append(f"- **Total Allocated Minutes:** {t_audit.get('total_allocated_minutes', 45)} mins")
        md.append(f"- **Within 45-Min Constraint:** {'✅ Yes' if t_audit.get('is_within_limit', True) else '❌ No'}")
        md.append(f"- **Pacing Evaluation:** {t_audit.get('evaluation', '')}\n")

        md.append("### Identified Instructional Gaps & Improvements\n")
        gaps = report.get("instructional_gaps", [])
        if gaps:
            for idx, g in enumerate(gaps, 1):
                md.append(f"#### {idx}. [{g.get('severity', 'Medium')}] Section: {g.get('section')}")
                md.append(f"- **Pedagogical Gap:** {g.get('gap')}")
                md.append(f"- **Improvement Recommendation:** *{g.get('suggested_improvement')}*\n")
        else:
            md.append("✅ No major pedagogical bottlenecks or cognitive gaps identified.\n")

        md.append("### Dual-Mode Pedagogical Suitability\n")
        dual = report.get("dual_mode_suitability", {})
        md.append(f"- **Self-Directed Learning:** `{dual.get('self_learning_rating', 'Good')}`")
        md.append(f"- **Instructor-Led Teaching:** `{dual.get('instructor_led_rating', 'Good')}`")
        if dual.get("notes"):
            md.append(f"- **Notes:** {dual.get('notes')}\n")

        md.append("### Auditor Summary\n")
        md.append(f"{report.get('final_summary', '')}\n")
        return "\n".join(md)

    @staticmethod
    def export_complete_package(lesson_record: Dict[str, Any]) -> str:
        """Combine lesson, research sources, and both QC reports into one master Markdown file."""
        title = lesson_record.get("title", "Lesson")
        active_lesson = lesson_record.get("edited_lesson") or lesson_record.get("generated_lesson", {})
        f_rep = lesson_record.get("factual_qc_report", {})
        i_rep = lesson_record.get("instructional_qc_report", {})

        md = [
            f"# Complete Educational Lesson Dossier: {title}\n",
            f"**Lesson ID:** `{lesson_record.get('id')}`  ",
            f"**Creation Date:** `{lesson_record.get('created_at')}`  ",
            f"**Status:** `{lesson_record.get('status')}`\n",
            "---\n",
            MarkdownExporter.export_lesson(active_lesson),
            "\n---\n",
            MarkdownExporter.export_factual_qc(f_rep, title),
            "\n---\n",
            MarkdownExporter.export_instructional_qc(i_rep, title),
        ]
        return "\n".join(md)

