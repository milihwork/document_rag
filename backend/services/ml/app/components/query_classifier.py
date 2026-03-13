"""LLM-based query intent classification."""

import json
import logging
import re
import time

from .base import BaseQueryClassifier, IntentResult

logger = logging.getLogger(__name__)

VALID_INTENTS = ["question", "command", "search", "clarification", "other"]

CLASSIFIER_PROMPT = """
You are a query intent classifier. Classify the user's query into one of these
categories:

- question: Asking for information or explanation (e.g., "What is X?",
  "How does Y work?")
- command: Requesting an action (e.g., "Create a file", "Delete this",
  "Run the test")
- search: Looking for specific content (e.g., "Find all files with X",
  "Show me Y")
- clarification: Asking for more details about previous context
  (e.g., "What do you mean?", "Can you explain further?")
- other: Doesn't fit the above categories

User Query: {query}

Respond ONLY with valid JSON (no markdown, no explanation):
{{"intent": "one of the categories above", "confidence": 0.0 to 1.0}}"""


class LLMQueryClassifier(BaseQueryClassifier):
    """Classify query intent using LLM."""

    def __init__(self, llm_backend):
        self._llm = llm_backend

    def classify(self, query: str) -> IntentResult:
        """Classify the intent of the query."""
        start = time.perf_counter()

        prompt = CLASSIFIER_PROMPT.format(query=query)

        try:
            response = self._llm.complete(prompt, n_predict=100, temperature=0.1)
            result = self._parse_response(response)
            elapsed = (time.perf_counter() - start) * 1000
            logger.info(
                "Query classification: intent=%s, confidence=%.2f in %.0fms",
                result.intent,
                result.confidence,
                elapsed,
            )
            return result
        except Exception as e:
            logger.error("Query classification failed: %s", e)
            return IntentResult(intent="other", confidence=0.0)

    def _parse_response(self, response: str) -> IntentResult:
        """Parse LLM response into IntentResult."""
        try:
            json_match = re.search(r"\{[^}]+\}", response)
            if json_match:
                data = json.loads(json_match.group())
                intent = str(data.get("intent", "other")).lower()
                if intent not in VALID_INTENTS:
                    intent = "other"
                return IntentResult(
                    intent=intent,
                    confidence=float(data.get("confidence", 0.0)),
                )
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("Failed to parse classification response: %s", e)

        return IntentResult(intent="other", confidence=0.0)
