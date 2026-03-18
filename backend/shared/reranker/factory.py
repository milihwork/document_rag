"""Reranker factory: select provider from config."""

import os

_reranker_instance = None


def get_reranker():
    """Return the reranker instance for the configured RERANKER_PROVIDER."""
    global _reranker_instance
    if _reranker_instance is None:
        provider = (os.getenv("RERANKER_PROVIDER", "bge") or "").strip().lower()
        if provider == "bge":
            # Lazy import so importing shared modules doesn't pull in heavy deps
            # (sentence-transformers, torch, numpy) unless the reranker is used.
            from .bge_reranker import BGEReranker

            _reranker_instance = BGEReranker()
        else:
            raise ValueError(
                f"Unsupported reranker provider: {provider}. Available: bge"
            )
    return _reranker_instance
