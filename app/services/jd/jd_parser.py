from __future__ import annotations

import re

from app.integrations.openai.client import OpenAIProvider
from app.schemas.jd import JobDescriptionStructured
from app.services.extraction.resume_extractor import ResumeExtractor
from app.utils.text import normalize_whitespace


class JobDescriptionParser:
    """Parses recruiter JD text into a structured object."""

    def __init__(self, openai_provider: OpenAIProvider | None = None) -> None:
        self.openai_provider = openai_provider or OpenAIProvider()
        self.skill_catalog = ResumeExtractor.COMMON_SKILLS

    def parse(self, jd_text: str) -> JobDescriptionStructured:
        if not jd_text.strip():
            raise ValueError("Job description text cannot be empty.")
        heuristic = self._heuristic_parse(jd_text)
        if self.openai_provider.enabled:
            try:
                system_prompt = (
                    "Extract a recruiter job description into JSON with keys role_title, must_have_skills,"
                    " nice_to_have_skills, years_required, domain_experience, tools_platforms,"
                    " education_or_certs, location, work_authorization_constraints, summary."
                )
                llm_payload = self.openai_provider.chat_json(system_prompt, jd_text[:10000])
                heuristic.update({k: v for k, v in llm_payload.items() if v not in (None, [], "")})
            except Exception:
                pass
        return JobDescriptionStructured.model_validate(heuristic)

    def _heuristic_parse(self, jd_text: str) -> dict:
        normalized = normalize_whitespace(jd_text).lower()
        must_have = [skill.title() for skill in self.skill_catalog if skill in normalized]
        years = re.search(r"(\d{1,2})\+?\s+years?", jd_text, re.IGNORECASE)
        title = next((line.strip() for line in jd_text.splitlines() if line.strip()), None)
        nice_to_have = []
        if "nice to have" in normalized or "preferred" in normalized:
            nice_to_have = must_have[:2]
        location = None
        location_match = re.search(r"location[:\s]+([A-Za-z ,]+)", jd_text, re.IGNORECASE)
        if location_match:
            location = location_match.group(1).strip()
        return {
            "role_title": title,
            "must_have_skills": must_have,
            "nice_to_have_skills": nice_to_have,
            "years_required": float(years.group(1)) if years else None,
            "domain_experience": ["Data", "Analytics"] if any(token in normalized for token in ["data", "analytics"]) else [],
            "tools_platforms": must_have,
            "education_or_certs": ["Bachelor's"] if "bachelor" in normalized else [],
            "location": location,
            "work_authorization_constraints": "Required" if "authorization" in normalized or "visa" in normalized else None,
            "summary": jd_text[:400],
        }
