"""Configuration for the Ingestion service."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root (document_rag/.env)
_env_path = Path(__file__).resolve().parents[5] / ".env"
load_dotenv(_env_path)


class Settings:
    """Settings loaded from environment."""

    EMBEDDING_URL: str = os.getenv("EMBEDDING_URL", "http://localhost:8002").rstrip("/")
    RETRIEVAL_URL: str = os.getenv("RETRIEVAL_URL", "http://localhost:8003").rstrip("/")
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "800"))

    # ML Service for document classification
    ML_SERVICE_URL: str = os.getenv("ML_SERVICE_URL", "http://localhost:8005").rstrip("/")
    DOCUMENT_CLASSIFICATION_ENABLED: bool = (
        os.getenv("DOCUMENT_CLASSIFICATION_ENABLED", "true").strip().lower() in ("true", "1", "yes")
    )


settings = Settings()
