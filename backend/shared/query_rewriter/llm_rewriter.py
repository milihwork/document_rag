"""LLM-based query rewriting for improved retrieval."""

import logging
import time

from .base import BaseQueryRewriter

logger = logging.getLogger(__name__)

REWRITER_PROMPT = """Rewrite the following user query to improve document retrieval.

Rules:
- Keep the meaning of the query
- Expand abbreviations if needed
- Make the query clearer and more descriptive
- Do not answer the question
- Return only the rewritten query

User query:
{query}"""


class LLMQueryRewriter(BaseQueryRewriter):
    """Rewrite queries using LLM for better retrieval."""

    def __init__(self, llm_backend, max_words: int = 10):
        """
        Initialize the LLM query rewriter.

        Parameters:
        - llm_backend: LLM backend instance with complete() method
        - max_words: skip rewriting if query has more than this many words
        """
        self._llm = llm_backend
        self._max_words = max_words

    def rewrite(self, query: str) -> str:
        """Rewrite the query for better retrieval."""
        if len(query.split()) > self._max_words:
            logger.debug(
                "Query has >%d words, skipping rewrite: %s",
                self._max_words,
                query[:80],
            )
            return query

        start = time.perf_counter()
        prompt = REWRITER_PROMPT.format(query=query)

        try:
            rewritten = self._llm.complete(prompt, n_predict=100, temperature=0.1)
            rewritten = rewritten.strip()

            if not rewritten:
                logger.warning("Empty rewrite result, using original query")
                return query

            elapsed = (time.perf_counter() - start) * 1000
            logger.info(
                "Query rewritten in %.0fms: %r -> %r",
                elapsed,
                query[:50],
                rewritten[:50],
            )
            return rewritten

        except Exception as e:
            logger.error("Query rewriting failed: %s", e)
            return query
