"""Abstract base for LLM backends."""

from abc import ABC, abstractmethod


class LLM(ABC):
    """Abstract LLM: prompt in, text out."""

    @abstractmethod
    def complete(
        self,
        prompt: str,
        *,
        n_predict: int | None = None,
        temperature: float | None = None,
    ) -> str:
        """Generate text from prompt. Returns generated text."""
        ...
