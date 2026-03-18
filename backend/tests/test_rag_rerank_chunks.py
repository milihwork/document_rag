"""Tests for RAG service _rerank_chunks helper."""

from shared.contracts import KEY_SOURCE, KEY_TEXT


def test_rerank_chunks_returns_chunks_in_reranked_order(monkeypatch):
    """_rerank_chunks uses get_reranker().rerank and maps results back to chunks."""
    from services.rag.app import main as rag_main

    class FakeReranker:
        def rerank(self, query: str, documents: list[str], top_k: int = 3) -> list[str]:
            # Return reverse order to assert order is applied
            return list(reversed(documents))[:top_k]

    monkeypatch.setattr(rag_main, "get_reranker", lambda: FakeReranker())
    monkeypatch.setattr(rag_main.settings, "RERANK_TOP_K", 3)

    chunks = [
        {KEY_TEXT: "first", KEY_SOURCE: "a.pdf"},
        {KEY_TEXT: "second", KEY_SOURCE: "b.pdf"},
        {KEY_TEXT: "third", KEY_SOURCE: "c.pdf"},
    ]
    result = rag_main._rerank_chunks("query", chunks, top_k=2)

    assert len(result) == 2
    assert result[0][KEY_TEXT] == "third" and result[0][KEY_SOURCE] == "c.pdf"
    assert result[1][KEY_TEXT] == "second" and result[1][KEY_SOURCE] == "b.pdf"


def test_rerank_chunks_empty_returns_empty():
    """_rerank_chunks with no chunks returns []."""
    from services.rag.app import main as rag_main

    result = rag_main._rerank_chunks("query", [], top_k=3)
    assert result == []
