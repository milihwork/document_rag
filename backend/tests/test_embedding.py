"""Tests for embedding service (local backend)."""

from services.embedding.app.backends.local import LocalEmbeddingBackend


def test_embed_returns_list_of_floats():
    """Embedding should return a list of floats."""
    backend = LocalEmbeddingBackend()
    result = backend.embed("test")
    assert isinstance(result, list)
    assert all(isinstance(x, float) for x in result)
    assert len(result) == 384  # BGE-small dimension


def test_embed_batch_returns_list_of_embeddings():
    """Batch embedding should return list of embeddings."""
    backend = LocalEmbeddingBackend()
    texts = ["First sentence.", "Second sentence."]
    result = backend.embed_batch(texts)
    assert len(result) == 2
    assert len(result[0]) == 384
    assert len(result[1]) == 384
