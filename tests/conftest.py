"""Shared pytest fixtures for the foundation test suite."""

from __future__ import annotations

import pytest
from app.config.settings import Settings, get_settings
from app.main import create_app
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def settings() -> Settings:
    get_settings.cache_clear()
    resolved = get_settings()
    # Hardenments under test without tripping live rate limits during the suite.
    object.__setattr__(resolved, "rate_limit_enabled", False)
    return resolved


@pytest.fixture
def app(settings: Settings):
    return create_app(settings=settings)


@pytest.fixture
def client(app):
    with TestClient(app) as test_client:
        yield test_client
