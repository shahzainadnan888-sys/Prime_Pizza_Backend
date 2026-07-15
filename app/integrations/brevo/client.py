"""Brevo (Sendinblue) transactional email client — HTTP API only."""

from __future__ import annotations

from typing import Any

import httpx
from loguru import logger

from app.config.settings import Settings

_BREVO_SMTP_URL = "https://api.brevo.com/v3/smtp/email"

_configured: bool = False
_api_key: str | None = None
_sender_email: str | None = None
_sender_name: str | None = None


def init_brevo(settings: Settings, *, strict: bool = False) -> None:
    """Configure Brevo credentials from environment settings."""
    global _configured, _api_key, _sender_email, _sender_name

    key = settings.brevo_api_key.strip()
    _sender_email = str(settings.brevo_sender_email).strip().lower() or None
    _sender_name = str(settings.brevo_sender_name).strip() or "Prime Pizza"

    missing: list[str] = []
    if not key:
        missing.append("BREVO_API_KEY")
    if not _sender_email:
        missing.append("BREVO_SENDER_EMAIL")
    if not _sender_name:
        missing.append("BREVO_SENDER_NAME")

    if missing:
        _api_key = None
        _configured = False
        detail = ",".join(missing)
        if strict:
            msg = f"Brevo startup configuration incomplete | missing={detail}"
            logger.error(msg)
            raise RuntimeError(msg)
        logger.warning("Brevo client left unconfigured | missing={}", detail)
        return

    _api_key = key
    _configured = True
    logger.info(
        "Brevo client configured | sender_email={} | sender_name={} | api_key_present=true",
        _sender_email,
        _sender_name,
    )


def close_brevo() -> None:
    global _configured, _api_key, _sender_email, _sender_name
    _configured = False
    _api_key = None
    _sender_email = None
    _sender_name = None
    logger.info("Brevo client closed")


def is_brevo_configured() -> bool:
    return _configured and bool(_api_key) and bool(_sender_email)


def ensure_brevo_initialized(settings: Settings) -> bool:
    """
    Initialize Brevo from settings if the process-level client is not ready.

    Returns True when configured and ready to send.
    """
    if is_brevo_configured():
        return True
    if settings.brevo_api_key.strip() and settings.email_enabled:
        init_brevo(settings)
    return is_brevo_configured()


def get_brevo_sender() -> tuple[str, str]:
    """Return (email, name) for the configured sender."""
    if not _sender_email:
        msg = "Brevo sender email is not configured"
        raise RuntimeError(msg)
    return _sender_email, _sender_name or "Prime Pizza"


async def send_email_via_brevo(
    *,
    to: list[str],
    subject: str,
    html: str,
    text: str,
    sender_email: str | None = None,
    sender_name: str | None = None,
    reply_to: str | None = None,
    tags: list[str] | None = None,
) -> str | None:
    """
    Send a transactional email through Brevo asynchronously.

    Returns the provider message id when available.
    Raises on provider / network failures (caller owns retry policy).
    """
    if not is_brevo_configured() or not _api_key:
        msg = "Brevo is not configured"
        raise RuntimeError(msg)

    email, name = get_brevo_sender()
    payload: dict[str, Any] = {
        "sender": {
            "email": sender_email or email,
            "name": sender_name or name,
        },
        "to": [{"email": recipient} for recipient in to],
        "subject": subject,
        "htmlContent": html,
        "textContent": text,
    }
    if reply_to:
        payload["replyTo"] = {"email": reply_to}
    if tags:
        payload["tags"] = tags

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": _api_key,
    }

    logger.info(
        "Brevo request start | url={} | to={} | subject={} | sender={}",
        _BREVO_SMTP_URL,
        to,
        subject,
        payload["sender"]["email"],
    )

    try:
        # Keep provider wait bounded so API handlers never hang near FE timeouts.
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=5.0)) as client:
            response = await client.post(_BREVO_SMTP_URL, json=payload, headers=headers)
    except httpx.HTTPError as exc:
        logger.exception(
            "Brevo request transport failure | to={} | subject={} | error={}",
            to,
            subject,
            str(exc),
        )
        raise RuntimeError(f"Brevo transport error: {exc}") from exc

    body_text = response.text
    logger.info(
        "Brevo request finished | status={} | to={} | subject={} | body_len={}",
        response.status_code,
        to,
        subject,
        len(body_text),
    )

    if response.status_code >= 400:
        logger.error(
            "Brevo API error | status={} | to={} | subject={} | response_body={}",
            response.status_code,
            to,
            subject,
            body_text[:2000],
        )
        msg = f"Brevo API error ({response.status_code}): {body_text[:500]}"
        raise RuntimeError(msg)

    data: Any = {}
    if response.content:
        try:
            data = response.json()
        except ValueError:
            logger.warning(
                "Brevo response was not JSON | status={} | body={}",
                response.status_code,
                body_text[:500],
            )
            data = {}

    message_id = data.get("messageId") if isinstance(data, dict) else None
    logger.info(
        "Brevo accepted email | message_id={} | to={} | subject={} | response={}",
        message_id,
        to,
        subject,
        data,
    )
    return str(message_id) if message_id else None
