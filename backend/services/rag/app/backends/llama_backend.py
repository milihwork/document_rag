"""LLM backend: llama.cpp HTTP completion API."""

import logging
import time

import httpx

from shared.contracts import PATH_COMPLETION

from ..config.settings import settings
from . import register
from .base import LLM

logger = logging.getLogger(__name__)


@register("llama")
class LlamaBackend(LLM):
    """Generate text via llama.cpp server."""

    def complete(
        self, prompt: str, n_predict: int = 256, temperature: float = 0.2
    ) -> str:
        """Send prompt to llama.cpp and return generated text."""
        url = f"{settings.LLM_URL}{PATH_COMPLETION}"
        payload = {
            "prompt": prompt,
            "n_predict": n_predict,
            "temperature": temperature,
            "stop": ["</s>"],
        }

        start = time.perf_counter()
        try:
            with httpx.Client(timeout=60.0) as client:
                r = client.post(url, json=payload)
                r.raise_for_status()
                data = r.json()
                content = data.get("content", "").strip()
            elapsed = (time.perf_counter() - start) * 1000
            logger.info("LLM generated %d chars in %.0fms", len(content), elapsed)
            return content
        except httpx.HTTPError as e:
            elapsed = (time.perf_counter() - start) * 1000
            logger.error("LLM request failed after %.0fms: %s", elapsed, e)
            raise
