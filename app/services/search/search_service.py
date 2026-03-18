from __future__ import annotations

import math
from collections import defaultdict

from sqlalchemy.orm import Session

from app.core.exceptions import SearchError
from app.db.models.entities import QueryHistory
from app.db.repositories.candidate_repository import CandidateRepository
from app.integrations.openai.client import OpenAIProvider
from app.integrations.qdrant.client import QdrantIndex
from app.schemas.candidate import CandidateComparisonResult, CandidateProfileSchema, CandidateSearchResult
from app.schemas.jd import JobDescriptionStructured
from app.services.jd.jd_parser import JobDescriptionParser
from app.services.ranking.ranking_service import RankingService


class SearchService:
    """Coordinates metadata filtering, vector retrieval, and ranking."""

    def __init__(
        self,
        session: Session,
        openai_provider: OpenAIProvider | None = None,
        vector_index: QdrantIndex | None = None,
    ) -> None:
        self.session = session
        self.repo = CandidateRepository(session)
        self.openai_provider = openai_provider or OpenAIProvider()
        self.vector_index = vector_index or QdrantIndex()
        self.jd_parser = JobDescriptionParser(self.openai_provider)
        self.ranking_service = RankingService()

    def search_candidates_by_jd(
        self, role_bucket: str, jd_text: str, top_k: int, session_id: str | None = None
    ) -> list[CandidateSearchResult]:
        jd = self.jd_parser.parse(jd_text)
        candidates = self.repo.list_candidates(role_bucket=role_bucket)
        if not candidates:
            raise SearchError(f"No candidates indexed for role bucket '{role_bucket}'.")
        query_vector = self._embed_query(jd_text)
        vector_hits = self.vector_index.search(query_vector, role_bucket=role_bucket, limit=max(top_k * 3, top_k))
        hit_scores: dict[str, float] = defaultdict(float)
        evidence: dict[str, list[str]] = defaultdict(list)
        for hit in vector_hits:
            hit_scores[hit.candidate_id] = max(hit_scores[hit.candidate_id], self._normalize_qdrant_score(hit.score))
            snippet = hit.payload.get("text_snippet")
            if snippet:
                evidence[hit.candidate_id].append(snippet)
        candidate_map = {candidate.id: CandidateProfileSchema.model_validate(candidate) for candidate in candidates}
        shortlist = [candidate_map[candidate_id] for candidate_id in candidate_map if candidate_id in candidate_map]
        ranked = self.ranking_service.rank_candidates(shortlist, jd, hit_scores, evidence)[:top_k]
        self.repo.log_query(
            QueryHistory(
                query_text=jd_text,
                role_bucket=role_bucket,
                query_type="jd_search",
                returned_candidate_ids=[result.candidate_id for result in ranked],
                session_id=session_id,
            )
        )
        return ranked

    def search_candidates_by_skills(
        self, role_bucket: str, skills: list[str], top_k: int, session_id: str | None = None
    ) -> list[CandidateSearchResult]:
        jd = JobDescriptionStructured(role_title=role_bucket, must_have_skills=skills)
        candidates = [CandidateProfileSchema.model_validate(item) for item in self.repo.list_candidates(role_bucket)]
        if not candidates:
            raise SearchError(f"No candidates indexed for role bucket '{role_bucket}'.")
        evidence = {candidate.id: [candidate.summary or candidate.raw_text[:220]] for candidate in candidates}
        semantic_scores = {
            candidate.id: len({skill.skill.lower() for skill in candidate.skills} & {skill.lower() for skill in skills}) / max(len(skills), 1)
            for candidate in candidates
        }
        ranked = self.ranking_service.rank_candidates(candidates, jd, semantic_scores, evidence)[:top_k]
        self.repo.log_query(
            QueryHistory(
                query_text=", ".join(skills),
                role_bucket=role_bucket,
                query_type="skill_search",
                returned_candidate_ids=[result.candidate_id for result in ranked],
                session_id=session_id,
            )
        )
        return ranked

    def get_candidate_profile(self, candidate_id: str) -> CandidateProfileSchema:
        candidate = self.repo.get_candidate(candidate_id)
        if not candidate:
            raise SearchError(f"Candidate '{candidate_id}' not found.")
        return CandidateProfileSchema.model_validate(candidate)

    def compare_candidates(
        self, role_bucket: str, candidate_ids: list[str], jd_text: str
    ) -> CandidateComparisonResult:
        if len(candidate_ids) < 2:
            raise SearchError("Comparison requires at least two candidates.")
        rankings = self.search_candidates_by_jd(role_bucket=role_bucket, jd_text=jd_text, top_k=25)
        filtered = [result for result in rankings if result.candidate_id in set(candidate_ids)]
        if len(filtered) < 2:
            raise SearchError("Insufficient candidate evidence available for comparison.")
        recommendation = filtered[0].explanation
        return CandidateComparisonResult(jd_title=role_bucket, candidates=filtered, recommendation=recommendation)

    def _embed_query(self, query: str) -> list[float]:
        if self.openai_provider.enabled:
            return self.openai_provider.embed([query])[0]
        terms = query.lower().split()
        vector = [0.0] * 8
        for index, term in enumerate(terms):
            vector[index % 8] += (sum(ord(char) for char in term) % 97) / 97
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

    @staticmethod
    def _normalize_qdrant_score(score: float) -> float:
        return max(min((score + 1.0) / 2.0, 1.0), 0.0)
