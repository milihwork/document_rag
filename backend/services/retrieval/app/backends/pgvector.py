"""pgvector vector store backend."""

import logging
from typing import Any
from uuid import UUID

import numpy as np
import psycopg2
from pgvector.psycopg2 import register_vector

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

_conn = None


def _get_conn():
    global _conn
    if _conn is None or _conn.closed:
        logger.info("Connecting to PostgreSQL for pgvector")
        _conn = psycopg2.connect(settings.DATABASE_URL)
        _conn.autocommit = True
        register_vector(_conn)
    return _conn


@register("pgvector")
class PgVectorBackend(VectorStore):
    """Vector search and upsert via PostgreSQL pgvector extension."""

    def ensure_collection(self) -> None:
        """Create table and extension if they do not exist."""
        conn = _get_conn()
        with conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS {table} (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    source TEXT NOT NULL DEFAULT 'unknown',
                    embedding vector({size})
                )
                """.format(
                    table=settings.PGVECTOR_TABLE_NAME,
                    size=settings.VECTOR_SIZE,
                ),
            )
            # Optional: create ivfflat index for faster search after table has data.
            # For empty tables, skip or run after first upsert.
            cur.execute(
                "SELECT COUNT(*) FROM {table}".format(table=settings.PGVECTOR_TABLE_NAME)
            )
            if cur.fetchone()[0] > 0:
                cur.execute(
                    """
                    CREATE INDEX IF NOT EXISTS {table}_embedding_idx
                    ON {table} USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = 100)
                    """.format(table=settings.PGVECTOR_TABLE_NAME)
                )
        logger.info("Ensured table and extension: %s", settings.PGVECTOR_TABLE_NAME)

    def search(
        self, query_vector: list[float], top_k: int | None = None
    ) -> list[dict[str, Any]]:
        """Search for relevant chunks. Returns list of dicts with 'text' and 'source'."""
        k = top_k or settings.TOP_K
        conn = _get_conn()
        self.ensure_collection()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT content, source FROM {table}
                ORDER BY embedding <=> %s
                LIMIT %s
                """.format(table=settings.PGVECTOR_TABLE_NAME),
                (np.array(query_vector, dtype=np.float32), k),
            )
            rows = cur.fetchall()
        chunks = [{KEY_TEXT: row[0], KEY_SOURCE: row[1] or SOURCE_UNKNOWN} for row in rows]
        logger.info("Retrieved %d chunks for query (top_k=%d)", len(chunks), k)
        return chunks

    def upsert(self, points: list[dict[str, Any]]) -> None:
        """
        Upsert points. Each point: {id, vector, payload: {text, source}}.
        """
        conn = _get_conn()
        self.ensure_collection()
        table = settings.PGVECTOR_TABLE_NAME
        with conn.cursor() as cur:
            for p in points:
                pid = p.get(KEY_ID)
                if isinstance(pid, UUID):
                    pid = str(pid)
                payload = p.get(KEY_PAYLOAD) or {}
                content = payload.get(KEY_TEXT, "")
                source = payload.get(KEY_SOURCE, SOURCE_UNKNOWN)
                vector = p.get(KEY_VECTOR, [])
                vec_arr = np.array(vector, dtype=np.float32)
                cur.execute(
                    """
                    INSERT INTO {table} (id, content, source, embedding)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        content = EXCLUDED.content,
                        source = EXCLUDED.source,
                        embedding = EXCLUDED.embedding
                    """.format(table=table),
                    (pid, content, source, vec_arr),
                )
        logger.info("Upserted %d points", len(points))
