"""Configuration for the Embedding service."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root (document_rag/.env)
_env_path = Path(__file__).resolve().parents[5] / ".env"
load_dotenv(_env_path)

def _parse_bool(value: str | None, *, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "t", "yes", "y", "on"}


class Settings:
    """Settings loaded from environment."""

    EMBEDDING_BACKEND: str = os.getenv("EMBEDDING_BACKEND", "local")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
    # Normalize embeddings by default (cosine-friendly).
    EMBEDDING_NORMALIZE: bool = _parse_bool(os.getenv("EMBEDDING_NORMALIZE"), default=True)

    # Optional runtime knobs for sentence-transformers backends.
    EMBEDDING_DEVICE: str | None = os.getenv("EMBEDDING_DEVICE") or None
    EMBEDDING_BATCH_SIZE: int = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))
    EMBEDDING_MAX_LENGTH: int | None = (
        int(os.getenv("EMBEDDING_MAX_LENGTH")) if os.getenv("EMBEDDING_MAX_LENGTH") else None
    )


settings = Settings()
