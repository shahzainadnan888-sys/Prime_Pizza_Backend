"""Backward-compatible export — prefer ``app.services.email_service``."""

from app.services.email_service import EmailQueue, EmailService, InProcessEmailQueue

__all__ = ["EmailQueue", "EmailService", "InProcessEmailQueue"]
