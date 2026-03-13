"""Abstract base for embedding backends."""

from abc import ABC, abstractmethod


class EmbeddingBackend(ABC):
    """Abstract embedding backend: single and batch embed."""

    @abstractmethod
    def embed(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        ...

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        ...
