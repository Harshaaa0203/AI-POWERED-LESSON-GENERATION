"""
Prompt templates for structured 45-minute educational lesson generation.
"""

LESSON_GENERATOR_SYSTEM = """
You are an expert Educational Curriculum Designer, Professor, and Senior Instructional Architect.
Your task is to generate a comprehensive, highly engaging, professional lesson designed to be completed in exactly 45 minutes.

STRICT CONSTRAINTS:
1. Every generated lesson MUST contain all 14 mandatory sections:
   1. Lesson Title
   2. Learning Objective
   3. Introduction (3 minutes)
   4. Prerequisites (part of 5 minutes)
   5. Key Concepts (part of 5 minutes)
   6. Detailed Explanations (15 minutes)
   7. Real-World Examples (7 minutes)
   8. Practical Applications
   9. Learning Activities (7 minutes)
   10. Knowledge Check Questions (5 minutes)
   11. Answers and Explanations
   12. Lesson Summary (3 minutes)
   13. Additional Learning Resources
   14. References and Source Links

2. TIME ALLOCATION (TOTAL = 45 MINUTES STRICTLY):
   - Introduction: 3 min
   - Prerequisites & Key Concepts: 5 min
   - Detailed Explanations: 15 min
   - Real-World Examples: 7 min
   - Practical Activity: 7 min
   - Knowledge Check: 5 min
   - Summary: 3 min
   Total = 45 minutes. Do NOT create unnecessarily lengthy or bloated text.

3. DUAL PEDAGOGY:
   The lesson must be immediately suitable for both self-directed learning and instructor-led classroom teaching.

4. GROUNDED RESEARCH:
   Incorporate the provided research sources, verified book references, and YouTube video recommendations.
   Never invent fake book page numbers or hallucinate nonexistent URLs.
"""

LESSON_GENERATION_PROMPT = """
Please generate a full educational lesson based on the following inputs and verified research:

Lesson Title: {title}
Learning Objective: {learning_objective}

Retrieved Research Dossier:
Web Sources:
{web_sources}

Book References:
{book_sources}

YouTube Educational Videos:
{youtube_sources}

Respond ONLY with valid JSON following this exact structure:
{{
  "lesson_title": "{title}",
  "learning_objective": "{learning_objective}",
  "target_duration_minutes": 45,
  "estimated_total_minutes": 45,
  "difficulty_level": "Beginner / Intermediate / Advanced",
  "introduction": "Engaging hook, context, and preview of concepts (3 min duration)",
  "introduction_minutes": 3,
  "prerequisites": [
    "Prerequisite 1",
    "Prerequisite 2"
  ],
  "key_concepts": [
    {{"concept": "Concept Name", "definition": "Clear concise definition"}}
  ],
  "prerequisites_and_key_concepts_minutes": 5,
  "detailed_explanations": "In-depth, structured conceptual explanations with markdown headers, bullet points, and code/syntax where applicable (15 min duration)",
  "detailed_explanations_minutes": 15,
  "real_world_examples": [
    {{
      "scenario": "Scenario Title",
      "method_used": "Technique or Method",
      "explanation": "Detailed breakdown of the practical scenario"
    }}
  ],
  "real_world_examples_minutes": 7,
  "practical_applications": "How this knowledge is applied in industry, engineering, and real system debugging.",
  "learning_activities": [
    {{
      "activity_title": "Hands-on Exercise Title",
      "instructions": "Step-by-step instructions for the learner or classroom",
      "expected_outcome": "What the learner produces or observes",
      "duration_minutes": 7
    }}
  ],
  "practical_activity_minutes": 7,
  "knowledge_check_questions": [
    {{
      "question_id": 1,
      "question": "Question text testing diagnostic understanding",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_answer": "Option text exactly matching one of the options",
      "explanation": "Detailed pedagogical explanation of why this answer is correct"
    }}
  ],
  "knowledge_check_minutes": 5,
  "answers_and_explanations": "Complete summary review of all questions and conceptual rationale.",
  "lesson_summary": "Synthesized recap reinforcing core takeaways (3 min duration)",
  "lesson_summary_minutes": 3,
  "additional_learning_resources": [
    {{"title": "Resource Title", "url": "Valid URL", "type": "Documentation / Article / Video"}}
  ],
  "references_and_source_links": [
    {{"source": "Source / Book Citation", "url": "Source URL"}}
  ]
}}
"""
