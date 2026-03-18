"""Local embedding backend using sentence-transformers (Hugging Face)."""

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

            if settings.EMBEDDING_DEVICE:
                self._model = SentenceTransformer(
                    settings.EMBEDDING_MODEL, device=settings.EMBEDDING_DEVICE
                )
            else:
                self._model = SentenceTransformer(settings.EMBEDDING_MODEL)
        return self._model

    def embed(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        model = self._get_model()
        return model.encode(
            text,
            normalize_embeddings=settings.EMBEDDING_NORMALIZE,
        ).tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        model = self._get_model()
        kwargs: dict[str, Any] = {
            "normalize_embeddings": settings.EMBEDDING_NORMALIZE,
            "batch_size": settings.EMBEDDING_BATCH_SIZE,
        }
        if settings.EMBEDDING_MAX_LENGTH is not None:
            kwargs["max_length"] = settings.EMBEDDING_MAX_LENGTH
        return model.encode(texts, **kwargs).tolist()


@register("huggingface")
class HuggingFaceEmbeddingBackend(LocalEmbeddingBackend):
    """Alias of the local sentence-transformers backend with explicit naming."""
