"""
Validation functions for lesson inputs, URLs, content structures, and QC reports.
"""

import re
import urllib.parse
from typing import Tuple, List, Dict, Any, Optional
import requests


MANDATORY_LESSON_SECTIONS = [
    "lesson_title",
    "learning_objective",
    "introduction",
    "prerequisites",
    "key_concepts",
    "detailed_explanations",
    "real_world_examples",
    "practical_applications",
    "learning_activities",
    "knowledge_check_questions",
    "answers_and_explanations",
    "lesson_summary",
    "additional_learning_resources",
    "references_and_source_links",
]

TARGET_SECTION_MINUTES = {
    "introduction": 3,
    "prerequisites_and_key_concepts": 5,
    "detailed_explanations": 15,
    "real_world_examples": 7,
    "learning_activities": 7,
    "knowledge_check_questions": 5,
    "lesson_summary": 3,
}
MAX_TOTAL_MINUTES = 45


def validate_lesson_inputs(title: Optional[str], learning_objective: Optional[str]) -> Tuple[bool, str]:
    """
    Validate lesson title and learning objective.
    Returns (is_valid, error_message).
    """
    if not title or not title.strip():
        return False, "Lesson Title cannot be empty."

    if not learning_objective or not learning_objective.strip():
        return False, "Learning Objective cannot be empty."

    clean_title = title.strip()
    clean_obj = learning_objective.strip()

    if len(clean_title) < 3:
        return False, "Lesson Title must be at least 3 characters long."

    if len(clean_title) > 200:
        return False, "Lesson Title cannot exceed 200 characters."

    if len(clean_obj) < 10:
        return False, "Learning Objective must be at least 10 characters long to provide sufficient context."

    if len(clean_obj) > 1000:
        return False, "Learning Objective cannot exceed 1000 characters."

    return True, ""


def validate_url(url: str, check_reachable: bool = False, timeout: int = 4) -> bool:
    """
    Check if a URL is syntactically valid, and optionally whether it is reachable.
    """
    if not url or not isinstance(url, str):
        return False

    url = url.strip()
    try:
        parsed = urllib.parse.urlparse(url)
        if not (parsed.scheme in ("http", "https") and parsed.netloc):
            return False

        if check_reachable:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            try:
                res = requests.head(url, headers=headers, timeout=timeout, allow_redirects=True)
                if res.status_code < 400:
                    return True
                res = requests.get(url, headers=headers, timeout=timeout, stream=True)
                return res.status_code < 400
            except Exception:
                return False

        return True
    except Exception:
        return False


def validate_lesson_structure(lesson_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Verify that a generated lesson satisfies all 14 mandatory sections and constraints.
    Returns (is_valid, list_of_missing_or_invalid_sections).
    """
    issues = []
    if not isinstance(lesson_data, dict):
        return False, ["Lesson data is not a valid dictionary."]

    for sec in MANDATORY_LESSON_SECTIONS:
        val = lesson_data.get(sec)
        if val is None or (isinstance(val, str) and not val.strip()) or (isinstance(val, list) and len(val) == 0):
            issues.append(f"Missing or empty required section: '{sec}'")

    # Time allocation check
    total_minutes = lesson_data.get("estimated_total_minutes", 0)
    try:
        total_num = float(total_minutes)
        if total_num > MAX_TOTAL_MINUTES:
            issues.append(f"Total lesson duration ({total_num} mins) exceeds maximum allowed {MAX_TOTAL_MINUTES} minutes.")
    except (ValueError, TypeError):
        pass

    return (len(issues) == 0, issues)


def sanitize_text(text: str) -> str:
    """Remove unsafe or excessive characters."""
    if not text:
        return ""
    text = re.sub(r"\r\n|\r", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

