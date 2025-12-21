"""
Utility functions for the AnkiPH addon
Version: 1.0.1 - Fixed escaping for Anki search queries
"""


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