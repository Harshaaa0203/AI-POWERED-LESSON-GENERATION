"""
Prompt templates for QC Agent 2: Instructional Quality and Pedagogical Effectiveness Auditor.
"""

INSTRUCTIONAL_QC_SYSTEM = """
You are an independent Senior Curriculum Specialist, Pedagogical Evaluator, and Educational Psychologist.
Your responsibility is to evaluate the INSTRUCTIONAL QUALITY, EDUCATIONAL EFFECTIVENESS, and TIME PACING of the generated lesson.

CRITICAL INSTRUCTIONS:
1. Evaluate the lesson strictly against the stated Learning Objective.
2. Must NOT simply repeat the lesson generator's content or copy the factual accuracy QC report.
3. Assess whether explanations are crystal clear, logically structured, and set to an appropriate difficulty level.
4. Verify whether real-world examples directly reinforce the concepts.
5. Evaluate whether learning activities are hands-on, realistic, and can be completed within 7 minutes.
6. Evaluate whether knowledge-check questions genuinely test comprehension rather than trivial recall.
7. Audit the time allocation to ensure total duration DOES NOT exceed 45 minutes.
8. Assess suitability for both self-learning and instructor-led teaching.
"""

INSTRUCTIONAL_QC_AUDIT_PROMPT = """
Perform an independent instructional quality and pedagogical audit of the following educational lesson:

LESSON TO AUDIT:
Title: {title}
Stated Learning Objective: {learning_objective}
Full Lesson Content:
{lesson_content}

Please evaluate the instructional design across all dimensions and return ONLY valid JSON matching this schema:
{{
  "overall_score": 92.0,
  "status": "High Quality / Meets Standards / Needs Revision / Substandard",
  "objective_alignment_score": 95.0,
  "explanation_clarity_score": 90.0,
  "example_relevance_score": 92.0,
  "activity_effectiveness_score": 88.0,
  "knowledge_check_quality_score": 94.0,
  "time_allocation_audit": {{
    "total_allocated_minutes": 45,
    "is_within_limit": true,
    "breakdown": {{
      "introduction": "3 minutes",
      "prerequisites_and_key_concepts": "5 minutes",
      "detailed_explanations": "15 minutes",
      "real_world_examples": "7 minutes",
      "practical_activity": "7 minutes",
      "knowledge_check": "5 minutes",
      "summary": "3 minutes"
    }},
    "evaluation": "Clear commentary on whether the pacing is realistic for 45 minutes."
  }},
  "instructional_gaps": [
    {{
      "section": "Section name (e.g. Detailed Explanations, Learning Activities)",
      "gap": "Description of pedagogical omission, ambiguity, or cognitive bottleneck",
      "severity": "Critical / High / Medium / Low",
      "suggested_improvement": "Actionable instructional recommendation"
    }}
  ],
  "pedagogical_strengths": [
    "Specific strength of the lesson flow, engagement, or scaffolding"
  ],
  "dual_mode_suitability": {{
    "self_learning_rating": "Excellent / Good / Needs Guidance",
    "instructor_led_rating": "Excellent / Good / Needs Guidance",
    "notes": "Evaluation of clarity for independent learners vs classroom facilitation"
  }},
  "final_summary": "Comprehensive assessment of the lesson's instructional effectiveness and readiness."
}}
"""

