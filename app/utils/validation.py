"""Generic validation helpers."""

from __future__ import annotations

import re

_SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def is_non_empty(value: str | None) -> bool:
    return bool(value and value.strip())


def is_valid_slug(value: str) -> bool:
    return bool(_SLUG_PATTERN.match(value))
