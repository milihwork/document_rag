"""Abstract base for vector store backends."""

from abc import ABC, abstractmethod
from typing import Any


class VectorStore(ABC):
    """Abstract vector store: ensure collection, search, upsert."""

    @abstractmethod
    def ensure_collection(self) -> None:
        """Create table/collection if it does not exist."""
        ...

    @abstractmethod
    def search(
        self, query_vector: list[float], top_k: int | None = None
    ) -> list[dict[str, Any]]:
        """Search for relevant chunks. Returns list of dicts with 'text' and 'source'."""
        ...

    @abstractmethod
    def upsert(self, points: list[dict[str, Any]]) -> None:
        """Upsert points. Each point: {id, vector, payload: {text, source}}."""
        ...
