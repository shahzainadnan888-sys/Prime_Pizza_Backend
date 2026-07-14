"""File helpers."""

from __future__ import annotations

import re
from pathlib import Path

_UNSAFE_FILENAME = re.compile(r"[^\w.\-]+")


def ensure_directory(path: str | Path) -> Path:
    """Create a directory if missing and return it."""
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def file_extension(filename: str) -> str:
    """Return lowercase file extension without the dot."""
    return Path(filename).suffix.lower().lstrip(".")


def sanitize_filename(filename: str, *, default: str = "upload.bin") -> str:
    """
    Strip path components and unsafe characters from a client-supplied name.

    Prevents path traversal and header/log injection via crafted filenames.
    """
    raw = (filename or "").replace("\\", "/").split("/")[-1].strip()
    if not raw or raw in {".", ".."}:
        return default
    cleaned = _UNSAFE_FILENAME.sub("_", raw).strip("._")
    if not cleaned:
        return default
    return cleaned[:180]
