"""Configuration for the ML service."""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    # Load .env from project root (document_rag/.env)
    _env_path = Path(__file__).resolve().parents[5] / ".env"
    load_dotenv(_env_path)
except ImportError:
    pass


class Settings:
    """Settings loaded from environment."""

    # LLM backend configuration (reuses RAG service patterns)
    LLM_BACKEND: str = os.getenv("LLM_BACKEND", "llama")
    LLM_URL: str = os.getenv("LLM_URL", "http://localhost:8080").rstrip("/")

    # OpenAI backend
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    OPENAI_BASE_URL: str | None = os.getenv("OPENAI_BASE_URL") or None

    # Injection detection thresholds
    INJECTION_THRESHOLD: float = float(os.getenv("INJECTION_THRESHOLD", "0.7"))

    # Retrieval scoring thresholds
    RETRIEVAL_SCORE_THRESHOLD: float = float(os.getenv("RETRIEVAL_SCORE_THRESHOLD", "0.5"))

    # Service port
    PORT: int = int(os.getenv("ML_SERVICE_PORT", "8005"))


settings = Settings()
