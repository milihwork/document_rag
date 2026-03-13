"""Abstract base classes for ML components."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class InjectionResult:
    """Result from injection detection."""

    is_injection: bool
    confidence: float
    reason: str


@dataclass
class IntentResult:
    """Result from query classification."""

    intent: str
    confidence: float


@dataclass
class RetrievalScoreResult:
    """Result from retrieval scoring."""

    score: float
    sufficient: bool
    reason: str


@dataclass
class DocumentClassResult:
    """Result from document classification."""

    category: str
    confidence: float


class BaseInjectionDetector(ABC):
    """Abstract base for injection detection."""

    @abstractmethod
    def detect(self, query: str) -> InjectionResult:
        """Detect if the query is a prompt injection attempt."""
        ...


class BaseQueryClassifier(ABC):
    """Abstract base for query classification."""

    @abstractmethod
    def classify(self, query: str) -> IntentResult:
        """Classify the intent of the query."""
        ...


class BaseRetrievalScorer(ABC):
    """Abstract base for retrieval quality scoring."""

    @abstractmethod
    def score(self, query: str, chunks: list[dict]) -> RetrievalScoreResult:
        """Score the quality of retrieved chunks for the given query."""
        ...


class BaseDocumentClassifier(ABC):
    """Abstract base for document classification."""

    @abstractmethod
    def classify(self, text_sample: str) -> DocumentClassResult:
        """Classify a document based on a text sample."""
        ...
