"""Qdrant vector store backend."""

import logging
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from shared.contracts import (
    KEY_ID,
    KEY_PAYLOAD,
    KEY_SOURCE,
    KEY_TEXT,
    KEY_VECTOR,
    SOURCE_UNKNOWN,
)

from ..config.settings import settings
from . import register
from .base import VectorStore

logger = logging.getLogger(__name__)

_client: QdrantClient | None = None


def _get_client() -> QdrantClient:
    global _client
    if _client is None:
        logger.info("Connecting to Qdrant at %s:%s", settings.QDRANT_HOST, settings.QDRANT_PORT)
        _client = QdrantClient(settings.QDRANT_HOST, port=settings.QDRANT_PORT)
    return _client


@register("qdrant")
class QdrantBackend(VectorStore):
    """Vector search and upsert via Qdrant."""

    def ensure_collection(self) -> None:
        """Create collection if it does not exist."""
        client = _get_client()
        existing = [c.name for c in client.get_collections().collections]
        if settings.COLLECTION_NAME not in existing:
            client.create_collection(
                collection_name=settings.COLLECTION_NAME,
                vectors_config=VectorParams(size=settings.VECTOR_SIZE, distance=Distance.COSINE),
            )
            logger.info("Created collection: %s", settings.COLLECTION_NAME)

    def search(self, query_vector: list[float], top_k: int | None = None) -> list[dict[str, Any]]:
        """Search for relevant chunks. Returns list of dicts with 'text' and 'source'."""
        k = top_k or settings.TOP_K
        client = _get_client()
        self.ensure_collection()

        results = client.query_points(
            collection_name=settings.COLLECTION_NAME,
            query=query_vector,
            limit=k,
        )

        chunks = []
        for point in results.points:
            chunks.append(
                {
                    KEY_TEXT: point.payload.get(KEY_TEXT, ""),
                    KEY_SOURCE: point.payload.get(KEY_SOURCE, SOURCE_UNKNOWN),
                }
            )

        logger.info("Retrieved %d chunks for query (top_k=%d)", len(chunks), k)
        return chunks

    def upsert(self, points: list[dict[str, Any]]) -> None:
        """
        Upsert points. Each point: {id: str, vector: list[float], payload: {text, source}}.
        """
        client = _get_client()
        self.ensure_collection()

        structs = [
            PointStruct(
                id=p[KEY_ID],
                vector=p[KEY_VECTOR],
                payload=p.get(KEY_PAYLOAD, {}),
            )
            for p in points
        ]
        client.upsert(collection_name=settings.COLLECTION_NAME, points=structs)
        logger.info("Upserted %d points", len(structs))
