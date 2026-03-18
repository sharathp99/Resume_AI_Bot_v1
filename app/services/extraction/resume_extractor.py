from __future__ import annotations

import re
from typing import Any

from app.core.exceptions import ExtractionError
from app.integrations.openai.client import OpenAIProvider
from app.schemas.candidate import CandidateStructuredExtraction
from app.utils.deterministic_extraction import extract_contacts
from app.utils.text import normalize_whitespace


class ResumeExtractor:
    """Hybrid deterministic + LLM-based resume extractor."""

    COMMON_SKILLS = {
        "python",
        "sql",
        "aws",
        "spark",
        "airflow",
        "dbt",
        "snowflake",
        "pandas",
        "tensorflow",
        "pytorch",
        "machine learning",
        "data engineering",
        "etl",
        "tableau",
        "power bi",
        "java",
        "scala",
    }

    def __init__(self, openai_provider: OpenAIProvider | None = None) -> None:
        self.openai_provider = openai_provider or OpenAIProvider()

    def extract(self, raw_text: str) -> CandidateStructuredExtraction:
        deterministic = extract_contacts(raw_text)
        heuristic = self._heuristic_extract(raw_text)
        payload: dict[str, Any] = {**heuristic, **{k: v for k, v in deterministic.items() if v}}
        if self.openai_provider.enabled:
            try:
                llm_payload = self._llm_extract(raw_text)
                payload.update({key: value for key, value in llm_payload.items() if value not in (None, [], "")})
            except Exception as exc:
                payload.setdefault("summary", heuristic.get("summary"))
                payload.setdefault("extraction_confidence", 0.55)
                payload["summary"] = payload.get("summary") or "LLM extraction unavailable; heuristics used."
        try:
            payload["skills"] = sorted({skill.strip() for skill in payload.get("skills", []) if skill.strip()})
            return CandidateStructuredExtraction.model_validate(payload)
        except Exception as exc:
            raise ExtractionError(f"Failed to validate extracted resume data: {exc}") from exc

    def _heuristic_extract(self, raw_text: str) -> dict[str, Any]:
        normalized = normalize_whitespace(raw_text)
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        full_name = lines[0][:120] if lines else None
        summary = " ".join(lines[:3])[:500] if lines else None
        current_title = None
        for line in lines[:10]:
            if any(token in line.lower() for token in ["engineer", "scientist", "analyst", "manager"]):
                current_title = line
                break
        location_match = re.search(r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]{2})", raw_text)
        years_match = re.search(r"(\d{1,2})\+?\s+years? of experience", raw_text, re.IGNORECASE)
        skills = [skill.title() for skill in self.COMMON_SKILLS if skill in normalized.lower()]
        return {
            "full_name": full_name,
            "location": location_match.group(1) if location_match else None,
            "years_experience": float(years_match.group(1)) if years_match else None,
            "current_title": current_title,
            "skills": skills,
            "summary": summary,
            "education": [],
            "certifications": [],
            "experience_history": [],
            "extraction_confidence": 0.65,
        }

    def _llm_extract(self, raw_text: str) -> dict[str, Any]:
        system_prompt = (
            "You extract resume information into JSON. Do not invent values. Return JSON keys that match the"
            " schema: full_name, email, phone, address, location, linkedin_url, github_url, work_authorization,"
            " years_experience, current_title, skills, education, certifications, experience_history, summary,"
            " extraction_confidence."
        )
        user_prompt = f"Resume text:\n{raw_text[:12000]}"
        return self.openai_provider.chat_json(system_prompt=system_prompt, user_prompt=user_prompt)
