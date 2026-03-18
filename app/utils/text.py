from __future__ import annotations

import hashlib
import re
from pathlib import Path


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def stable_candidate_id(role_bucket: str, source_file: str) -> str:
    payload = f"{role_bucket}:{Path(source_file).name}:{source_file}"
    return sha256_text(payload)[:24]


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    clean_text = text.strip()
    if not clean_text:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(clean_text):
        end = min(len(clean_text), start + chunk_size)
        chunks.append(clean_text[start:end])
        if end == len(clean_text):
            break
        start = max(0, end - overlap)
    return chunks
