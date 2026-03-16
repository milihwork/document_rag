"""Retrieval service: FastAPI app exposing /search, /upsert, /ensure_collection."""

import logging

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from shared.contracts import (
    KEY_CHUNKS,
    KEY_COUNT,
    KEY_OK,
    KEY_STATUS,
    PATH_ENSURE_COLLECTION,
    PATH_HEALTH,
    PATH_SEARCH,
    PATH_UPSERT,
)

from .backends import get_backend

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Retrieval Service",
    description="Vector search and upsert with configurable backend",
)

_backend = None


def _get_backend():
    global _backend
    if _backend is None:
        _backend = get_backend()
    return _backend


class SearchRequest(BaseModel):
    query_vector: list[float]
    top_k: int | None = None


class PointPayload(BaseModel):
    text: str
    source: str


class Point(BaseModel):
    id: str
    vector: list[float]
    payload: PointPayload


class UpsertRequest(BaseModel):
    points: list[Point]


@app.get("/")
def root():
    """Redirect root to API docs."""
    return RedirectResponse(url="/docs", status_code=302)


@app.post(PATH_SEARCH)
def search(request: SearchRequest):
    """Search for chunks by query vector. Returns {chunks: [{text, source}, ...]}."""
    try:
        chunks = _get_backend().search(request.query_vector, request.top_k)
        return {KEY_CHUNKS: chunks}
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))


@app.post(PATH_UPSERT)
def upsert(request: UpsertRequest):
    """Upsert points. Ensures collection exists. Payload must include text and source."""
    try:
        points_dict = [p.model_dump() for p in request.points]
        _get_backend().upsert(points_dict)
        return {KEY_STATUS: KEY_OK, KEY_COUNT: len(points_dict)}
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))


@app.post(PATH_ENSURE_COLLECTION)
def ensure_collection():
    """Ensure the vector collection exists (idempotent)."""
    try:
        _get_backend().ensure_collection()
        return {KEY_STATUS: KEY_OK}
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))


@app.get(PATH_HEALTH)
def health():
    return {KEY_STATUS: KEY_OK}
