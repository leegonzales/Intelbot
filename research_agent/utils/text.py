"""Text processing utilities."""

import re
from typing import List


def normalize_text(text: str) -> str:
    """
    Normalize text for comparison.

    Args:
        text: Input text

    Returns:
        Normalized text
    """
    # Convert to lowercase
    text = text.lower()

    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)

    # Strip leading/trailing whitespace
    text = text.strip()

    return text


def extract_snippet(text: str, max_length: int = 500) -> str:
    """
    Extract snippet from text.

    Args:
        text: Full text
        max_length: Maximum snippet length

    Returns:
        Snippet (first max_length chars)
    """
    if len(text) <= max_length:
        return text

    # Try to break at sentence boundary
    snippet = text[:max_length]
    last_period = snippet.rfind('.')
    last_newline = snippet.rfind('\n')

    break_point = max(last_period, last_newline)

    if break_point > max_length * 0.7:  # Only break if reasonably close to max
        return snippet[:break_point + 1].strip()

    return snippet + "..."


def extract_keywords(text: str, min_length: int = 4) -> List[str]:
    """
    Extract keywords from text.

    Args:
        text: Input text
        min_length: Minimum keyword length

    Returns:
        List of keywords
    """
    # Simple keyword extraction: words longer than min_length, alphanumeric only
    words = re.findall(r'\b[a-zA-Z0-9]+\b', text.lower())
    keywords = [w for w in words if len(w) >= min_length]

    # Remove duplicates while preserving order
    seen = set()
    unique_keywords = []
    for k in keywords:
        if k not in seen:
            seen.add(k)
            unique_keywords.append(k)

    return unique_keywords


def clean_html(html: str) -> str:
    """
    Remove HTML tags and decode entities.

    Args:
        html: HTML string

    Returns:
        Plain text
    """
    from html import unescape

    # Remove script and style elements
    text = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', html, flags=re.DOTALL)

    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # Decode HTML entities
    text = unescape(text)

    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to max length.

    Args:
        text: Input text
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix
