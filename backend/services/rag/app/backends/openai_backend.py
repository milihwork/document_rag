"""OpenAI chat completions LLM backend."""

import logging
import time

from openai import OpenAI

from ..config.settings import settings
from . import register
from .base import LLM

logger = logging.getLogger(__name__)


@register("openai")
class OpenAIBackend(LLM):
    """Generate text via OpenAI chat completions API."""

    def __init__(self) -> None:
        kwargs = {"api_key": settings.OPENAI_API_KEY}
        if settings.OPENAI_BASE_URL:
            kwargs["base_url"] = settings.OPENAI_BASE_URL
        self._client = OpenAI(**kwargs)

    def complete(
        self,
        prompt: str,
        *,
        n_predict: int | None = None,
        temperature: float | None = None,
    ) -> str:
        """Send prompt as user message and return assistant content."""
        max_tokens = n_predict if n_predict is not None else 256
        temp = temperature if temperature is not None else 0.2

        start = time.perf_counter()
        try:
            response = self._client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temp,
            )
            content = (
                (response.choices[0].message.content or "").strip()
                if response.choices
                else ""
            )
            elapsed = (time.perf_counter() - start) * 1000
            logger.info("OpenAI generated %d chars in %.0fms", len(content), elapsed)
            return content
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            logger.error("OpenAI request failed after %.0fms: %s", elapsed, e)
            raise
