"""LLM-based document classification."""

import json
import logging
import re
import time

from .base import BaseDocumentClassifier, DocumentClassResult

logger = logging.getLogger(__name__)

VALID_CATEGORIES = ["cv", "technical", "legal", "report", "research", "other"]

CLASSIFIER_PROMPT = """Classify this document into one category based on the content sample.

Categories:
- cv: Resume, CV, professional profile, work experience
- technical: Technical documentation, API docs, guides, tutorials
- legal: Contracts, terms of service, legal documents, agreements
- report: Business reports, analysis, summaries, presentations
- research: Academic papers, research documents, scientific articles
- other: Uncategorized documents

Document sample:
{text_sample}

Respond ONLY with valid JSON (no markdown, no explanation):
{{"category": "one of the categories above", "confidence": 0.0 to 1.0}}"""


class LLMDocumentClassifier(BaseDocumentClassifier):
    """Classify documents using LLM."""

    def __init__(self, llm_backend):
        self._llm = llm_backend

    def classify(self, text_sample: str) -> DocumentClassResult:
        """Classify the document based on a text sample."""
        start = time.perf_counter()

        # Truncate text sample to avoid token limits
        truncated = text_sample[:2000] if len(text_sample) > 2000 else text_sample
        prompt = CLASSIFIER_PROMPT.format(text_sample=truncated)

        try:
            response = self._llm.complete(prompt, n_predict=100, temperature=0.1)
            result = self._parse_response(response)
            elapsed = (time.perf_counter() - start) * 1000
            logger.info(
                "Document classification: category=%s, confidence=%.2f in %.0fms",
                result.category,
                result.confidence,
                elapsed,
            )
            return result
        except Exception as e:
            logger.error("Document classification failed: %s", e)
            return DocumentClassResult(category="other", confidence=0.0)

    def _parse_response(self, response: str) -> DocumentClassResult:
        """Parse LLM response into DocumentClassResult."""
        try:
            json_match = re.search(r"\{[^}]+\}", response)
            if json_match:
                data = json.loads(json_match.group())
                category = str(data.get("category", "other")).lower()
                if category not in VALID_CATEGORIES:
                    category = "other"
                return DocumentClassResult(
                    category=category,
                    confidence=float(data.get("confidence", 0.0)),
                )
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("Failed to parse classification response: %s", e)

        return DocumentClassResult(category="other", confidence=0.0)
