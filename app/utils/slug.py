"""Slug helpers for catalog entities."""

from __future__ import annotations

import re
import unicodedata


_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(value: str, *, max_length: int = 220) -> str:
    """Normalize a human string into a URL-safe slug."""
    normalized = unicodedata.normalize("NFKD", value.strip().lower())
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    slug = _SLUG_RE.sub("-", ascii_only).strip("-")
    if not slug:
        msg = "Unable to generate slug from empty value"
        raise ValueError(msg)
    return slug[:max_length].rstrip("-")
