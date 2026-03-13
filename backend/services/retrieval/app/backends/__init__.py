"""Vector store backends: qdrant, pgvector, etc."""

import importlib
import logging

from ..config.settings import settings

logger = logging.getLogger(__name__)

_BACKENDS = {}

# Lazy-load mapping: only the configured backend module is imported (avoids
# requiring psycopg2/pgvector when using VECTOR_BACKEND=qdrant).
_BACKEND_MODULES = {
    "qdrant": ".qdrant_backend",
    "pgvector": ".pgvector",
}


def register(name: str):
    """Decorator to register a vector store backend."""

    def decorator(cls):
        _BACKENDS[name] = cls
        return cls

    return decorator


def get_backend():
    """Return the backend instance for the configured VECTOR_BACKEND."""
    name = (settings.VECTOR_BACKEND or "qdrant").strip().lower()
    if name not in _BACKEND_MODULES:
        raise ValueError(
            f"Unknown VECTOR_BACKEND: {name}. Available: {list(_BACKEND_MODULES.keys())}"
        )
    if name not in _BACKENDS:
        mod_path = _BACKEND_MODULES[name]
        importlib.import_module(mod_path, package=__name__)
    return _BACKENDS[name]()
