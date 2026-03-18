"""Smoke tests for the LangChain-enabled retrieval path.

This test does not require the Embedding/Retrieval services to be running; it
monkeypatches the RAG service's internal functions to keep the test fast and
deterministic.
"""

import pytest

from shared.contracts import KEY_SOURCE, KEY_TEXT


@pytest.mark.asyncio
async def test_langchain_multiquery_retrieval_calls_embed_multiple_times(monkeypatch):
    pytest.importorskip("langchain_core")
    from services.rag.app import main as rag_main

    # Force the LangChain path configuration for this test.
    rag_main.settings.LANGCHAIN_ENABLED = True
    rag_main.settings.MULTIQUERY_ENABLED = True
    rag_main.settings.MULTIQUERY_N = 3
    rag_main.settings.RERANKER_PROVIDER = "none"
    rag_main.settings.RERANK_TOP_K = 3
    rag_main.settings.LANGCHAIN_RETRIEVER_TOP_K = 10

    embed_calls = []
    search_calls = []

    async def fake_embed(text: str):
        embed_calls.append(text)
        # Encode call index into vector so fake_search can vary results.
        return [float(len(embed_calls))]

    async def fake_search(query_vector, top_k=None):
        search_calls.append((query_vector, top_k))
        idx = int(query_vector[0])
        return [
            {KEY_TEXT: f"chunk_{idx}", KEY_SOURCE: f"doc_{idx}.pdf"},
        ]

    class FakeBackend:
        def complete(self, prompt: str, **_kwargs):
            # Match the prompt contract: one query per line, no numbering.
            return "query_variant_a\nquery_variant_b\nquery_variant_c\n"

    monkeypatch.setattr(rag_main, "_embed", fake_embed)
    monkeypatch.setattr(rag_main, "_search", fake_search)
    monkeypatch.setattr(rag_main, "_get_llm", lambda: FakeBackend())

    chunks = await rag_main._langchain_retrieve(
        question="What is the warranty policy?",
        retrieval_query="warranty policy",
    )

    # include_original=True + 3 generated variants => at least 4 embeds/searches
    assert len(embed_calls) >= 4
    assert len(search_calls) >= 4
    assert len(chunks) > 0
    assert all(KEY_TEXT in c and KEY_SOURCE in c for c in chunks)

