from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies.database import get_db
from app.db.models.entities import CandidateStatus, RecruiterNote
from app.db.repositories.candidate_repository import CandidateRepository
from app.schemas.candidate import NoteCreateRequest, RecruiterNoteSchema, StatusUpdateRequest

router = APIRouter()


@router.post("/", response_model=RecruiterNoteSchema)
def add_note(payload: NoteCreateRequest, db: Session = Depends(get_db)) -> RecruiterNoteSchema:
    repo = CandidateRepository(db)
    if not repo.get_candidate(payload.candidate_id):
        raise HTTPException(status_code=404, detail="Candidate not found")
    note = repo.add_note(
        RecruiterNote(candidate_id=payload.candidate_id, note_text=payload.note_text, created_by=payload.created_by)
    )
    return RecruiterNoteSchema.model_validate(note)


@router.get("/{candidate_id}", response_model=list[RecruiterNoteSchema])
def get_notes(candidate_id: str, db: Session = Depends(get_db)) -> list[RecruiterNoteSchema]:
    repo = CandidateRepository(db)
    return [RecruiterNoteSchema.model_validate(note) for note in repo.candidate_notes(candidate_id)]


@router.post("/status")
def update_status(payload: StatusUpdateRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    repo = CandidateRepository(db)
    if not repo.get_candidate(payload.candidate_id):
        raise HTTPException(status_code=404, detail="Candidate not found")
    repo.add_status(
        CandidateStatus(
            candidate_id=payload.candidate_id,
            status=payload.status,
            shortlisted=payload.shortlisted,
            contacted=payload.contacted,
            metadata_json=payload.metadata_json,
        )
    )
    return {"status": "updated"}
