from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies.database import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat.chat_service import RecruiterCopilotService

router = APIRouter()


@router.post("/", response_model=ChatResponse)
def recruiter_chat(payload: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    service = RecruiterCopilotService(db)
    try:
        return service.handle_message(
            message=payload.message,
            role_bucket=payload.role_bucket,
            candidate_ids=payload.candidate_ids,
            jd_text=payload.jd_text,
            session_id=payload.session_id,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
