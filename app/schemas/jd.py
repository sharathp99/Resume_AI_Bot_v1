from __future__ import annotations

from pydantic import BaseModel, Field


class JobDescriptionParseRequest(BaseModel):
    role_bucket: str
    jd_text: str


class JobDescriptionStructured(BaseModel):
    role_title: str | None = None
    must_have_skills: list[str] = Field(default_factory=list)
    nice_to_have_skills: list[str] = Field(default_factory=list)
    years_required: float | None = None
    domain_experience: list[str] = Field(default_factory=list)
    tools_platforms: list[str] = Field(default_factory=list)
    education_or_certs: list[str] = Field(default_factory=list)
    location: str | None = None
    work_authorization_constraints: str | None = None
    summary: str | None = None
