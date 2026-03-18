from __future__ import annotations

from app.schemas.candidate import CandidateContactSchema, CandidateProfileSchema, CandidateSkillSchema
from app.schemas.jd import JobDescriptionStructured
from app.services.ranking.ranking_service import RankingService



def test_ranking_prioritizes_skill_match() -> None:
    service = RankingService()
    candidates = [
        CandidateProfileSchema(
            id="1",
            role_bucket="data_engineer",
            full_name="Alex",
            raw_text="Python SQL Airflow",
            source_file="a.pdf",
            extraction_status="completed",
            contact=CandidateContactSchema(email="alex@example.com"),
            skills=[CandidateSkillSchema(skill="Python"), CandidateSkillSchema(skill="SQL")],
        ),
        CandidateProfileSchema(
            id="2",
            role_bucket="data_engineer",
            full_name="Jamie",
            raw_text="Tableau only",
            source_file="b.pdf",
            extraction_status="completed",
            skills=[CandidateSkillSchema(skill="Tableau")],
        ),
    ]
    jd = JobDescriptionStructured(must_have_skills=["Python", "SQL"])

    results = service.rank_candidates(candidates, jd, {"1": 0.8, "2": 0.2}, {"1": ["Python SQL"]})

    assert results[0].candidate_id == "1"
    assert results[0].score > results[1].score
