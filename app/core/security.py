from __future__ import annotations

import re


EMAIL_PATTERN = re.compile(r"([\w.+'%-]+)@([\w.-]+\.[A-Za-z]{2,})")
PHONE_PATTERN = re.compile(r"(\+?\d[\d\s().-]{7,}\d)")


def mask_sensitive_value(text: str | None) -> str | None:
    """Mask email and phone values before logging."""

    if text is None:
        return None
    masked = EMAIL_PATTERN.sub(lambda match: f"***@{match.group(2)}", text)
    masked = PHONE_PATTERN.sub("***PHONE***", masked)
    return masked
