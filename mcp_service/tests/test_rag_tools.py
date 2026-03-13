"""Unit tests for RAG tool implementations (mocked HTTP)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from mcp_service.rag_tools import (
    ask_rag_impl,
    ingest_document_impl,
    search_documents_impl,
)


@pytest.mark.asyncio
async def test_search_documents_impl_calls_embed_then_search(
    mock_embedding, mock_chunks
):
    """search_documents_impl should call embed then search with correct payloads."""
    resp1 = MagicMock()
    resp1.raise_for_status = MagicMock()
    resp1.json.return_value = {"embedding": mock_embedding}
    resp2 = MagicMock()
    resp2.raise_for_status = MagicMock()
    resp2.json.return_value = {"chunks": mock_chunks}
    mock_post = AsyncMock(side_effect=[resp1, resp2])

    with patch("mcp_service.rag_tools.httpx.AsyncClient") as client_cls:
        client_cls.return_value.__aenter__.return_value.post = mock_post
        client_cls.return_value.__aexit__.return_value = None

        result = await search_documents_impl("test query")

    assert result == mock_chunks
    assert mock_post.call_count == 2
    first_call = mock_post.call_args_list[0]
    second_call = mock_post.call_args_list[1]
    assert "embed" in first_call[0][0]
    assert first_call[1]["json"] == {"text": "test query"}
    assert "search" in second_call[0][0]
    assert second_call[1]["json"]["query_vector"] == mock_embedding
    assert "top_k" in second_call[1]["json"]


@pytest.mark.asyncio
async def test_ask_rag_impl_calls_rag_service(mock_rag_response):
    """ask_rag_impl should POST to RAG /ask and return parsed response."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = mock_rag_response
    mock_post = AsyncMock(return_value=mock_resp)

    with patch("mcp_service.rag_tools.httpx.AsyncClient") as client_cls:
        client_cls.return_value.__aenter__.return_value.post = mock_post
        client_cls.return_value.__aexit__.return_value = None

        result = await ask_rag_impl("What is RAG?")

    assert result == mock_rag_response
    assert result["answer"] == "RAG is Retrieval Augmented Generation."
    assert result["sources"] == ["doc1.pdf"]
    mock_post.assert_called_once()
    call_url = mock_post.call_args[0][0]
    assert "ask" in call_url
    assert mock_post.call_args[1]["json"] == {"question": "What is RAG?"}


@pytest.mark.asyncio
async def test_ingest_document_impl_calls_ingestion(mock_ingest_response):
    """ingest_document_impl should POST to /ingest/text with text and source."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = mock_ingest_response
    mock_post = AsyncMock(return_value=mock_resp)

    with patch("mcp_service.rag_tools.httpx.AsyncClient") as client_cls:
        client_cls.return_value.__aenter__.return_value.post = mock_post
        client_cls.return_value.__aexit__.return_value = None

        result = await ingest_document_impl("Some document text.", source="my-doc")

    assert result == mock_ingest_response
    assert result["chunks_inserted"] == 2
    mock_post.assert_called_once()
    call_url = mock_post.call_args[0][0]
    assert "ingest/text" in call_url
    assert mock_post.call_args[1]["json"] == {
        "text": "Some document text.",
        "source": "my-doc",
    }


@pytest.mark.asyncio
async def test_ingest_document_impl_default_source(mock_ingest_response):
    """ingest_document_impl should use 'mcp' as default source."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = mock_ingest_response
    mock_post = AsyncMock(return_value=mock_resp)

    with patch("mcp_service.rag_tools.httpx.AsyncClient") as client_cls:
        client_cls.return_value.__aenter__.return_value.post = mock_post
        client_cls.return_value.__aexit__.return_value = None

        await ingest_document_impl("Text only.")

    assert mock_post.call_args[1]["json"]["source"] == "mcp"
