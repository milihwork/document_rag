"""LLM-based retrieval quality scoring."""

import json
import logging
import re
import time

from .base import BaseRetrievalScorer, RetrievalScoreResult

logger = logging.getLogger(__name__)

SCORER_PROMPT = """
You are a retrieval quality evaluator. Given a user query and retrieved
document chunks, assess how well the chunks answer or relate to the query.

User Query: {query}

Retrieved Chunks:
{chunks_text}

Evaluate:
1. Relevance: Do the chunks contain information related to the query?
2. Completeness: Do the chunks provide enough information to answer the query?
3. Quality: Is the information clear and useful?

Respond ONLY with valid JSON (no markdown, no explanation):
{{"score": 0.0 to 1.0, "sufficient": true or false,
"reason": "brief explanation"}}

Score guidelines:
- 0.0-0.3: Chunks are irrelevant or unhelpful
- 0.3-0.6: Partially relevant, may need more context
- 0.6-0.8: Good relevance, can likely answer the query
- 0.8-1.0: Excellent match, chunks directly address the query"""


class LLMRetrievalScorer(BaseRetrievalScorer):
    """Score retrieval quality using LLM."""

    def __init__(self, llm_backend, threshold: float = 0.5):
        self._llm = llm_backend
        self._threshold = threshold

    def score(self, query: str, chunks: list[dict]) -> RetrievalScoreResult:
        """Score the quality of retrieved chunks for the given query."""
        start = time.perf_counter()

        if not chunks:
            return RetrievalScoreResult(
                score=0.0,
                sufficient=False,
                reason="No chunks retrieved",
            )

        chunks_text = self._format_chunks(chunks)
        prompt = SCORER_PROMPT.format(query=query, chunks_text=chunks_text)

        try:
            response = self._llm.complete(prompt, n_predict=150, temperature=0.1)
            result = self._parse_response(response)
            elapsed = (time.perf_counter() - start) * 1000
            logger.info(
                "Retrieval scoring: score=%.2f, sufficient=%s in %.0fms",
                result.score,
                result.sufficient,
                elapsed,
            )
            return result
        except Exception as e:
            logger.error("Retrieval scoring failed: %s", e)
            return RetrievalScoreResult(
                score=0.5,
                sufficient=True,
                reason=f"Scoring failed: {e}",
            )

    def _format_chunks(self, chunks: list[dict], max_chars: int = 2000) -> str:
        """Format chunks for the prompt, truncating if necessary."""
        formatted = []
        total_chars = 0

        for i, chunk in enumerate(chunks, 1):
            text = chunk.get("text", "")
            source = chunk.get("source", "unknown")
            entry = f"[{i}] (Source: {source})\n{text}"

            if total_chars + len(entry) > max_chars:
                entry = entry[: max_chars - total_chars] + "..."
                formatted.append(entry)
                break

            formatted.append(entry)
            total_chars += len(entry)

        return "\n\n".join(formatted)

    def _parse_response(self, response: str) -> RetrievalScoreResult:
        """Parse LLM response into RetrievalScoreResult."""
        try:
            json_match = re.search(r"\{[^}]+\}", response)
            if json_match:
                data = json.loads(json_match.group())
                score = float(data.get("score", 0.5))
                sufficient = data.get("sufficient")
                if sufficient is None:
                    sufficient = score >= self._threshold
                return RetrievalScoreResult(
                    score=score,
                    sufficient=bool(sufficient),
                    reason=str(data.get("reason", "")),
                )
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("Failed to parse scoring response: %s", e)

        return RetrievalScoreResult(
            score=0.5,
            sufficient=True,
            reason="Failed to parse LLM response",
        )
