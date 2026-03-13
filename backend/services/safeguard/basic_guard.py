"""Basic safeguard: pattern- and topic-based input/output validation."""

from .base import BaseSafeguard
from shared.safeguard_constants import (
    BLOCKED_OUTPUT_PATTERNS,
    BLOCKED_PROMPT_PATTERNS,
    BLOCKED_TOPICS,
)


class BasicSafeguard(BaseSafeguard):
    """Validates input and output against shared blocked patterns and topics."""

    def validate_input(self, query: str) -> bool:
        q = query.lower()

        for pattern in BLOCKED_PROMPT_PATTERNS:
            if pattern and pattern in q:
                return False

        for topic in BLOCKED_TOPICS:
            if topic and topic in q:
                return False

        return True

    def validate_output(self, response: str) -> bool:
        r = response.lower()

        for pattern in BLOCKED_OUTPUT_PATTERNS:
            if pattern and pattern in r:
                return False

        return True
