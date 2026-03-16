"""Ingestion: PDF upload, chunk, embed via Embedding API, upsert via Retrieval API."""

import logging
import os
import tempfile
import uuid

import httpx
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

# Use shared package (run with PYTHONPATH including backend root)
from shared.chunker import chunk_text
from shared.contracts import (
    KEY_CATEGORY,
    KEY_CATEGORY_CONFIDENCE,
    KEY_CHUNKS_INSERTED,
    KEY_CONFIDENCE,
    KEY_DOCUMENT,
    KEY_EMBEDDINGS,
    KEY_ID,
    KEY_OK,
    KEY_PAYLOAD,
    KEY_POINTS,
    KEY_SOURCE,
    KEY_STATUS,
    KEY_SUCCESS,
    KEY_TEXT,
    KEY_TEXT_SAMPLE,
    KEY_TEXTS,
    KEY_VECTOR,
    PATH_CLASSIFY,
    PATH_EMBED,
    PATH_HEALTH,
    PATH_INGEST,
    PATH_INGEST_TEXT,
    PATH_UPSERT,
    SOURCE_UNKNOWN,
)
from shared.pdf_parser import extract_text

from .config.settings import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Ingestion Service",
    description="PDF to vector store via Embedding and Retrieval services",
)


async def _embed_batch(texts: list[str]) -> list[list[float]]:
    """Call Embedding service for batch embeddings."""
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(
            f"{settings.EMBEDDING_URL}{PATH_EMBED}",
            json={KEY_TEXTS: texts},
        )
        r.raise_for_status()
        data = r.json()
        return data[KEY_EMBEDDINGS]


async def _upsert(points: list[dict], category: str | None = None) -> None:
    """Call Retrieval service to upsert points."""
    payload = {
        KEY_POINTS: [
            {
                KEY_ID: p[KEY_ID],
                KEY_VECTOR: p[KEY_VECTOR],
                KEY_PAYLOAD: {
                    KEY_TEXT: p[KEY_TEXT],
                    KEY_SOURCE: p[KEY_SOURCE],
                    **({"category": category} if category else {}),
                },
            }
            for p in points
        ]
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(f"{settings.RETRIEVAL_URL}{PATH_UPSERT}", json=payload)
        r.raise_for_status()


async def _classify_document(text_sample: str) -> dict:
    """Call ML service to classify document. Returns {category, confidence}."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                f"{settings.ML_SERVICE_URL}{PATH_CLASSIFY}",
                json={KEY_TEXT_SAMPLE: text_sample[:2000]},
            )
            r.raise_for_status()
            return r.json()
    except httpx.HTTPError as e:
        logger.warning("Document classification failed: %s", e)
        return {KEY_CATEGORY: "other", KEY_CONFIDENCE: 0.0}


class IngestTextRequest(BaseModel):
    """Request body for text ingestion."""

    text: str
    source: str = "mcp"


@app.get("/")
def root():
    """Redirect root to API docs."""
    return RedirectResponse(url="/docs", status_code=302)


@app.post(PATH_INGEST_TEXT)
async def ingest_text(request: IngestTextRequest):
    """Ingest raw text: chunk, embed, upsert. Returns status and chunk count."""
    source = request.source or "mcp"
    logger.info("Ingest text request: source=%s, len=%d", source, len(request.text))

    # Classify document if enabled
    category = None
    category_confidence = None
    if settings.DOCUMENT_CLASSIFICATION_ENABLED:
        class_result = await _classify_document(request.text)
        category = class_result.get(KEY_CATEGORY, "other")
        category_confidence = class_result.get(KEY_CONFIDENCE, 0.0)
        logger.info("Document classified as: %s (confidence=%.2f)", category, category_confidence)

    chunks = chunk_text(request.text, max_chars=settings.CHUNK_SIZE)

    if not chunks:
        logger.warning("No chunks from text (source=%s)", source)
        return {
            KEY_STATUS: KEY_SUCCESS,
            KEY_CHUNKS_INSERTED: 0,
            KEY_DOCUMENT: source,
            KEY_CATEGORY: category,
            KEY_CATEGORY_CONFIDENCE: category_confidence,
        }

    embeddings = await _embed_batch(chunks)

    points = [
        {
            KEY_ID: str(uuid.uuid4()),
            KEY_VECTOR: emb,
            KEY_TEXT: chunk,
            KEY_SOURCE: source,
        }
        for chunk, emb in zip(chunks, embeddings, strict=True)
    ]

    await _upsert(points, category=category)

    logger.info(
        "Ingested %d chunks from text (source=%s, category=%s)",
        len(points),
        source,
        category,
    )

    return {
        KEY_STATUS: KEY_SUCCESS,
        KEY_CHUNKS_INSERTED: len(points),
        KEY_DOCUMENT: source,
        KEY_CATEGORY: category,
        KEY_CATEGORY_CONFIDENCE: category_confidence,
    }


@app.post(PATH_INGEST)
async def ingest(file: UploadFile = File(...)):
    """Ingest PDF: extract text, classify, chunk, embed, upsert. Returns status and chunk count."""
    logger.info("Ingest request: %s", file.filename)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(await file.read())
        temp_path = tmp.name

    try:
        text = extract_text(temp_path)

        # Classify document if enabled
        category = None
        category_confidence = None
        if settings.DOCUMENT_CLASSIFICATION_ENABLED:
            class_result = await _classify_document(text)
            category = class_result.get(KEY_CATEGORY, "other")
            category_confidence = class_result.get(KEY_CONFIDENCE, 0.0)
            logger.info(
                "Document classified as: %s (confidence=%.2f)",
                category,
                category_confidence,
            )

        chunks = chunk_text(text, max_chars=settings.CHUNK_SIZE)

        if not chunks:
            logger.warning("No chunks extracted from %s", file.filename)
            return {
                KEY_STATUS: KEY_SUCCESS,
                KEY_CHUNKS_INSERTED: 0,
                KEY_DOCUMENT: file.filename or SOURCE_UNKNOWN,
                KEY_CATEGORY: category,
                KEY_CATEGORY_CONFIDENCE: category_confidence,
            }

        embeddings = await _embed_batch(chunks)

        points = [
            {
                KEY_ID: str(uuid.uuid4()),
                KEY_VECTOR: emb,
                KEY_TEXT: chunk,
                KEY_SOURCE: file.filename or SOURCE_UNKNOWN,
            }
            for chunk, emb in zip(chunks, embeddings, strict=True)
        ]

        await _upsert(points, category=category)

        logger.info(
            "Ingested %d chunks from %s (category=%s)",
            len(points),
            file.filename,
            category,
        )

        return {
            KEY_STATUS: KEY_SUCCESS,
            KEY_CHUNKS_INSERTED: len(points),
            KEY_DOCUMENT: file.filename or SOURCE_UNKNOWN,
            KEY_CATEGORY: category,
            KEY_CATEGORY_CONFIDENCE: category_confidence,
        }
    finally:
        os.remove(temp_path)


@app.get(PATH_HEALTH)
def health():
    return {KEY_STATUS: KEY_OK}
