from __future__ import annotations

from app.db.models.entities import Candidate, CandidateContact, CandidateSkill, CandidateStatus
from app.db.repositories.candidate_repository import CandidateRepository
from app.services.chat.chat_service import RecruiterCopilotService
from app.services.ingestion.ingestion_service import IngestionService



def test_chat_candidate_detail_lookup(session) -> None:
    repo = CandidateRepository(session)
    candidate = Candidate(
        id="cand-1",
        role_bucket="data_engineer",
        full_name="Alex Johnson",
        summary="Strong data engineer with Python and SQL",
        raw_text="Python SQL",
        source_file="alex.pdf",
        content_hash="hash-1",
        extraction_status="completed",
        location="Seattle, WA",
    )
    candidate.contact = CandidateContact(email="alex@example.com", phone="1234567890", address="Seattle, WA")
    candidate.skills = [CandidateSkill(skill="Python"), CandidateSkill(skill="SQL")]
    candidate.statuses = [CandidateStatus(status="new", shortlisted=False, contacted=False)]
    repo.upsert_candidate(candidate)

    service = RecruiterCopilotService(session)
    response = service.handle_message(
        message="Show this candidate's phone, email, address, and summary",
        role_bucket="data_engineer",
        candidate_ids=["cand-1"],
        jd_text=None,
    )

    assert response.tool_name == "get_candidate_profile"
    assert "alex@example.com" in response.answer
