"""Local embedding backend using sentence-transformers."""

import logging
from typing import Any

from ..config.settings import settings
from . import register
from .base import EmbeddingBackend

logger = logging.getLogger(__name__)


@register("local")
class LocalEmbeddingBackend(EmbeddingBackend):
    """Generate embeddings with a local sentence-transformers model."""

    def __init__(self):
        self._model: Any | None = None

    def _get_model(self):
        if self._model is None:
            logger.info("Loading embedding model: %s", settings.EMBEDDING_MODEL)
            # Lazy import to avoid importing heavy deps at module import time.
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(settings.EMBEDDING_MODEL)
        return self._model

    def embed(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        model = self._get_model()
        return model.encode(text).tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        model = self._get_model()
        return model.encode(texts).tolist()
