"""RAG tool implementations: HTTP calls to Embedding, Retrieval, RAG, and Ingestion services."""

import logging

import httpx

from .config import settings

logger = logging.getLogger(__name__)

# Path and payload keys (mirror backend/shared/contracts to avoid backend dependency)
PATH_EMBED = "/embed"
PATH_SEARCH = "/search"
PATH_ASK = "/ask"
PATH_INGEST_TEXT = "/ingest/text"
KEY_TEXT = "text"
KEY_TEXTS = "texts"
KEY_EMBEDDING = "embedding"
KEY_EMBEDDINGS = "embeddings"
KEY_CHUNKS = "chunks"
KEY_QUERY_VECTOR = "query_vector"
KEY_TOP_K = "top_k"
KEY_QUESTION = "question"
KEY_ANSWER = "answer"
KEY_SOURCES = "sources"
KEY_STATUS = "status"
KEY_CHUNKS_INSERTED = "chunks_inserted"
KEY_DOCUMENT = "document"
KEY_SOURCE = "source"


async def search_documents_impl(query: str, top_k: int | None = None) -> list[dict]:
    """
    Run vector similarity search: embed query, then search retrieval service.
    Returns list of {text, source} chunks.
    """
    k = top_k if top_k is not None else settings.TOP_K
    async with httpx.AsyncClient(timeout=30.0) as client:
        embed_resp = await client.post(
            f"{settings.EMBEDDING_SERVICE_URL}{PATH_EMBED}",
            json={KEY_TEXT: query},
        )
        embed_resp.raise_for_status()
        embedding = embed_resp.json()[KEY_EMBEDDING]

        search_resp = await client.post(
            f"{settings.RETRIEVAL_SERVICE_URL}{PATH_SEARCH}",
            json={KEY_QUERY_VECTOR: embedding, KEY_TOP_K: k},
        )
        search_resp.raise_for_status()
        chunks = search_resp.json()[KEY_CHUNKS]

    return chunks


async def ask_rag_impl(question: str) -> dict:
    """
    Full RAG: call RAG service with question, return answer and sources.
    """
    async with httpx.AsyncClient(timeout=90.0) as client:
        resp = await client.post(
            f"{settings.RAG_SERVICE_URL}{PATH_ASK}",
            json={KEY_QUESTION: question},
        )
        resp.raise_for_status()
        return resp.json()


async def ingest_document_impl(document: str, source: str = "mcp") -> dict:
    """
    Ingest document text via Ingestion service (chunk, embed, upsert).
    Returns status, chunks_inserted, and document/source.
    """
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{settings.INGESTION_SERVICE_URL}{PATH_INGEST_TEXT}",
            json={KEY_TEXT: document, KEY_SOURCE: source or "mcp"},
        )
        resp.raise_for_status()
        return resp.json()
