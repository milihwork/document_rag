"""Factory functions for ML components."""

import logging

from ..config.settings import settings

logger = logging.getLogger(__name__)

_injection_detector = None
_query_classifier = None
_retrieval_scorer = None
_document_classifier = None


def _get_llm_backend():
    """Get the configured LLM backend."""
    from services.rag.app.backends import get_backend

    return get_backend()


def get_injection_detector():
    """Return the injection detector instance."""
    global _injection_detector
    if _injection_detector is None:
        from .injection_detector import LLMInjectionDetector

        llm = _get_llm_backend()
        _injection_detector = LLMInjectionDetector(llm)
        logger.info("Initialized LLMInjectionDetector")
    return _injection_detector


def get_query_classifier():
    """Return the query classifier instance."""
    global _query_classifier
    if _query_classifier is None:
        from .query_classifier import LLMQueryClassifier

        llm = _get_llm_backend()
        _query_classifier = LLMQueryClassifier(llm)
        logger.info("Initialized LLMQueryClassifier")
    return _query_classifier


def get_retrieval_scorer():
    """Return the retrieval scorer instance."""
    global _retrieval_scorer
    if _retrieval_scorer is None:
        from .retrieval_scorer import LLMRetrievalScorer

        llm = _get_llm_backend()
        _retrieval_scorer = LLMRetrievalScorer(
            llm, threshold=settings.RETRIEVAL_SCORE_THRESHOLD
        )
        logger.info("Initialized LLMRetrievalScorer")
    return _retrieval_scorer


def get_document_classifier():
    """Return the document classifier instance."""
    global _document_classifier
    if _document_classifier is None:
        from .document_classifier import LLMDocumentClassifier

        llm = _get_llm_backend()
        _document_classifier = LLMDocumentClassifier(llm)
        logger.info("Initialized LLMDocumentClassifier")
    return _document_classifier


def reset_instances():
    """Reset all cached instances (for testing)."""
    global _injection_detector, _query_classifier, _retrieval_scorer, _document_classifier
    _injection_detector = None
    _query_classifier = None
    _retrieval_scorer = None
    _document_classifier = None
