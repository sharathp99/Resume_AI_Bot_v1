from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.entities import IndexingJob, JobDescription


class IngestionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_job(self, job: IndexingJob) -> IndexingJob:
        self.session.add(job)
        self.session.flush()
        return job

    def list_jobs(self, role_bucket: str | None = None) -> list[IndexingJob]:
        stmt = select(IndexingJob).order_by(IndexingJob.created_at.desc())
        if role_bucket:
            stmt = stmt.where(IndexingJob.role_bucket == role_bucket)
        return list(self.session.execute(stmt).scalars().all())

    def save_job_description(self, jd: JobDescription) -> JobDescription:
        self.session.add(jd)
        self.session.flush()
        return jd
