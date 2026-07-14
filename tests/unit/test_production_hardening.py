"""Unit tests for production hardening helpers."""

from __future__ import annotations

import pytest
from app.config.settings import Settings
from app.core.logging import _redact_record
from app.monitoring.metrics import MetricsRegistry
from app.utils.files import sanitize_filename
from app.utils.network import get_client_ip
from starlette.requests import Request


def test_docs_disabled_in_production_property() -> None:
    settings = Settings.model_construct(
        app_env="production",
        enable_docs=True,
        debug=False,
    )
    assert settings.docs_enabled is False


def test_docs_enabled_in_development() -> None:
    settings = Settings.model_construct(app_env="development", enable_docs=True)
    assert settings.docs_enabled is True


def test_production_validator_rejects_debug() -> None:
    with pytest.raises(ValueError, match="DEBUG"):
        Settings(
            APP_NAME="x",
            APP_ENV="production",
            DEBUG=True,
            SECRET_KEY="x" * 64,
            DATABASE_URL="postgresql://u:p@localhost/db",
            REDIS_URL="rediss://localhost:6379",
            CLOUDINARY_CLOUD_NAME="c",
            CLOUDINARY_API_KEY="k",
            CLOUDINARY_API_SECRET="s",
            OWNER_PHONE_NUMBER="+15551234567",
            OWNER_EMAIL="owner@example.com",
            FRONTEND_URL="https://primepizza.example",
            ALLOWED_HOSTS=["api.primepizza.example"],
        )


def test_production_validator_requires_trusted_proxies_when_xff_enabled() -> None:
    with pytest.raises(ValueError, match="TRUSTED_PROXY_IPS"):
        Settings(
            APP_NAME="x",
            APP_ENV="production",
            DEBUG=False,
            SECRET_KEY="x" * 64,
            DATABASE_URL="postgresql://u:p@localhost/db",
            REDIS_URL="rediss://localhost:6379",
            CLOUDINARY_CLOUD_NAME="c",
            CLOUDINARY_API_KEY="k",
            CLOUDINARY_API_SECRET="s",
            OWNER_PHONE_NUMBER="+15551234567",
            OWNER_EMAIL="owner@example.com",
            FRONTEND_URL="https://primepizza.example",
            ALLOWED_HOSTS=["api.primepizza.example"],
            TRUST_X_FORWARDED_FOR=True,
            TRUSTED_PROXY_IPS=[],
        )


def test_metrics_registry_snapshot() -> None:
    registry = MetricsRegistry()
    registry.incr("http.requests_total")
    registry.observe("http.request.duration_ms", 12.5)
    snap = registry.snapshot()
    assert snap["counters"]["http.requests_total"] == 1
    assert snap["timers"]["http.request.duration_ms"]["count"] == 1


def _request(*, headers: list[tuple[bytes, bytes]] | None = None, client: str = "127.0.0.1") -> Request:
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "path": "/",
        "raw_path": b"/",
        "root_path": "",
        "scheme": "http",
        "query_string": b"",
        "headers": headers or [],
        "client": (client, 12345),
        "server": ("test", 80),
    }
    return Request(scope)


def test_get_client_ip_ignores_xff_by_default() -> None:
    request = _request(headers=[(b"x-forwarded-for", b"203.0.113.10, 10.0.0.1")])
    settings = Settings.model_construct(trust_x_forwarded_for=False, trusted_proxy_ips=[])
    assert get_client_ip(request, settings) == "127.0.0.1"


def test_get_client_ip_honors_xff_from_trusted_proxy() -> None:
    request = _request(
        headers=[(b"x-forwarded-for", b"203.0.113.10, 10.0.0.1")],
        client="10.0.0.2",
    )
    settings = Settings.model_construct(
        trust_x_forwarded_for=True,
        trusted_proxy_ips=["10.0.0.2"],
    )
    assert get_client_ip(request, settings) == "203.0.113.10"


def test_sanitize_filename_strips_path_traversal() -> None:
    assert sanitize_filename("../../etc/passwd.jpg") == "passwd.jpg"
    assert sanitize_filename("ok name.png") == "ok_name.png"


def test_log_redaction_masks_bearer_and_jwt() -> None:
    record = {
        "message": (
            "auth failure Authorization: Bearer abc.def.ghi password=secret "
            "token eyJhbGciOiJIUzI1NiJ9.e30.signature"
        )
    }
    assert _redact_record(record) is True
    assert "abc.def.ghi" not in record["message"]
    assert "secret" not in record["message"].split("password=", 1)[-1][:20]
    assert "[REDACTED]" in record["message"]
    assert "[REDACTED_JWT]" in record["message"]
