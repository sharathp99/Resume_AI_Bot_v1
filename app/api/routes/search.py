from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies.database import get_db
from app.db.repositories.candidate_repository import CandidateRepository
from app.schemas.search import (
    CandidateSearchRequest,
    CandidateSearchResponse,
    ComparisonRequest,
    ComparisonResponse,
    SkillSearchRequest,
)
from app.services.search.search_service import SearchService

router = APIRouter()


@router.post("/jd", response_model=CandidateSearchResponse)
def search_by_jd(payload: CandidateSearchRequest, db: Session = Depends(get_db)) -> CandidateSearchResponse:
    service = SearchService(db)
    try:
        results = service.search_candidates_by_jd(payload.role_bucket, payload.jd_text, payload.top_k, payload.session_id)
        return CandidateSearchResponse(results=results)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/skills", response_model=CandidateSearchResponse)
def search_by_skills(payload: SkillSearchRequest, db: Session = Depends(get_db)) -> CandidateSearchResponse:
    service = SearchService(db)
    try:
        return CandidateSearchResponse(
            results=service.search_candidates_by_skills(payload.role_bucket, payload.skills, payload.top_k, payload.session_id)
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/compare", response_model=ComparisonResponse)
def compare_candidates(payload: ComparisonRequest, db: Session = Depends(get_db)) -> ComparisonResponse:
    service = SearchService(db)
    try:
        return ComparisonResponse(comparison=service.compare_candidates(payload.role_bucket, payload.candidate_ids, payload.jd_text))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/history")
def recent_query_history(db: Session = Depends(get_db)) -> list[dict]:
    repo = CandidateRepository(db)
    return [
        {
            "query_text": item.query_text,
            "role_bucket": item.role_bucket,
            "query_type": item.query_type,
            "returned_candidate_ids": item.returned_candidate_ids,
            "created_at": item.created_at,
        }
        for item in repo.recent_queries()
    ]
