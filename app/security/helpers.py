"""Generic security helpers."""

from __future__ import annotations

import secrets


def generate_secure_token(nbytes: int = 32) -> str:
    """Generate a URL-safe opaque token."""
    return secrets.token_urlsafe(nbytes)


def constant_time_compare(left: str, right: str) -> bool:
    """Compare two strings in constant time."""
    return secrets.compare_digest(left, right)
