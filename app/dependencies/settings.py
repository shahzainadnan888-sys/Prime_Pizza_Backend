"""Settings dependency."""

from __future__ import annotations

from fastapi import Request

from app.config.settings import Settings, get_settings


def get_app_settings(request: Request) -> Settings:
    """Return settings from app state, falling back to the cached singleton."""
    settings = getattr(request.app.state, "settings", None)
    if isinstance(settings, Settings):
        return settings
    return get_settings()
