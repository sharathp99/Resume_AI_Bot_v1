from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.candidate import CandidateComparisonResult, CandidateSearchResult


class CandidateSearchRequest(BaseModel):
    role_bucket: str
    jd_text: str
    top_k: int = 5
    session_id: str | None = None


class SkillSearchRequest(BaseModel):
    role_bucket: str
    skills: list[str] = Field(default_factory=list)
    top_k: int = 5
    session_id: str | None = None


class CandidateSearchResponse(BaseModel):
    results: list[CandidateSearchResult]


class ComparisonRequest(BaseModel):
    role_bucket: str
    candidate_ids: list[str]
    jd_text: str


class ComparisonResponse(BaseModel):
    comparison: CandidateComparisonResult
