"""Resend email client — configuration + async send wrapper."""

from __future__ import annotations

from typing import Any

import resend
from loguru import logger

from app.config.settings import Settings

_configured: bool = False
_from_email: str | None = None


def init_resend(settings: Settings) -> None:
    """Configure the Resend SDK from environment settings."""
    global _configured, _from_email

    if settings.resend_api_key:
        resend.api_key = settings.resend_api_key
        _configured = True
        logger.info("Resend client configured")
    else:
        _configured = False
        logger.warning("RESEND_API_KEY not set — email client left unconfigured")

    _from_email = str(settings.resend_from_email)


def close_resend() -> None:
    """Clear Resend configuration."""
    global _configured, _from_email
    _configured = False
    _from_email = None
    logger.info("Resend client closed")


def is_resend_configured() -> bool:
    return _configured


def get_resend_from_email() -> str:
    if _from_email is None:
        msg = "Resend from-email is not configured."
        raise RuntimeError(msg)
    return _from_email


async def send_email_via_resend(
    *,
    to: list[str],
    subject: str,
    html: str,
    text: str,
    from_email: str | None = None,
    reply_to: str | None = None,
    attachments: list[dict[str, Any]] | None = None,
    tags: list[dict[str, str]] | None = None,
    scheduled_at: str | None = None,
) -> str | None:
    """
    Send a transactional email through Resend asynchronously.

    Returns the provider message id when available.
    Raises on provider / network failures (caller owns retry policy).
    """
    if not _configured:
        msg = "Resend is not configured"
        raise RuntimeError(msg)

    params: resend.Emails.SendParams = {
        "from": from_email or get_resend_from_email(),
        "to": to,
        "subject": subject,
        "html": html,
        "text": text,
    }
    if reply_to:
        params["reply_to"] = reply_to
    if attachments:
        params["attachments"] = attachments  # type: ignore[typeddict-item]
    if tags:
        params["tags"] = tags  # type: ignore[typeddict-item]
    if scheduled_at:
        params["scheduled_at"] = scheduled_at

    response = await resend.Emails.send_async(params)
    if isinstance(response, dict):
        return response.get("id")
    return getattr(response, "id", None)
