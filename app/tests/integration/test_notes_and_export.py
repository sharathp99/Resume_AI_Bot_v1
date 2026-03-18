from __future__ import annotations

from pathlib import Path

from app.db.models.entities import Candidate, CandidateContact, CandidateSkill, CandidateStatus
from app.db.repositories.candidate_repository import CandidateRepository
from app.services.export.export_service import ExportService



def test_notes_status_and_export(session, tmp_path: Path, monkeypatch) -> None:
    repo = CandidateRepository(session)
    candidate = Candidate(
        id="cand-1",
        role_bucket="data_engineer",
        full_name="Alex Johnson",
        raw_text="Python SQL",
        source_file="alex.pdf",
        content_hash="hash-1",
        extraction_status="completed",
    )
    candidate.contact = CandidateContact(email="alex@example.com", phone="1234567890", address="Seattle, WA")
    candidate.skills = [CandidateSkill(skill="Python"), CandidateSkill(skill="SQL")]
    candidate.statuses = [CandidateStatus(status="shortlisted", shortlisted=True, contacted=False)]
    repo.upsert_candidate(candidate)

    settings = __import__("app.core.config", fromlist=["get_settings"]).get_settings()
    monkeypatch.setattr(settings, "export_root", tmp_path)

    export_service = ExportService(session)
    export_file = export_service.export_shortlist(["cand-1"], "csv")

    assert Path(export_file).exists()
    assert "Alex Johnson" in Path(export_file).read_text()
