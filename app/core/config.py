from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="Resume Intelligence Platform", alias="APP_NAME")
    app_env: str = Field(default="local", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    database_url: str = Field(default="sqlite:///./resume_intelligence.db", alias="DATABASE_URL")
    qdrant_url: str = Field(default="http://localhost:6333", alias="QDRANT_URL")
    qdrant_collection: str = Field(default="resume_candidates", alias="QDRANT_COLLECTION")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_chat_model: str = Field(default="gpt-4.1-mini", alias="OPENAI_CHAT_MODEL")
    openai_embedding_model: str = Field(
        default="text-embedding-3-small", alias="OPENAI_EMBEDDING_MODEL"
    )
    data_root: Path = Field(default=Path("./data"), alias="DATA_ROOT")
    resume_root: Path = Field(default=Path("./data/resumes"), alias="RESUME_ROOT")
    export_root: Path = Field(default=Path("./data/exports"), alias="EXPORT_ROOT")
    default_top_k: int = Field(default=5, alias="DEFAULT_TOP_K")
    chunk_size: int = Field(default=900, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=120, alias="CHUNK_OVERLAP")
    ranking_required_skill_weight: float = Field(
        default=0.35, alias="RANKING_REQUIRED_SKILL_WEIGHT"
    )
    ranking_preferred_skill_weight: float = Field(
        default=0.15, alias="RANKING_PREFERRED_SKILL_WEIGHT"
    )
    ranking_semantic_weight: float = Field(default=0.25, alias="RANKING_SEMANTIC_WEIGHT")
    ranking_experience_weight: float = Field(default=0.10, alias="RANKING_EXPERIENCE_WEIGHT")
    ranking_domain_weight: float = Field(default=0.10, alias="RANKING_DOMAIN_WEIGHT")
    ranking_education_weight: float = Field(default=0.05, alias="RANKING_EDUCATION_WEIGHT")
    enable_openai_extraction: bool = Field(default=True, alias="ENABLE_OPENAI_EXTRACTION")
    enable_qdrant: bool = Field(default=True, alias="ENABLE_QDRANT")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.data_root.mkdir(parents=True, exist_ok=True)
    settings.resume_root.mkdir(parents=True, exist_ok=True)
    settings.export_root.mkdir(parents=True, exist_ok=True)
    return settings
