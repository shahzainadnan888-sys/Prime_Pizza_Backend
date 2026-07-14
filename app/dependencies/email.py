"""FastAPI dependencies for transactional email."""

from __future__ import annotations

from fastapi import Depends

from app.config.settings import Settings
from app.dependencies.settings import get_app_settings
from app.emails.renderer import EmailRenderer
from app.services.email import EmailService


def get_email_renderer() -> EmailRenderer:
    return EmailRenderer()


def get_email_service(
    settings: Settings = Depends(get_app_settings),
    renderer: EmailRenderer = Depends(get_email_renderer),
) -> EmailService:
    return EmailService(settings=settings, renderer=renderer)
