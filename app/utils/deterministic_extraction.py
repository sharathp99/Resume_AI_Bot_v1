from __future__ import annotations

import re
from typing import Any

from app.utils.text import normalize_whitespace

EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
PHONE_RE = re.compile(r"(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}")
LINKEDIN_RE = re.compile(r"https?://(?:www\.)?linkedin\.com/in/[\w\-/%]+", re.IGNORECASE)
GITHUB_RE = re.compile(r"https?://(?:www\.)?github\.com/[\w\-]+", re.IGNORECASE)


def extract_contacts(text: str) -> dict[str, Any]:
    normalized = normalize_whitespace(text)
    emails = EMAIL_RE.findall(normalized)
    phones = PHONE_RE.findall(normalized)
    linkedin = LINKEDIN_RE.findall(normalized)
    github = GITHUB_RE.findall(normalized)
    return {
        "email": emails[0].lower() if emails else None,
        "phone": phones[0] if phones else None,
        "linkedin_url": linkedin[0] if linkedin else None,
        "github_url": github[0] if github else None,
    }
