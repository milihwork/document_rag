"""LLM backends: llama (llama.cpp HTTP), bedrock (stub), etc."""

import importlib
import logging

from ..config.settings import settings

logger = logging.getLogger(__name__)

_BACKENDS = {}

# Lazy-load mapping: only the configured backend module is imported (avoids
# requiring e.g. openai when using LLM_BACKEND=llama).
_BACKEND_MODULES = {
    "llama": ".llama_backend",
    "openai": ".openai_backend",
    "bedrock": ".bedrock_stub",
}


def register(name: str):
    """Decorator to register an LLM backend."""

    def decorator(cls):
        _BACKENDS[name] = cls
        return cls

    return decorator


def get_backend():
    """Return the LLM backend instance for the configured LLM_BACKEND."""
    name = (settings.LLM_BACKEND or "llama").strip().lower()
    if name not in _BACKEND_MODULES:
        raise ValueError(
            f"Unknown LLM_BACKEND: {name}. Available: {list(_BACKEND_MODULES.keys())}"
        )
    if name not in _BACKENDS:
        mod_path = _BACKEND_MODULES[name]
        importlib.import_module(mod_path, package=__name__)
    return _BACKENDS[name]()
