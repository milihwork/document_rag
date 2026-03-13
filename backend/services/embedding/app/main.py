"""Embedding service: FastAPI app exposing POST /embed."""

import logging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from shared.contracts import KEY_EMBEDDING, KEY_EMBEDDINGS, KEY_OK, KEY_STATUS, PATH_EMBED, PATH_HEALTH

from .backends import get_backend

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Embedding Service", description="Text to vectors with configurable backend")

_backend = None


def _get_backend():
    global _backend
    if _backend is None:
        _backend = get_backend()
    return _backend


class EmbedRequest(BaseModel):
    """Either text (single) or texts (batch). Exactly one must be set."""

    text: str | None = None
    texts: list[str] | None = None


@app.post(PATH_EMBED)
def embed(request: EmbedRequest):
    """
    Generate embedding(s). Send either {"text": "..."} or {"texts": ["...", "..."]}.
    Returns {"embedding": [...]} or {"embeddings": [[...], [...]]}.
    """
    try:
        if request.text is not None:
            if request.texts is not None:
                raise HTTPException(
                    status_code=400, detail="Provide either 'text' or 'texts', not both"
                )
            vec = _get_backend().embed(request.text)
            return {KEY_EMBEDDING: vec}
        if request.texts is not None:
            if not request.texts:
                raise HTTPException(status_code=400, detail="texts must be non-empty")
            vecs = _get_backend().embed_batch(request.texts)
            return {KEY_EMBEDDINGS: vecs}
        raise HTTPException(status_code=400, detail="Provide either 'text' or 'texts'")
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))


@app.get(PATH_HEALTH)
def health():
    return {KEY_STATUS: KEY_OK}
