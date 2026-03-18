from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class ExportRequest(BaseModel):
    candidate_ids: list[str]
    format: Literal["csv", "xlsx"] = "csv"
