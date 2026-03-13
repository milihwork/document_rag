"""Safeguard factory: select provider from config."""

import os

from .basic_guard import BasicSafeguard

_safeguard_instance = None


def get_safeguard():
    """Return the safeguard instance for the configured SAFEGUARD_PROVIDER."""
    global _safeguard_instance
    if _safeguard_instance is None:
        provider = (os.getenv("SAFEGUARD_PROVIDER", "basic") or "").strip().lower()
        if provider == "basic":
            _safeguard_instance = BasicSafeguard()
        else:
            raise ValueError(f"Unsupported safeguard provider: {provider}")
    return _safeguard_instance
