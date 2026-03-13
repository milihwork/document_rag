"""Abstract base for query rewriter backends."""

from abc import ABC, abstractmethod


class BaseQueryRewriter(ABC):
    """Abstract query rewriter: transform user query for better retrieval."""

    @abstractmethod
    def rewrite(self, query: str) -> str:
        """
        Rewrite a user query into a clearer and more descriptive form.

        Parameters:
        - query: original user query

        Returns:
        - rewritten query optimized for vector retrieval
        """
        ...
