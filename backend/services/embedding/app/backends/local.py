"""Local embedding backend using sentence-transformers."""

import logging

from sentence_transformers import SentenceTransformer

from ..config.settings import settings
from . import register
from .base import EmbeddingBackend

logger = logging.getLogger(__name__)


@register("local")
class LocalEmbeddingBackend(EmbeddingBackend):
    """Generate embeddings with a local sentence-transformers model."""

    def __init__(self):
        self._model: SentenceTransformer | None = None

    def _get_model(self) -> SentenceTransformer:
        if self._model is None:
            logger.info("Loading embedding model: %s", settings.EMBEDDING_MODEL)
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
