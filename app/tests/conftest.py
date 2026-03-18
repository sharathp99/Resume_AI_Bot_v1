from __future__ import annotations

import os
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_resume_intelligence.db")
os.environ.setdefault("ENABLE_OPENAI_EXTRACTION", "false")
os.environ.setdefault("ENABLE_QDRANT", "false")

from app.db.base import Base  # noqa: E402


@pytest.fixture()
def session(tmp_path: Path):
    database_url = f"sqlite:///{tmp_path / 'test.db'}"
    engine = create_engine(database_url, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
        db.commit()
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
