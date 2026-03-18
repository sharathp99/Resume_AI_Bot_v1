from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    role_bucket: str | None = None
    message: str
    session_id: str | None = None
    candidate_ids: list[str] = Field(default_factory=list)
    jd_text: str | None = None


class ChatEvidence(BaseModel):
    candidate_id: str
    snippet: str
    source_file: str


class ChatResponse(BaseModel):
    answer: str
    tool_name: str
    evidence: list[ChatEvidence] = Field(default_factory=list)
