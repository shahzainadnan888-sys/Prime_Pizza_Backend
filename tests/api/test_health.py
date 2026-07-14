"""API smoke tests for health endpoints."""

from __future__ import annotations


def test_root(client) -> None:
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "data" in body
    assert "X-Request-ID" in response.headers


def test_health(client) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True


def test_health_under_api_prefix(client) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
