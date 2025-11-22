"""Author name parsing and normalization utilities."""

import re
from typing import List, Set


def parse_author_string(author_string: str) -> List[str]:
    """
    Parse author string into individual normalized author names.

    Handles various formats:
    - "Smith, J., Jones, A., Lee, B."
    - "John Smith, Alice Jones, Bob Lee"
    - "J. Smith, A. Jones, B. Lee"
    - "Smith J, Jones A"

    Returns normalized format: "Last, F." or "Last, F. M."

    Args:
        author_string: Raw author string from source

    Returns:
        List of normalized author names

    Examples:
        >>> parse_author_string("Smith, J., Jones, A.")
        ['Smith, J.', 'Jones, A.']
        >>> parse_author_string("John Smith, Alice Jones")
        ['Smith, J.', 'Jones, A.']
    """
    if not author_string or not isinstance(author_string, str):
        return []

    # Split on various delimiters
    # Common patterns: ", " or " and " or ";" or " & "
    author_string = author_string.replace(' and ', ', ')
    author_string = author_string.replace(' & ', ', ')
    author_string = author_string.replace(';', ',')

    # Split into potential author names
    parts = [p.strip() for p in author_string.split(',') if p.strip()]

    authors = []
    i = 0
    while i < len(parts):
        part = parts[i]

        # Check if this looks like "Last" followed by "First" pattern
        # e.g., ["Smith", "J."] from "Smith, J., Jones, A."
        if i + 1 < len(parts) and _is_likely_initials(parts[i + 1]):
            # "Smith, J." pattern
            last_name = part
            initials = parts[i + 1]
            authors.append(_normalize_name(last_name, initials))
            i += 2
        elif _is_likely_initials(part):
            # Standalone initials (malformed, skip)
            i += 1
        else:
            # Try to parse as "First Last" or "F. Last"
            parsed = _parse_single_name(part)
            if parsed:
                authors.append(parsed)
            i += 1

    # Deduplicate while preserving order
    seen: Set[str] = set()
    unique_authors = []
    for author in authors:
        if author not in seen:
            seen.add(author)
            unique_authors.append(author)

    return unique_authors


def _is_likely_initials(s: str) -> bool:
    """Check if string looks like initials (e.g., 'J.', 'J. M.', 'JM')."""
    # Remove spaces and periods
    cleaned = s.replace('.', '').replace(' ', '')
    # Initials are typically 1-4 uppercase letters
    return len(cleaned) <= 4 and cleaned.isupper() and cleaned.isalpha()


def _parse_single_name(name: str) -> str:
    """
    Parse a single name like 'John Smith' or 'J. Smith' into 'Smith, J.'

    Args:
        name: Single author name

    Returns:
        Normalized "Last, F." format or empty string if can't parse
    """
    name = name.strip()
    if not name:
        return ""

    # Split on whitespace
    parts = name.split()

    if len(parts) == 1:
        # Single word, assume it's a last name (e.g., "Anthropic")
        return parts[0]

    # Check if last part looks like a last name (starts with capital)
    if parts[-1][0].isupper():
        last_name = parts[-1]
        # Take first parts as first name/initials
        first_parts = parts[:-1]
        initials = _extract_initials(' '.join(first_parts))
        return _normalize_name(last_name, initials)

    # Couldn't parse, return as-is
    return name


def _extract_initials(first_name: str) -> str:
    """
    Extract initials from first name(s).

    Examples:
        'John' -> 'J.'
        'John Michael' -> 'J. M.'
        'J.' -> 'J.'
        'J. M.' -> 'J. M.'
    """
    # If already in initial format, return as-is
    if re.match(r'^[A-Z]\.(\s*[A-Z]\.)*$', first_name):
        return first_name

    # Extract capital letters
    parts = first_name.split()
    initials = []
    for part in parts:
        if part:
            # Get first character if it's a letter
            first_char = part[0]
            if first_char.isalpha():
                initials.append(first_char.upper() + '.')

    return ' '.join(initials)


def _normalize_name(last_name: str, initials: str) -> str:
    """
    Normalize to 'Last, F.' or 'Last, F. M.' format.

    Args:
        last_name: Last name
        initials: Initials (may or may not have periods)

    Returns:
        Normalized name
    """
    # Clean up last name
    last_name = last_name.strip()

    # Clean up initials - ensure they have periods
    if initials:
        # Remove existing periods and spaces
        initials_clean = initials.replace('.', '').replace(' ', '')
        # Add periods back
        initials_formatted = '. '.join(list(initials_clean)) + '.'
        return f"{last_name}, {initials_formatted}"
    else:
        return last_name


def get_primary_author(author_string: str) -> str:
    """
    Get the primary (first) author from an author string.

    First authors are often more distinctive and important for tracking.

    Args:
        author_string: Raw author string

    Returns:
        Primary author name in normalized format
    """
    authors = parse_author_string(author_string)
    return authors[0] if authors else ""


def normalize_author_name(author_name: str) -> str:
    """
    Normalize a single author name for consistent storage/lookup.

    Args:
        author_name: Author name in any format

    Returns:
        Normalized author name
    """
    # Try to parse as a full author string
    authors = parse_author_string(author_name)
    return authors[0] if authors else author_name.strip()
