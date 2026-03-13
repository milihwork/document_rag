"""Pytest configuration and fixtures."""

import pytest


@pytest.fixture
def sample_text() -> str:
    """Sample text for embedding tests."""
    return "RAG stands for Retrieval Augmented Generation."
