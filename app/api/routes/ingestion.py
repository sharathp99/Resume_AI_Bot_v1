from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies.database import get_db
from app.schemas.ingestion import IngestionRequest, IngestionResponse
from app.services.ingestion.ingestion_service import IngestionService

router = APIRouter()


@router.post("/resumes", response_model=IngestionResponse)
def ingest_resumes(payload: IngestionRequest, db: Session = Depends(get_db)) -> IngestionResponse:
    service = IngestionService(db)
    try:
        return service.ingest_role_bucket(payload.role_bucket, reindex=payload.reindex)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
