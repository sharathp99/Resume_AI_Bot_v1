from __future__ import annotations

from pydantic import BaseModel, Field


class IngestionRequest(BaseModel):
    role_bucket: str
    reindex: bool = False


class IngestionFileResult(BaseModel):
    source_file: str
    status: str
    candidate_id: str | None = None
    error: str | None = None


class IngestionResponse(BaseModel):
    role_bucket: str
    indexed_count: int
    failed_count: int
    files: list[IngestionFileResult] = Field(default_factory=list)
