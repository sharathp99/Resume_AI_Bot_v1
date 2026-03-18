from __future__ import annotations

from dataclasses import dataclass

from app.core.config import get_settings
from app.schemas.candidate import CandidateProfileSchema, CandidateSearchResult
from app.schemas.jd import JobDescriptionStructured


@dataclass
class RankingComponentScores:
    required_skill_score: float
    preferred_skill_score: float
    semantic_score: float
    experience_score: float
    domain_score: float
    education_score: float


class RankingService:
    """Weighted ranking service for candidate recommendation and explainability."""

    def __init__(self) -> None:
        self.settings = get_settings()

    def rank_candidates(
        self,
        candidates: list[CandidateProfileSchema],
        jd: JobDescriptionStructured,
        semantic_scores: dict[str, float],
        evidence: dict[str, list[str]],
    ) -> list[CandidateSearchResult]:
        results = []
        for candidate in candidates:
            scores = self._calculate_component_scores(candidate, jd, semantic_scores.get(candidate.id, 0.0))
            total_score = (
                scores.required_skill_score * self.settings.ranking_required_skill_weight
                + scores.preferred_skill_score * self.settings.ranking_preferred_skill_weight
                + scores.semantic_score * self.settings.ranking_semantic_weight
                + scores.experience_score * self.settings.ranking_experience_weight
                + scores.domain_score * self.settings.ranking_domain_weight
                + scores.education_score * self.settings.ranking_education_weight
            )
            strengths, gaps = self._build_strengths_and_gaps(candidate, jd)
            results.append(
                CandidateSearchResult(
                    candidate_id=candidate.id,
                    full_name=candidate.full_name,
                    score=round(total_score * 100, 2),
                    email=candidate.contact.email if candidate.contact else None,
                    phone=candidate.contact.phone if candidate.contact else None,
                    location=candidate.location,
                    top_skills=[skill.skill for skill in candidate.skills[:8]],
                    strengths=strengths,
                    gaps=gaps,
                    evidence_snippets=evidence.get(candidate.id, [])[:4],
                    explanation=self._build_explanation(candidate, scores, strengths, gaps),
                )
            )
        return sorted(results, key=lambda item: item.score, reverse=True)

    def _calculate_component_scores(
        self, candidate: CandidateProfileSchema, jd: JobDescriptionStructured, semantic_score: float
    ) -> RankingComponentScores:
        candidate_skills = {skill.skill.lower() for skill in candidate.skills}
        required = {skill.lower() for skill in jd.must_have_skills}
        preferred = {skill.lower() for skill in jd.nice_to_have_skills}
        required_score = len(candidate_skills & required) / max(len(required), 1)
        preferred_score = len(candidate_skills & preferred) / max(len(preferred), 1) if preferred else 1.0
        experience_score = 1.0
        if jd.years_required is not None:
            years = candidate.years_experience or 0.0
            experience_score = min(years / max(jd.years_required, 1.0), 1.0)
        domain_score = 1.0 if any(domain.lower() in (candidate.summary or "").lower() for domain in jd.domain_experience) else 0.5
        education_score = 1.0 if not jd.education_or_certs else float(bool(candidate.education or candidate.certifications))
        return RankingComponentScores(
            required_skill_score=required_score,
            preferred_skill_score=preferred_score,
            semantic_score=max(min(semantic_score, 1.0), 0.0),
            experience_score=experience_score,
            domain_score=domain_score,
            education_score=education_score,
        )

    def _build_strengths_and_gaps(self, candidate: CandidateProfileSchema, jd: JobDescriptionStructured) -> tuple[list[str], list[str]]:
        candidate_skills = {skill.skill.lower() for skill in candidate.skills}
        strengths = [skill for skill in jd.must_have_skills if skill.lower() in candidate_skills]
        gaps = [skill for skill in jd.must_have_skills if skill.lower() not in candidate_skills]
        if candidate.years_experience and jd.years_required and candidate.years_experience >= jd.years_required:
            strengths.append(f"Experience meets {jd.years_required}+ years requirement")
        elif jd.years_required:
            gaps.append(f"Experience below {jd.years_required}+ years target")
        return strengths[:5], gaps[:5]

    def _build_explanation(
        self, candidate: CandidateProfileSchema, scores: RankingComponentScores, strengths: list[str], gaps: list[str]
    ) -> str:
        lead = candidate.full_name or candidate.id
        return (
            f"{lead} scored highly due to strong required-skill coverage ({scores.required_skill_score:.2f}), "
            f"semantic alignment ({scores.semantic_score:.2f}), and experience fit ({scores.experience_score:.2f}). "
            f"Strengths: {', '.join(strengths) if strengths else 'none observed'}. "
            f"Gaps: {', '.join(gaps) if gaps else 'no major gaps detected'}."
        )
