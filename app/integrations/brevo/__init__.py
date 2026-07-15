"""Brevo email integration."""

from app.integrations.brevo.client import (
    close_brevo,
    ensure_brevo_initialized,
    get_brevo_sender,
    init_brevo,
    is_brevo_configured,
    send_email_via_brevo,
)

__all__ = [
    "close_brevo",
    "ensure_brevo_initialized",
    "get_brevo_sender",
    "init_brevo",
    "is_brevo_configured",
    "send_email_via_brevo",
]
