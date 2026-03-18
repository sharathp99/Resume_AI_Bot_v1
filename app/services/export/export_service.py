from __future__ import annotations

from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import ExportError
from app.db.repositories.candidate_repository import CandidateRepository


class ExportService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repo = CandidateRepository(session)
        self.settings = get_settings()

    def export_shortlist(self, candidate_ids: list[str], export_format: str) -> Path:
        if not candidate_ids:
            raise ExportError("No candidates selected for export.")
        rows = []
        for candidate_id in candidate_ids:
            candidate = self.repo.get_candidate(candidate_id)
            if not candidate:
                continue
            rows.append(
                {
                    "candidate_id": candidate.id,
                    "full_name": candidate.full_name,
                    "role_bucket": candidate.role_bucket,
                    "email": candidate.contact.email if candidate.contact else None,
                    "phone": candidate.contact.phone if candidate.contact else None,
                    "location": candidate.location,
                    "skills": ", ".join(skill.skill for skill in candidate.skills),
                    "summary": candidate.summary,
                }
            )
        if not rows:
            raise ExportError("No valid candidates found for export.")
        df = pd.DataFrame(rows)
        filename = self.settings.export_root / f"shortlist_export.{export_format}"
        if export_format == "csv":
            df.to_csv(filename, index=False)
        elif export_format == "xlsx":
            df.to_excel(filename, index=False)
        else:
            raise ExportError(f"Invalid export format: {export_format}")
        return filename
