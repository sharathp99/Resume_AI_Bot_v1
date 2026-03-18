from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.models.entities import (
    Candidate,
    CandidateCertification,
    CandidateContact,
    CandidateEducation,
    CandidateExperience,
    CandidateSkill,
    CandidateStatus,
    IndexingJob,
    ResumeDocument,
)
from app.db.repositories.candidate_repository import CandidateRepository
from app.db.repositories.ingestion_repository import IngestionRepository
from app.integrations.openai.client import OpenAIProvider
from app.integrations.qdrant.client import QdrantIndex
from app.schemas.ingestion import IngestionFileResult, IngestionResponse
from app.services.extraction.resume_extractor import ResumeExtractor
from app.services.parsing.document_parser import DocumentParser
from app.utils.text import chunk_text, sha256_text, stable_candidate_id

logger = get_logger(__name__)


class IngestionService:
    """Handles resume ingestion, structured extraction, storage, and indexing."""

    def __init__(
        self,
        session: Session,
        openai_provider: OpenAIProvider | None = None,
        vector_index: QdrantIndex | None = None,
    ) -> None:
        self.settings = get_settings()
        self.session = session
        self.parser = DocumentParser()
        self.extractor = ResumeExtractor(openai_provider)
        self.vector_index = vector_index or QdrantIndex()
        self.candidate_repo = CandidateRepository(session)
        self.ingestion_repo = IngestionRepository(session)
        self.openai_provider = openai_provider or OpenAIProvider()

    def ingest_role_bucket(self, role_bucket: str, reindex: bool = False) -> IngestionResponse:
        role_path = self.settings.resume_root / role_bucket
        if not role_path.exists():
            raise FileNotFoundError(f"Role bucket folder not found: {role_path}")
        files = sorted(
            [path for path in role_path.iterdir() if path.suffix.lower() in self.parser.SUPPORTED_EXTENSIONS]
        )
        if reindex:
            self.vector_index.recreate_collection(vector_size=self._vector_size())
        else:
            self.vector_index.ensure_collection(vector_size=self._vector_size())
        results: list[IngestionFileResult] = []
        indexed_count = 0
        failed_count = 0
        for file_path in files:
            job = self.ingestion_repo.create_job(
                IndexingJob(role_bucket=role_bucket, source_file=str(file_path), status="running")
            )
            try:
                result = self._ingest_file(role_bucket, file_path)
                job.status = "completed"
                indexed_count += 1
            except Exception as exc:
                logger.exception("resume_ingestion_failed", source_file=str(file_path), error=str(exc))
                job.status = "failed"
                job.error_message = str(exc)
                result = IngestionFileResult(source_file=str(file_path), status="failed", error=str(exc))
                failed_count += 1
            results.append(result)
        return IngestionResponse(
            role_bucket=role_bucket,
            indexed_count=indexed_count,
            failed_count=failed_count,
            files=results,
        )

    def _ingest_file(self, role_bucket: str, file_path: Path) -> IngestionFileResult:
        raw_text = self.parser.extract_text(file_path)
        content_hash = sha256_text(raw_text)
        existing = self.candidate_repo.find_by_source_file(str(file_path))
        candidate_id = stable_candidate_id(role_bucket, str(file_path))
        if existing and existing.content_hash == content_hash:
            return IngestionFileResult(source_file=str(file_path), status="skipped", candidate_id=existing.id)
        extraction = self.extractor.extract(raw_text)
        if existing:
            self.vector_index.delete_candidate(existing.id)
        candidate = Candidate(
            id=candidate_id,
            role_bucket=role_bucket,
            full_name=extraction.full_name,
            current_title=extraction.current_title,
            years_experience=extraction.years_experience,
            summary=extraction.summary,
            location=extraction.location,
            linkedin_url=extraction.linkedin_url,
            github_url=extraction.github_url,
            work_authorization=extraction.work_authorization,
            extraction_confidence=extraction.extraction_confidence,
            raw_text=raw_text,
            source_file=str(file_path),
            content_hash=content_hash,
            extraction_status="completed",
            extraction_error=None,
        )
        candidate.contact = CandidateContact(
            email=str(extraction.email) if extraction.email else None,
            phone=extraction.phone,
            address=extraction.address or extraction.location,
        )
        candidate.skills = [CandidateSkill(skill=skill, category="resume") for skill in extraction.skills]
        candidate.education = [
            CandidateEducation(**education.model_dump()) for education in extraction.education
        ]
        candidate.experiences = [
            CandidateExperience(
                company=experience.company,
                title=experience.title,
                start_date=experience.start_date,
                end_date=experience.end_date,
                description=experience.description,
            )
            for experience in extraction.experience_history
        ]
        candidate.certifications = [
            CandidateCertification(name=cert.name, issuer=cert.issuer) for cert in extraction.certifications
        ]
        candidate.documents = [
            ResumeDocument(
                role_bucket=role_bucket,
                source_file=str(file_path),
                document_type=file_path.suffix.lower().lstrip("."),
                raw_text=raw_text,
                metadata_json={"file_name": file_path.name},
            )
        ]
        candidate.statuses = [CandidateStatus(status="new", shortlisted=False, contacted=False)]
        self.candidate_repo.upsert_candidate(candidate)
        self._index_candidate(candidate)
        return IngestionFileResult(source_file=str(file_path), status="indexed", candidate_id=candidate_id)

    def _index_candidate(self, candidate: Candidate) -> None:
        chunks = chunk_text(candidate.raw_text, self.settings.chunk_size, self.settings.chunk_overlap)
        vectors = self._embed_chunks(chunks)
        points = []
        for index, (chunk, vector) in enumerate(zip(chunks, vectors, strict=False)):
            points.append(
                {
                    "id": int(sha256_text(f"{candidate.id}-{index}")[:12], 16),
                    "vector": vector,
                    "payload": {
                        "candidate_id": candidate.id,
                        "role_bucket": candidate.role_bucket,
                        "source_file": candidate.source_file,
                        "chunk_id": index,
                        "text_snippet": chunk[:300],
                        "skills": [skill.skill for skill in candidate.skills],
                    },
                }
            )
        self.vector_index.upsert_points(points)

    def _embed_chunks(self, chunks: list[str]) -> list[list[float]]:
        if self.openai_provider.enabled:
            return self.openai_provider.embed(chunks)
        vectors = []
        for chunk in chunks:
            vector = [0.0] * 8
            for index, token in enumerate(chunk.lower().split()[:256]):
                vector[index % 8] += (sum(ord(char) for char in token) % 101) / 101
            norm = sum(item * item for item in vector) ** 0.5 or 1.0
            vectors.append([item / norm for item in vector])
        return vectors

    def _vector_size(self) -> int:
        return 1536 if self.openai_provider.enabled else 8
