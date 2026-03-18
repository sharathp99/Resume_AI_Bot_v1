from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import SearchError
from app.db.repositories.candidate_repository import CandidateRepository
from app.schemas.chat import ChatEvidence, ChatResponse
from app.services.search.search_service import SearchService


class RecruiterCopilotService:
    """Tool-driven recruiter copilot that only answers from indexed data."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.search_service = SearchService(session)
        self.repo = CandidateRepository(session)

    def handle_message(
        self, message: str, role_bucket: str | None, candidate_ids: list[str], jd_text: str | None, session_id: str | None = None
    ) -> ChatResponse:
        lower_message = message.lower()
        if jd_text and role_bucket and ("top" in lower_message or "best" in lower_message or "candidate" in lower_message):
            results = self.search_service.search_candidates_by_jd(role_bucket, jd_text, top_k=5, session_id=session_id)
            evidence = [
                ChatEvidence(candidate_id=result.candidate_id, snippet=snippet, source_file=self.repo.get_candidate(result.candidate_id).source_file)
                for result in results
                for snippet in result.evidence_snippets[:1]
            ]
            answer = "Top candidates: " + "; ".join(
                f"{result.full_name or result.candidate_id} ({result.score})" for result in results
            )
            return ChatResponse(answer=answer, tool_name="search_candidates_by_jd", evidence=evidence)
        if candidate_ids and ("compare" in lower_message or "difference" in lower_message):
            if not role_bucket or not jd_text:
                raise SearchError("Comparison requires role_bucket and jd_text context.")
            comparison = self.search_service.compare_candidates(role_bucket, candidate_ids, jd_text)
            evidence = [
                ChatEvidence(candidate_id=result.candidate_id, snippet=result.evidence_snippets[0], source_file=self.repo.get_candidate(result.candidate_id).source_file)
                for result in comparison.candidates
                if result.evidence_snippets
            ]
            return ChatResponse(
                answer=comparison.recommendation,
                tool_name="compare_candidates",
                evidence=evidence,
            )
        if candidate_ids and ("phone" in lower_message or "email" in lower_message or "address" in lower_message or "summary" in lower_message):
            candidate = self.search_service.get_candidate_profile(candidate_ids[0])
            answer = (
                f"{candidate.full_name}: email={candidate.contact.email if candidate.contact else 'missing'}, "
                f"phone={candidate.contact.phone if candidate.contact else 'missing'}, "
                f"address={candidate.contact.address if candidate.contact else 'missing'}, "
                f"summary={candidate.summary or 'missing'}"
            )
            evidence = [
                ChatEvidence(candidate_id=candidate.id, snippet=(candidate.summary or candidate.raw_text[:200]), source_file=candidate.source_file)
            ]
            return ChatResponse(answer=answer, tool_name="get_candidate_profile", evidence=evidence)
        raise SearchError(
            "Unsupported query type. Try JD ranking, candidate detail lookup, or candidate comparison with the required context."
        )
