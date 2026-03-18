from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies.database import get_db
from app.schemas.candidate import CandidateProfileSchema
from app.services.search.search_service import SearchService

router = APIRouter()


@router.get("/", response_model=list[CandidateProfileSchema])
def list_candidates(
    role_bucket: str | None = Query(default=None),
    status: str | None = Query(default=None),
    shortlisted: bool | None = Query(default=None),
    contacted: bool | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[CandidateProfileSchema]:
    service = SearchService(db)
    return [
        CandidateProfileSchema.model_validate(item)
        for item in service.repo.list_candidates(
            role_bucket=role_bucket,
            status=status,
            shortlisted=shortlisted,
            contacted=contacted,
        )
    ]


@router.get("/{candidate_id}", response_model=CandidateProfileSchema)
def get_candidate(candidate_id: str, db: Session = Depends(get_db)) -> CandidateProfileSchema:
    service = SearchService(db)
    try:
        return service.get_candidate_profile(candidate_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
