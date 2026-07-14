"""Date / time helpers."""

from __future__ import annotations

from datetime import UTC, datetime


def utc_now() -> datetime:
    """Return timezone-aware UTC now."""
    return datetime.now(UTC)


def to_iso8601(value: datetime) -> str:
    """Serialize a datetime to ISO-8601."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.isoformat()
