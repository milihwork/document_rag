"""Configuration for the Retrieval service."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root (document_rag/.env)
_env_path = Path(__file__).resolve().parents[5] / ".env"
load_dotenv(_env_path)


class Settings:
    """Settings loaded from environment."""

    VECTOR_BACKEND: str = os.getenv("VECTOR_BACKEND", "qdrant")
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
    COLLECTION_NAME: str = os.getenv("COLLECTION_NAME", "documents")
    VECTOR_SIZE: int = int(os.getenv("VECTOR_SIZE", "384"))
    TOP_K: int = int(os.getenv("TOP_K", "3"))

    # pgvector backend
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql://localhost/document_rag"
    )
    PGVECTOR_TABLE_NAME: str = os.getenv("PGVECTOR_TABLE_NAME", "documents")


settings = Settings()
