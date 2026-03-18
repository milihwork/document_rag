"""Tests for embedding service (local backend)."""

from services.embedding.app.backends.local import LocalEmbeddingBackend


def test_embed_returns_list_of_floats(monkeypatch):
    """Embedding should return a list of floats."""
    backend = LocalEmbeddingBackend()
    # Avoid loading sentence-transformers/numpy during tests.
    class FakeVec:
        def tolist(self):
            return [0.0] * 384

    monkeypatch.setattr(
        backend,
        "_get_model",
        lambda: type(
            "FakeModel",
            (),
            {"encode": staticmethod(lambda _text: FakeVec())},
        )(),
    )
    result = backend.embed("test")
    assert isinstance(result, list)
    assert all(isinstance(x, float) for x in result)
    assert len(result) == 384  # BGE-small dimension


def test_embed_batch_returns_list_of_embeddings(monkeypatch):
    """Batch embedding should return list of embeddings."""
    backend = LocalEmbeddingBackend()
    class FakeMat:
        def __init__(self, n: int):
            self._n = n

        def tolist(self):
            return [[0.0] * 384 for _ in range(self._n)]

    monkeypatch.setattr(
        backend,
        "_get_model",
        lambda: type(
            "FakeModel",
            (),
            {"encode": staticmethod(lambda texts: FakeMat(len(texts)))},
        )(),
    )
    texts = ["First sentence.", "Second sentence."]
    result = backend.embed_batch(texts)
    assert len(result) == 2
    assert len(result[0]) == 384
    assert len(result[1]) == 384
