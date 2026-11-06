"""
Standardized error classes and resilient execution helpers.
"""

import functools
import logging
import time
from typing import Callable, Any, Optional

logger = logging.getLogger("AILessonCreator")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


class LessonCreatorError(Exception):
    """Base exception for AI Lesson Creator."""
    def __init__(self, message: str, user_friendly_message: Optional[str] = None):
        super().__init__(message)
        self.user_friendly_message = user_friendly_message or message


class ValidationError(LessonCreatorError):
    """Input or schema validation failed."""
    pass


class ResearchError(LessonCreatorError):
    """Error occurred during web, book, or video research."""
    pass


class LLMError(LessonCreatorError):
    """Error communicating with or parsing LLM responses."""
    pass


class DatabaseError(LessonCreatorError):
    """Error during database interaction."""
    pass


class ExportError(LessonCreatorError):
    """Error during PDF or Markdown export generation."""
    pass


class QCError(LessonCreatorError):
    """Error during quality control evaluation."""
    pass


def retry_with_backoff(retries: int = 3, backoff_factor: float = 1.5, exceptions=(Exception,)):
    """
    Decorator to retry transient failures with exponential backoff.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_err = None
            delay = 1.0
            for attempt in range(1, retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_err = e
                    logger.warning(
                        f"Attempt {attempt}/{retries} failed for {func.__name__}: {e}. Retrying in {delay:.1f}s..."
                    )
                    if attempt == retries:
                        break
                    time.sleep(delay)
                    delay *= backoff_factor
            logger.error(f"All {retries} attempts failed for {func.__name__}.")
            raise last_err
        return wrapper
    return decorator


def format_error_for_ui(e: Exception) -> str:
    """Format an exception into a clear, helpful message for end users."""
    if isinstance(e, LessonCreatorError) and e.user_friendly_message:
        return e.user_friendly_message
    msg = str(e)
    if "API_KEY" in msg or "401" in msg or "403" in msg:
        return "Authentication error: Please ensure your API key is correctly configured in .env or the Settings panel."
    if "timeout" in msg.lower():
        return "Network timeout: The service took too long to respond. Please check your internet connection and retry."
    if "rate" in msg.lower() or "429" in msg:
        return "Rate limit exceeded: The external API quota was reached. Please wait a moment before retrying."
    return f"Operation encountered an unexpected error: {msg}"
