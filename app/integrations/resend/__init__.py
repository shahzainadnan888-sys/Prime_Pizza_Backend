"""Email integration package."""

from app.integrations.resend.client import (
    close_resend,
    get_resend_from_email,
    init_resend,
    is_resend_configured,
    send_email_via_resend,
)

__all__ = [
    "close_resend",
    "get_resend_from_email",
    "init_resend",
    "is_resend_configured",
    "send_email_via_resend",
]
