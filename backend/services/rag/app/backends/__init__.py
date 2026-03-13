"""LLM backends: llama (llama.cpp HTTP), bedrock (stub), etc."""

import logging

from ..config.settings import settings

logger = logging.getLogger(__name__)

_BACKENDS = {}


def register(name: str):
    """Decorator to register an LLM backend."""

    def decorator(cls):
        _BACKENDS[name] = cls
        return cls

    return decorator


def get_backend():
    """Return the LLM backend instance for the configured LLM_BACKEND."""
    from . import (
        bedrock_stub,  # noqa: F401
        llama_backend,  # noqa: F401
        openai_backend,  # noqa: F401
    )

    name = (settings.LLM_BACKEND or "llama").strip().lower()
    if name not in _BACKENDS:
        raise ValueError(f"Unknown LLM_BACKEND: {name}. Available: {list(_BACKENDS.keys())}")
    return _BACKENDS[name]()
