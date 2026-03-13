"""Vector store backends: qdrant, pgvector, etc."""

import logging

from ..config.settings import settings

logger = logging.getLogger(__name__)

_BACKENDS = {}


def register(name: str):
    """Decorator to register a vector store backend."""

    def decorator(cls):
        _BACKENDS[name] = cls
        return cls

    return decorator


def get_backend():
    """Return the backend instance for the configured VECTOR_BACKEND."""
    from . import (
        pgvector,  # noqa: F401
        qdrant_backend,  # noqa: F401
    )

    name = (settings.VECTOR_BACKEND or "qdrant").strip().lower()
    if name not in _BACKENDS:
        raise ValueError(f"Unknown VECTOR_BACKEND: {name}. Available: {list(_BACKENDS.keys())}")
    return _BACKENDS[name]()
