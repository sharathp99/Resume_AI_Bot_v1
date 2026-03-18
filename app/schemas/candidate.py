from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.common import ORMBaseModel, TimestampedModel


class CandidateContactSchema(ORMBaseModel):
    email: EmailStr | None = None
    phone: str | None = None
    address: str | None = None


class CandidateSkillSchema(ORMBaseModel):
    skill: str
    category: str | None = None


class CandidateEducationSchema(ORMBaseModel):
    institution: str | None = None
    degree: str | None = None
    field_of_study: str | None = None
    start_year: int | None = None
    end_year: int | None = None


class CandidateExperienceSchema(ORMBaseModel):
    company: str | None = None
    title: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    description: str | None = None


class CandidateCertificationSchema(ORMBaseModel):
    name: str
    issuer: str | None = None


class RecruiterNoteSchema(TimestampedModel):
    id: int | None = None
    note_text: str
    created_by: str | None = None


class CandidateStatusSchema(TimestampedModel):
    id: int | None = None
    status: str
    shortlisted: bool = False
    contacted: bool = False
    metadata_json: dict = Field(default_factory=dict)


class CandidateProfileSchema(TimestampedModel):
    id: str
    role_bucket: str
    full_name: str | None = None
    current_title: str | None = None
    years_experience: float | None = None
    summary: str | None = None
    location: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    work_authorization: str | None = None
    extraction_confidence: float | None = None
    raw_text: str
    source_file: str
    extraction_status: str
    extraction_error: str | None = None
    contact: CandidateContactSchema | None = None
    skills: list[CandidateSkillSchema] = Field(default_factory=list)
    education: list[CandidateEducationSchema] = Field(default_factory=list)
    experiences: list[CandidateExperienceSchema] = Field(default_factory=list)
    certifications: list[CandidateCertificationSchema] = Field(default_factory=list)
    statuses: list[CandidateStatusSchema] = Field(default_factory=list)
    notes: list[RecruiterNoteSchema] = Field(default_factory=list)


class CandidateStructuredExtraction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    address: str | None = None
    location: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    work_authorization: str | None = None
    years_experience: float | None = None
    current_title: str | None = None
    skills: list[str] = Field(default_factory=list)
    education: list[CandidateEducationSchema] = Field(default_factory=list)
    certifications: list[CandidateCertificationSchema] = Field(default_factory=list)
    experience_history: list[CandidateExperienceSchema] = Field(default_factory=list)
    summary: str | None = None
    extraction_confidence: float | None = None


class CandidateSearchResult(BaseModel):
    candidate_id: str
    full_name: str | None = None
    score: float
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    top_skills: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    evidence_snippets: list[str] = Field(default_factory=list)
    explanation: str


class CandidateComparisonResult(BaseModel):
    jd_title: str | None = None
    candidates: list[CandidateSearchResult]
    recommendation: str


class NoteCreateRequest(BaseModel):
    candidate_id: str
    note_text: str
    created_by: str | None = None


class StatusUpdateRequest(BaseModel):
    candidate_id: str
    status: Literal[
        "new",
        "shortlisted",
        "contacted",
        "submitted",
        "interviewing",
        "rejected",
        "on_hold",
    ]
    shortlisted: bool = False
    contacted: bool = False
    metadata_json: dict = Field(default_factory=dict)
