"""Abstract base for safeguard backends."""

from abc import ABC, abstractmethod


class BaseSafeguard(ABC):
    """Abstract safeguard: validate user input and LLM output."""

    @abstractmethod
    def validate_input(self, query: str) -> bool:
        """
        Return True if the query is allowed, False if it should be blocked.

        Parameters:
        - query: user question or prompt

        Returns:
        - True if allowed, False if blocked (e.g. prompt injection or unsafe topic)
        """
        ...

    @abstractmethod
    def validate_output(self, response: str) -> bool:
        """
        Return True if the response is allowed, False if it should be blocked.

        Parameters:
        - response: generated answer from the LLM

        Returns:
        - True if allowed, False if blocked (e.g. leaked confidential content)
        """
        ...
