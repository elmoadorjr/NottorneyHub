"""
Utility functions for the AnkiPH addon
Version: 1.0.1 - Fixed escaping for Anki search queries
"""
import re


def escape_anki_search(text: str) -> str:
    """
    Escape special characters for Anki search queries.
    
    Parentheses and other special characters in deck names or search terms
    will break Anki's search syntax if not properly escaped.
    
    Args:
        text: The text to escape (deck name, guid, etc.)
    
    Returns:
        Escaped text safe for use in Anki search queries
    """
    if not text:
        return text
    
    # Escape parentheses with backslash for Anki search
    text = text.replace("(", r"\(")
    text = text.replace(")", r"\)")
    
    # Escape double quotes
    text = text.replace('"', r'\"')
    
    # Escape asterisks (wildcard in Anki search)
    text = text.replace("*", r"\*")
    
    # Note: We don't escape colons as they're needed for subdeck paths
    # and search operators like "deck:"
    
    return text


def validate_card_id(cid: int) -> bool:
    """
    Validate that card ID is a positive 64-bit integer.
    Prevents overflow/underflow logical issues in Anki 2.1+.
    """
    if not isinstance(cid, int):
        return False
    # Max signed 64-bit integer: 9,223,372,036,854,775,807
    # Anki uses signed 64-bit int for IDs (milliseconds since epoch)
    return 0 < cid <= 9223372036854775807


def sanitize_sql_like(text: str) -> str:
    """
    Escape special characters for SQL LIKE queries.
    Used when searching with wildcards in SQLite.
    
    Args:
        text: The text to escape
    
    Returns:
        Escaped text safe for use in SQL LIKE clauses
    """
    if not text:
        return text
    
    # Escape SQL LIKE wildcards
    text = text.replace("%", r"\%")
    text = text.replace("_", r"\_")
    
    return text



# Pre-compiled regex for HTML tag stripping
HTML_TAG_PATTERN = re.compile(r'<[^>]+>')


def strip_html(text: str) -> str:
    """
    Efficiently strip HTML tags from text using pre-compiled regex.
    
    Args:
        text: The text containing HTML tags
    
    Returns:
        Clean text without HTML tags
    """
    if not text:
        return ""
    return HTML_TAG_PATTERN.sub('', text)


class ErrorHandler:
    """
    Unified error handler for AnkiPH.
    Separates logging from UI feedback.
    """
    
    @staticmethod
    def handle(e: Exception, context: str, silent: bool = False) -> None:
        """
        Handle an exception efficiently.
        
        Args:
            e: The exception object
            context: Description of where the error occurred
            silent: If True, log only (no UI)
        """
        from .logger import logger
        
        # Log purely
        logger.exception(f"Error in {context}: {str(e)}")
        
        # UI Feedback (if available and not silent)
        if not silent:
            try:
                from aqt import mw
                from aqt.utils import showWarning
                if mw:
                    showWarning(f"An error occurred in {context}:\n{str(e)}")
            except ImportError:
                pass  # Headless or running outside Anki