"""Embedding backends: local (sentence-transformers), bedrock (stub), etc."""

import logging

from ..config.settings import settings

logger = logging.getLogger(__name__)

_BACKENDS = {}


def register(name: str):
    """Decorator to register an embedding backend."""

    def decorator(cls):
        _BACKENDS[name] = cls
        return cls

    return decorator


def get_backend():
    """Return the embedding backend instance for the configured EMBEDDING_BACKEND."""
    from . import (
        bedrock_stub,  # noqa: F401
        local,  # noqa: F401
    )

    name = (settings.EMBEDDING_BACKEND or "local").strip().lower()
    if name not in _BACKENDS:
        raise ValueError(f"Unknown EMBEDDING_BACKEND: {name}. Available: {list(_BACKENDS.keys())}")
    return _BACKENDS[name]()
