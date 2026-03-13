"""Tests for reranker module (BGE backend and factory)."""

import os

import pytest

# Skip entire module if sentence_transformers not available or broken (e.g. numpy crash on some Macs)
pytest.importorskip("sentence_transformers")

from shared.reranker.bge_reranker import BGEReranker
from shared.reranker.factory import get_reranker


def test_factory_returns_bge_reranker_by_default():
    """With default or RERANKER_PROVIDER=bge, get_reranker returns BGEReranker."""
    import shared.reranker.factory as factory_module

    factory_module._reranker_instance = None
    try:
        reranker = get_reranker()
        assert isinstance(reranker, BGEReranker)
    finally:
        factory_module._reranker_instance = None


def test_factory_raises_for_unknown_provider():
    """Unknown RERANKER_PROVIDER raises ValueError."""
    import shared.reranker.factory as factory_module

    factory_module._reranker_instance = None
    orig = os.environ.get("RERANKER_PROVIDER")
    os.environ["RERANKER_PROVIDER"] = "unknown_provider"
    try:
        with pytest.raises(ValueError, match="Unsupported reranker provider"):
            get_reranker()
    finally:
        factory_module._reranker_instance = None
        if orig is None:
            os.environ.pop("RERANKER_PROVIDER", None)
        else:
            os.environ["RERANKER_PROVIDER"] = orig


def test_bge_reranker_returns_top_k():
    """BGEReranker.rerank returns a list of length top_k from the input documents."""
    reranker = BGEReranker()
    documents = [
        "The quick brown fox jumps over the lazy dog.",
        "Python is a programming language.",
        "Machine learning models can be used for classification.",
    ]
    result = reranker.rerank("What is Python?", documents, top_k=2)
    assert len(result) == 2
    assert all(doc in documents for doc in result)
    # Python-related doc should rank first
    assert result[0] == "Python is a programming language."


def test_bge_reranker_empty_documents():
    """BGEReranker.rerank with empty list returns empty list."""
    reranker = BGEReranker()
    result = reranker.rerank("query", [], top_k=3)
    assert result == []


def test_bge_reranker_top_k_larger_than_docs():
    """When top_k exceeds document count, returns all documents."""
    reranker = BGEReranker()
    documents = ["First.", "Second."]
    result = reranker.rerank("query", documents, top_k=10)
    assert len(result) == 2
    assert set(result) == set(documents)
