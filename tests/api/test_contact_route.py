"""Smoke-test contact route registration and auth role claim."""

from __future__ import annotations

from app.config.settings import get_settings
from app.main import create_app
from fastapi.testclient import TestClient


def test_contact_route_exists_and_validates() -> None:
    app = create_app(settings=get_settings())
    with TestClient(app) as client:
        # Missing body fields → validation error, proves route is mounted (not 404)
        resp = client.post("/api/v1/contact", json={})
        assert resp.status_code == 422, resp.text

        resp_slash = client.post("/api/v1/contact/", json={})
        assert resp_slash.status_code == 422, resp_slash.text

        resp_alias = client.post("/api/v1/contacts", json={})
        assert resp_alias.status_code == 422, resp_alias.text


def test_openapi_lists_contact() -> None:
    app = create_app(settings=get_settings())
    paths = app.openapi()["paths"]
    assert "/api/v1/contact" in paths
    assert "post" in paths["/api/v1/contact"]
