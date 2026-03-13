"""Pytest configuration for MCP service tests."""

import pytest


@pytest.fixture
def mock_embedding():
    """Fake embedding vector (e.g. 384-dim for BGE-small)."""
    return [0.1] * 384


@pytest.fixture
def mock_chunks():
    """Sample chunks returned by retrieval."""
    return [
        {"text": "First chunk about RAG.", "source": "doc1.pdf"},
        {"text": "Second chunk about vectors.", "source": "doc1.pdf"},
    ]


@pytest.fixture
def mock_rag_response():
    """Sample RAG /ask response."""
    return {
        "question": "What is RAG?",
        "answer": "RAG is Retrieval Augmented Generation.",
        "sources": ["doc1.pdf"],
    }


@pytest.fixture
def mock_ingest_response():
    """Sample ingestion response."""
    return {
        "status": "success",
        "chunks_inserted": 2,
        "document": "mcp",
    }
