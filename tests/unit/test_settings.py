"""Unit tests for settings normalization."""

from __future__ import annotations

from app.config.settings import Settings


def test_database_url_asyncpg_normalization() -> None:
    url = Settings.normalize_database_url(
        "postgresql://user:pass@host/db?sslmode=require&channel_binding=require"
    )
    assert url.startswith("postgresql+asyncpg://")
    assert "ssl=require" in url
    assert "channel_binding" not in url
    assert "sslmode" not in url


def test_redis_url_cli_paste_normalization() -> None:
    raw = (
        "redis-cli --tls -u "
        "redis://default:secret@curious-seahorse.upstash.io:6379"
    )
    url = Settings.normalize_redis_url(raw)
    assert url.startswith("rediss://")
    assert "redis-cli" not in url
