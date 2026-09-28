"""Application settings loaded from environment variables or the repo root .env file."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    openai_api_key: str = ""
    database_url: str = "postgresql+asyncpg://rag:rag@localhost:5432/rag"

    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    chat_model: str = "gpt-4o-mini"

    # Chunks are measured in words. 600 words is roughly 800 tokens.
    chunk_size_words: int = 600
    chunk_overlap_words: int = 75

    top_k: int = 5
    similarity_threshold: float = 0.35

    model_config = SettingsConfigDict(
        env_file=(REPO_ROOT / ".env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
