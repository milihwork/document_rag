"""Configuration for the Embedding service."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root (document_rag/.env)
_env_path = Path(__file__).resolve().parents[5] / ".env"
load_dotenv(_env_path)


class Settings:
    """Settings loaded from environment."""

    EMBEDDING_BACKEND: str = os.getenv("EMBEDDING_BACKEND", "local")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")


settings = Settings()
