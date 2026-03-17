"""PII scrubbing — removes Israeli IDs, phone numbers, and emails.

Extracted from the old ``agent/history.py`` so every service can reuse it.
"""

import re
import logging

logger = logging.getLogger(__name__)

_PII_PATTERNS: list[tuple[re.Pattern, str]] = [
    # Israeli ID number (9 digits)
    (re.compile(r"\b\d{9}\b"), "[ת.ז. הוסר]"),
    # Israeli landline or mobile (0X-XXXXXXX)
    (re.compile(r"\b0[2-9]\d?-?\d{7}\b"), "[טלפון הוסר]"),
    # International format (+972-X-XXXXXXX)
    (re.compile(r"\+972-?\d{1,2}-?\d{7}\b"), "[טלפון הוסר]"),
    # Generic 10-digit phone
    (re.compile(r"\b\d{3}-?\d{7}\b"), "[טלפון הוסר]"),
    # Email address
    (re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"), "[אימייל הוסר]"),
]


def remove_pii(text: str) -> str:
    """Scrub known PII patterns from *text* and return the cleaned string."""
    for pattern, replacement in _PII_PATTERNS:
        if pattern.search(text):
            logger.info("PII scrubbed: %s", replacement)
            text = pattern.sub(replacement, text)
    return text
