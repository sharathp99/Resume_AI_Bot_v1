from __future__ import annotations

from pathlib import Path

import fitz
from docx import Document

from app.core.exceptions import IngestionError


class DocumentParser:
    """Extracts text from supported resume documents."""

    SUPPORTED_EXTENSIONS = {".pdf", ".docx"}

    def extract_text(self, file_path: Path) -> str:
        if not file_path.exists():
            raise IngestionError(f"Source file not found: {file_path}")
        suffix = file_path.suffix.lower()
        if suffix not in self.SUPPORTED_EXTENSIONS:
            raise IngestionError(f"Unsupported format: {suffix}")
        if suffix == ".pdf":
            return self._extract_pdf(file_path)
        return self._extract_docx(file_path)

    def _extract_pdf(self, file_path: Path) -> str:
        try:
            document = fitz.open(file_path)
            text = "\n".join(page.get_text("text") for page in document)
            document.close()
        except Exception as exc:
            raise IngestionError(f"Failed to parse PDF {file_path}: {exc}") from exc
        if not text.strip():
            raise IngestionError(f"PDF is empty: {file_path}")
        return text

    def _extract_docx(self, file_path: Path) -> str:
        try:
            document = Document(file_path)
            text = "\n".join(paragraph.text for paragraph in document.paragraphs)
        except Exception as exc:
            raise IngestionError(f"Failed to parse DOCX {file_path}: {exc}") from exc
        if not text.strip():
            raise IngestionError(f"DOCX is empty: {file_path}")
        return text
