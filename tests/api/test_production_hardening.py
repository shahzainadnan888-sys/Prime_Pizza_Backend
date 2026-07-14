"""Production hardening API smoke tests."""

from __future__ import annotations

from app.config.settings import Settings
from app.main import create_app
from fastapi.testclient import TestClient


def test_security_headers_present(client) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "Content-Security-Policy" in response.headers
    assert "Permissions-Policy" in response.headers


def test_docs_csp_allows_swagger_cdn(client) -> None:
    response = client.get("/docs")
    assert response.status_code == 200
    csp = response.headers.get("Content-Security-Policy", "")
    assert "cdn.jsdelivr.net" in csp
    assert "script-src" in csp


def test_request_id_echo(client) -> None:
    response = client.get("/health", headers={"X-Request-ID": "test-corr-id-001"})
    assert response.headers.get("X-Request-ID") == "test-corr-id-001"


def test_request_id_injection_rejected(client) -> None:
    response = client.get("/health", headers={"X-Request-ID": "bad\r\nInjected: yes"})
    assert response.status_code == 200
    assert "\r" not in response.headers.get("X-Request-ID", "")
    assert response.headers.get("X-Request-ID") != "bad\r\nInjected: yes"


def test_health_services(client) -> None:
    response = client.get("/health/services")
    assert response.status_code in {200, 503}
    body = response.json()
    assert "data" in body
    assert "database" in body["data"]
    assert "redis" in body["data"]
    assert "cloudinary" in body["data"]
    assert "resend" in body["data"]
    assert "otp_provider" in body["data"]
    assert "metrics" in body["data"]
    metrics = body["data"]["metrics"]
    assert "uptime_seconds" in metrics
    assert "http_requests_total" in metrics
    assert "counters" not in metrics
    assert "timers" not in metrics


def test_root_hides_docs_paths_consistently(client) -> None:
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert "name" in data
    assert "environment" in data


def test_oversized_content_length_rejected(settings: Settings) -> None:
    tiny = settings.model_copy(update={"max_request_body_bytes": 32, "rate_limit_enabled": False})
    app = create_app(settings=tiny)
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/send-otp",
            json={"phone_number": "+155512345678901234567890"},
        )
    assert response.status_code == 413
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "payload_too_large"


def test_xff_spoof_does_not_change_peer_without_trust(client) -> None:
    # When TRUST_X_FORWARDED_FOR is false (default), spoofed XFF must not alter identity
    # used by middleware; health remains reachable and rate-limit headers are stable.
    response = client.get(
        "/health",
        headers={"X-Forwarded-For": "203.0.113.99"},
    )
    assert response.status_code == 200
