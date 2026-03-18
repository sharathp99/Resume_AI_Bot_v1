from __future__ import annotations

from sqlalchemy import Boolean, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base, TimestampMixin


class Candidate(Base, TimestampMixin):
    __tablename__ = "candidates"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    role_bucket: Mapped[str] = mapped_column(String(128), index=True)
    full_name: Mapped[str | None] = mapped_column(String(255), index=True)
    current_title: Mapped[str | None] = mapped_column(String(255))
    years_experience: Mapped[float | None] = mapped_column(Float)
    summary: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(String(255))
    linkedin_url: Mapped[str | None] = mapped_column(String(500))
    github_url: Mapped[str | None] = mapped_column(String(500))
    work_authorization: Mapped[str | None] = mapped_column(String(255))
    extraction_confidence: Mapped[float | None] = mapped_column(Float)
    raw_text: Mapped[str] = mapped_column(Text)
    source_file: Mapped[str] = mapped_column(String(500), unique=True)
    content_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    extraction_status: Mapped[str] = mapped_column(String(50), default="completed")
    extraction_error: Mapped[str | None] = mapped_column(Text)

    contact: Mapped["CandidateContact"] = relationship(back_populates="candidate", uselist=False, cascade="all, delete-orphan")
    skills: Mapped[list["CandidateSkill"]] = relationship(back_populates="candidate", cascade="all, delete-orphan")
    education: Mapped[list["CandidateEducation"]] = relationship(back_populates="candidate", cascade="all, delete-orphan")
    experiences: Mapped[list["CandidateExperience"]] = relationship(back_populates="candidate", cascade="all, delete-orphan")
    certifications: Mapped[list["CandidateCertification"]] = relationship(back_populates="candidate", cascade="all, delete-orphan")
    statuses: Mapped[list["CandidateStatus"]] = relationship(back_populates="candidate", cascade="all, delete-orphan")
    notes: Mapped[list["RecruiterNote"]] = relationship(back_populates="candidate", cascade="all, delete-orphan")
    documents: Mapped[list["ResumeDocument"]] = relationship(back_populates="candidate", cascade="all, delete-orphan")


class CandidateContact(Base, TimestampMixin):
    __tablename__ = "candidate_contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    candidate_id: Mapped[str] = mapped_column(ForeignKey("candidates.id"), unique=True)
    email: Mapped[str | None] = mapped_column(String(255), index=True)
    phone: Mapped[str | None] = mapped_column(String(64))
    address: Mapped[str | None] = mapped_column(String(255))

    candidate: Mapped[Candidate] = relationship(back_populates="contact")


class CandidateSkill(Base, TimestampMixin):
    __tablename__ = "candidate_skills"
    __table_args__ = (UniqueConstraint("candidate_id", "skill", name="uq_candidate_skill"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    candidate_id: Mapped[str] = mapped_column(ForeignKey("candidates.id"), index=True)
    skill: Mapped[str] = mapped_column(String(128), index=True)
    category: Mapped[str | None] = mapped_column(String(128))

    candidate: Mapped[Candidate] = relationship(back_populates="skills")


class CandidateEducation(Base, TimestampMixin):
    __tablename__ = "candidate_education"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    candidate_id: Mapped[str] = mapped_column(ForeignKey("candidates.id"), index=True)
    institution: Mapped[str | None] = mapped_column(String(255))
    degree: Mapped[str | None] = mapped_column(String(255))
    field_of_study: Mapped[str | None] = mapped_column(String(255))
    start_year: Mapped[int | None] = mapped_column(Integer)
    end_year: Mapped[int | None] = mapped_column(Integer)

    candidate: Mapped[Candidate] = relationship(back_populates="education")


class CandidateExperience(Base, TimestampMixin):
    __tablename__ = "candidate_experience"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    candidate_id: Mapped[str] = mapped_column(ForeignKey("candidates.id"), index=True)
    company: Mapped[str | None] = mapped_column(String(255))
    title: Mapped[str | None] = mapped_column(String(255))
    start_date: Mapped[str | None] = mapped_column(String(64))
    end_date: Mapped[str | None] = mapped_column(String(64))
    description: Mapped[str | None] = mapped_column(Text)

    candidate: Mapped[Candidate] = relationship(back_populates="experiences")


class CandidateCertification(Base, TimestampMixin):
    __tablename__ = "candidate_certifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    candidate_id: Mapped[str] = mapped_column(ForeignKey("candidates.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    issuer: Mapped[str | None] = mapped_column(String(255))

    candidate: Mapped[Candidate] = relationship(back_populates="certifications")


class ResumeDocument(Base, TimestampMixin):
    __tablename__ = "resume_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    candidate_id: Mapped[str] = mapped_column(ForeignKey("candidates.id"), index=True)
    role_bucket: Mapped[str] = mapped_column(String(128), index=True)
    source_file: Mapped[str] = mapped_column(String(500))
    document_type: Mapped[str] = mapped_column(String(50))
    raw_text: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)

    candidate: Mapped[Candidate] = relationship(back_populates="documents")


class JobDescription(Base, TimestampMixin):
    __tablename__ = "job_descriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    role_bucket: Mapped[str] = mapped_column(String(128), index=True)
    title: Mapped[str | None] = mapped_column(String(255))
    raw_text: Mapped[str] = mapped_column(Text)
    structured_json: Mapped[dict] = mapped_column(JSON, default=dict)


class RecruiterNote(Base, TimestampMixin):
    __tablename__ = "recruiter_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    candidate_id: Mapped[str] = mapped_column(ForeignKey("candidates.id"), index=True)
    note_text: Mapped[str] = mapped_column(Text)
    created_by: Mapped[str | None] = mapped_column(String(255))

    candidate: Mapped[Candidate] = relationship(back_populates="notes")


class CandidateStatus(Base, TimestampMixin):
    __tablename__ = "candidate_statuses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    candidate_id: Mapped[str] = mapped_column(ForeignKey("candidates.id"), index=True)
    status: Mapped[str] = mapped_column(String(64), index=True)
    shortlisted: Mapped[bool] = mapped_column(Boolean, default=False)
    contacted: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)

    candidate: Mapped[Candidate] = relationship(back_populates="statuses")


class QueryHistory(Base, TimestampMixin):
    __tablename__ = "query_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    query_text: Mapped[str] = mapped_column(Text)
    role_bucket: Mapped[str | None] = mapped_column(String(128), index=True)
    query_type: Mapped[str] = mapped_column(String(64), index=True)
    returned_candidate_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    session_id: Mapped[str | None] = mapped_column(String(128), index=True)


class IndexingJob(Base, TimestampMixin):
    __tablename__ = "indexing_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    role_bucket: Mapped[str] = mapped_column(String(128), index=True)
    source_file: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(64), index=True)
    error_message: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
