"""Configuration for the MCP server (service URLs from environment)."""

import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class Settings:
    """Settings loaded from environment."""

    RETRIEVAL_SERVICE_URL: str = os.getenv(
        "RETRIEVAL_SERVICE_URL", "http://localhost:8003"
    ).rstrip("/")
    EMBEDDING_SERVICE_URL: str = os.getenv(
        "EMBEDDING_SERVICE_URL", "http://localhost:8002"
    ).rstrip("/")
    RAG_SERVICE_URL: str = os.getenv(
        "RAG_SERVICE_URL", "http://localhost:8004"
    ).rstrip("/")
    INGESTION_SERVICE_URL: str = os.getenv(
        "INGESTION_SERVICE_URL", "http://localhost:8001"
    ).rstrip("/")
    TOP_K: int = int(os.getenv("TOP_K", "3"))


settings = Settings()
