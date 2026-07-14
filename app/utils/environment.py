"""Environment helper utilities."""

from __future__ import annotations

import os


def env_bool(name: str, default: bool = False) -> bool:
    """Parse a boolean environment variable."""
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def require_env(name: str) -> str:
    """Return a required environment variable or raise."""
    value = os.getenv(name)
    if value is None or value.strip() == "":
        msg = f"Missing required environment variable: {name}"
        raise RuntimeError(msg)
    return value
