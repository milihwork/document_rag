"""Configuration for the RAG service."""

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
    LLM_BACKEND: str = os.getenv("LLM_BACKEND", "llama")
    LLM_URL: str = os.getenv("LLM_URL", "http://localhost:8080").rstrip("/")
    TOP_K: int = int(os.getenv("TOP_K", "3"))

    # Reranker (optional): set to "none" or "" to disable
    RERANKER_PROVIDER: str = (os.getenv("RERANKER_PROVIDER", "bge") or "").strip().lower()
    VECTOR_SEARCH_TOP_K: int = int(os.getenv("VECTOR_SEARCH_TOP_K", "20"))
    RERANK_TOP_K: int = int(os.getenv("RERANK_TOP_K", "3"))

    # OpenAI backend
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    OPENAI_BASE_URL: str | None = os.getenv("OPENAI_BASE_URL") or None

    # Safeguard (input/output validation): set SAFEGUARD_ENABLED=false to disable
    SAFEGUARD_ENABLED: bool = (
        os.getenv("SAFEGUARD_ENABLED", "true").strip().lower() in ("true", "1", "yes")
    )
    SAFEGUARD_PROVIDER: str = (
        (os.getenv("SAFEGUARD_PROVIDER", "basic") or "basic").strip().lower()
    )

    # ML Service (injection detection, query classification, retrieval scoring)
    ML_SERVICE_ENABLED: bool = (
        os.getenv("ML_SERVICE_ENABLED", "false").strip().lower() in ("true", "1", "yes")
    )
    ML_SERVICE_URL: str = os.getenv("ML_SERVICE_URL", "http://localhost:8005").rstrip("/")
    INJECTION_THRESHOLD: float = float(os.getenv("INJECTION_THRESHOLD", "0.7"))
    RETRIEVAL_SCORE_THRESHOLD: float = float(os.getenv("RETRIEVAL_SCORE_THRESHOLD", "0.5"))

    # Query Rewriter (optional): set QUERY_REWRITING_ENABLED=false to disable
    QUERY_REWRITING_ENABLED: bool = (
        os.getenv("QUERY_REWRITING_ENABLED", "true").strip().lower() in ("true", "1", "yes")
    )
    QUERY_REWRITER_PROVIDER: str = (
        (os.getenv("QUERY_REWRITER_PROVIDER", "llm") or "llm").strip().lower()
    )
    QUERY_REWRITER_MAX_WORDS: int = int(os.getenv("QUERY_REWRITER_MAX_WORDS", "10"))

    # LangChain (optional): feature-flagged orchestration enhancements
    LANGCHAIN_ENABLED: bool = (
        os.getenv("LANGCHAIN_ENABLED", "false").strip().lower() in ("true", "1", "yes")
    )
    MULTIQUERY_ENABLED: bool = (
        os.getenv("MULTIQUERY_ENABLED", "true").strip().lower() in ("true", "1", "yes")
    )
    MULTIQUERY_N: int = int(os.getenv("MULTIQUERY_N", "4"))
    # Candidate depth for LangChain retrieval (pre-rerank). Defaults to VECTOR_SEARCH_TOP_K.
    LANGCHAIN_RETRIEVER_TOP_K: int = int(
        os.getenv("LANGCHAIN_RETRIEVER_TOP_K", str(int(os.getenv("VECTOR_SEARCH_TOP_K", "20"))))
    )

    # LangSmith tracing (optional). LangChain primarily uses LANGCHAIN_* env vars, but we
    # also support a simple boolean to make it easy to toggle in this repo.
    LANGSMITH_TRACING: bool = (
        os.getenv("LANGSMITH_TRACING", "false").strip().lower() in ("true", "1", "yes")
    )


settings = Settings()
