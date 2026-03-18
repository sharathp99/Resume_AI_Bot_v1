from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.dependencies.database import get_db
from app.schemas.export import ExportRequest
from app.services.export.export_service import ExportService

router = APIRouter()


@router.post("/shortlist")
def export_shortlist(payload: ExportRequest, db: Session = Depends(get_db)) -> FileResponse:
    service = ExportService(db)
    try:
        export_path = service.export_shortlist(payload.candidate_ids, payload.format)
        return FileResponse(path=export_path, filename=export_path.name)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
