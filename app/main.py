from __future__ import annotations

from fastapi import FastAPI

from app.api.routes import candidates, chat, exports, health, ingestion, notes, search
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import init_db

configure_logging()
settings = get_settings()
init_db()

app = FastAPI(title=settings.app_name, version="0.1.0")
app.include_router(health.router)
app.include_router(ingestion.router, prefix="/api/ingestion", tags=["ingestion"])
app.include_router(candidates.router, prefix="/api/candidates", tags=["candidates"])
app.include_router(search.router, prefix="/api/search", tags=["search"])
app.include_router(notes.router, prefix="/api/notes", tags=["notes"])
app.include_router(exports.router, prefix="/api/exports", tags=["exports"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
