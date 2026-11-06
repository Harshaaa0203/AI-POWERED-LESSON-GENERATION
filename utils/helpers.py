"""
Utility helper functions for JSON parsing, string manipulation, and UI formatting.
"""

import json
import re
import urllib.parse
from typing import Any, Dict, Optional


def parse_json_robust(text: str) -> Dict[str, Any]:
    """
    Robustly extract and parse JSON from LLM outputs, stripping Markdown fences,
    handling common formatting quirks, and repairing minor syntax errors.
    """
    if not text or not isinstance(text, str):
        return {}

    cleaned = text.strip()

    # Extract JSON between ```json ... ``` or ``` ... ```
    code_block_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned, re.IGNORECASE)
    if code_block_match:
        cleaned = code_block_match.group(1).strip()

    # If still not starting with { or [, look for outer curly braces
    if not (cleaned.startswith("{") or cleaned.startswith("[")):
        brace_match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", cleaned)
        if brace_match:
            cleaned = brace_match.group(1).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Repair trailing commas before closing braces/brackets
        repaired = re.sub(r",\s*([\]}])", r"\1", cleaned)
        # Replace single quotes around keys if any
        repaired = re.sub(r"(?<=\{|\,)\s*'([^']+)'\s*:", r' "\1":', repaired)
        try:
            return json.loads(repaired)
        except json.JSONDecodeError as e:
            # Fallback: log error and return empty or partial
            return {"error": f"JSON parse error: {str(e)}", "raw_content": cleaned}


def extract_domain(url: str) -> str:
    """Extract clean domain name from URL."""
    try:
        parsed = urllib.parse.urlparse(url)
        netloc = parsed.netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc
    except Exception:
        return url


def get_score_color(score: float) -> str:
    """Return hex color code based on QC score."""
    if score >= 85:
        return "#10b981"  # Emerald / Green
    elif score >= 70:
        return "#f59e0b"  # Amber / Yellow
    else:
        return "#ef4444"  # Rose / Red


def get_severity_color(severity: str) -> str:
    """Return styling color for severity tag."""
    sev = (severity or "").lower()
    if sev == "critical":
        return "#dc2626"
    elif sev == "high":
        return "#ea580c"
    elif sev == "medium":
        return "#d97706"
    elif sev == "low":
        return "#2563eb"
    return "#64748b"


def format_duration(minutes: Any) -> str:
    """Format minutes into readable badge."""
    try:
        m = int(minutes)
        return f"{m} mins" if m != 1 else "1 min"
    except Exception:
        return f"{minutes}"

