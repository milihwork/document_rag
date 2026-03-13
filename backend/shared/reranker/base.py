"""Abstract base for reranker backends."""

from abc import ABC, abstractmethod


class BaseReranker(ABC):
    """Abstract reranker: query + documents -> top_k ranked documents."""

    @abstractmethod
    def rerank(self, query: str, documents: list[str], top_k: int = 3) -> list[str]:
        """
        Rerank documents based on relevance to the query.

        Parameters:
        - query: user query
        - documents: list of retrieved document chunks
        - top_k: number of documents to return

        Returns:
        - list of top_k ranked documents
        """
        ...
