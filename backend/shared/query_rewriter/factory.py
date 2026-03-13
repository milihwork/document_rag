"""Query rewriter factory: select provider from config."""

import os

from .llm_rewriter import LLMQueryRewriter

_rewriter_instance = None


def get_query_rewriter(llm_backend, max_words: int | None = None):
    """
    Return the query rewriter instance for the configured provider.

    Parameters:
    - llm_backend: LLM backend instance (required for LLM provider)
    - max_words: override for QUERY_REWRITER_MAX_WORDS setting
    """
    global _rewriter_instance
    if _rewriter_instance is None:
        provider = (os.getenv("QUERY_REWRITER_PROVIDER", "llm") or "llm").strip().lower()
        if max_words is None:
            max_words = int(os.getenv("QUERY_REWRITER_MAX_WORDS", "10"))

        if provider == "llm":
            _rewriter_instance = LLMQueryRewriter(llm_backend, max_words=max_words)
        else:
            raise ValueError(
                f"Unsupported query rewriter provider: {provider}. Available: llm"
            )
    return _rewriter_instance
