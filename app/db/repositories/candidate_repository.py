from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.models.entities import Candidate, CandidateStatus, QueryHistory, RecruiterNote


class CandidateRepository:
    """Database access for candidate-centric operations."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert_candidate(self, candidate: Candidate) -> Candidate:
        existing = self.session.get(Candidate, candidate.id)
        if existing:
            self.session.delete(existing)
            self.session.flush()
        self.session.add(candidate)
        self.session.flush()
        return candidate

    def get_candidate(self, candidate_id: str) -> Candidate | None:
        stmt = (
            select(Candidate)
            .options(
                joinedload(Candidate.contact),
                joinedload(Candidate.skills),
                joinedload(Candidate.education),
                joinedload(Candidate.experiences),
                joinedload(Candidate.certifications),
                joinedload(Candidate.statuses),
                joinedload(Candidate.notes),
                joinedload(Candidate.documents),
            )
            .where(Candidate.id == candidate_id)
        )
        return self.session.execute(stmt).unique().scalar_one_or_none()

    def list_candidates(
        self,
        role_bucket: str | None = None,
        status: str | None = None,
        shortlisted: bool | None = None,
        contacted: bool | None = None,
    ) -> list[Candidate]:
        stmt = select(Candidate).options(
            joinedload(Candidate.contact), joinedload(Candidate.skills), joinedload(Candidate.statuses)
        )
        if role_bucket:
            stmt = stmt.where(Candidate.role_bucket == role_bucket)
        candidates = list(self.session.execute(stmt.order_by(Candidate.full_name)).unique().scalars().all())
        filtered: list[Candidate] = []
        for candidate in candidates:
            latest = max(candidate.statuses, key=lambda item: item.created_at or 0) if candidate.statuses else None
            if status and (not latest or latest.status != status):
                continue
            if shortlisted is not None and (not latest or latest.shortlisted != shortlisted):
                continue
            if contacted is not None and (not latest or latest.contacted != contacted):
                continue
            filtered.append(candidate)
        return filtered

    def find_by_source_file(self, source_file: str) -> Candidate | None:
        stmt = select(Candidate).where(Candidate.source_file == source_file)
        return self.session.execute(stmt).scalar_one_or_none()

    def add_note(self, note: RecruiterNote) -> RecruiterNote:
        self.session.add(note)
        self.session.flush()
        return note

    def add_status(self, status: CandidateStatus) -> CandidateStatus:
        self.session.add(status)
        self.session.flush()
        return status

    def latest_status(self, candidate_id: str) -> CandidateStatus | None:
        stmt = (
            select(CandidateStatus)
            .where(CandidateStatus.candidate_id == candidate_id)
            .order_by(CandidateStatus.created_at.desc())
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def candidate_notes(self, candidate_id: str) -> list[RecruiterNote]:
        stmt = (
            select(RecruiterNote)
            .where(RecruiterNote.candidate_id == candidate_id)
            .order_by(RecruiterNote.created_at.desc())
        )
        return list(self.session.execute(stmt).scalars().all())

    def log_query(self, query: QueryHistory) -> QueryHistory:
        self.session.add(query)
        self.session.flush()
        return query

    def recent_queries(self, limit: int = 10) -> list[QueryHistory]:
        stmt = select(QueryHistory).order_by(QueryHistory.created_at.desc()).limit(limit)
        return list(self.session.execute(stmt).scalars().all())
