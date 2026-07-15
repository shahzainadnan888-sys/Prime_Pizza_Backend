"""Email service FastAPI dependencies."""

from __future__ import annotations

from fastapi import Depends

from app.config.settings import Settings
from app.dependencies.settings import get_app_settings
from app.services.email_service import EmailService


def get_email_service(settings: Settings = Depends(get_app_settings)) -> EmailService:
    return EmailService(settings=settings)
