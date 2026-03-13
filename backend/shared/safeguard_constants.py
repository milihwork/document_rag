"""Centralized safeguard rules for input and output validation.

All blocked patterns and topics are defined here so they can be reused
across the RAG pipeline and any future safeguard providers.
"""

BLOCKED_PROMPT_PATTERNS = [
    "ignore previous instructions",
    "ignore system prompt",
    "reveal system prompt",
    "show hidden prompt",
    "developer mode",
]

BLOCKED_TOPICS = [
    "how to hack",
    "build a bomb",
]

BLOCKED_OUTPUT_PATTERNS = [
    "confidential",
    "internal document",
]
