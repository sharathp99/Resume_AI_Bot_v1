from __future__ import annotations

from pathlib import Path

import fitz

from app.core.config import get_settings
from app.services.ingestion.ingestion_service import IngestionService
from app.services.search.search_service import SearchService



def test_end_to_end_ingestion_and_search(session, tmp_path: Path, monkeypatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "resume_root", tmp_path)
    monkeypatch.setattr(settings, "export_root", tmp_path / "exports")
    settings.export_root.mkdir(parents=True, exist_ok=True)

    role_folder = tmp_path / "data_engineer"
    role_folder.mkdir(parents=True, exist_ok=True)
    resume_path = role_folder / "alex.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Alex Johnson\nData Engineer\nalex@example.com\n(206) 555-0101\nPython SQL Airflow AWS\n8 years of experience")
    doc.save(resume_path)
    doc.close()

    ingestion = IngestionService(session)
    result = ingestion.ingest_role_bucket("data_engineer", reindex=True)

    assert result.indexed_count == 1

    search_service = SearchService(session)
    ranked = search_service.search_candidates_by_jd(
        role_bucket="data_engineer",
        jd_text="Data Engineer with Python SQL Airflow and AWS. 5+ years.",
        top_k=3,
    )

    assert ranked
    assert ranked[0].full_name == "Alex Johnson"
