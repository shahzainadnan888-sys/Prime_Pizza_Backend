"""Reusable transactional email service with retry and async queue preparation."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from email_validator import EmailNotValidError, validate_email
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import EmailDeliveryStatus, EmailTemplateKey
from app.config.settings import Settings
from app.core.exceptions import ValidationException
from app.database.session import async_session_factory
from app.emails.payloads import (
    AttachmentPayload,
    EmailMessage,
    OrderEmailPayload,
    OwnerTestEmailPayload,
)
from app.emails.renderer import EmailRenderer
from app.emails.safe import sanitize_header
from app.integrations.resend.client import (
    get_resend_from_email,
    is_resend_configured,
    send_email_via_resend,
)
from app.models.email_log import EmailLog
from app.repositories.email_log import EmailLogRepository
from app.services.base import BaseService


class EmailService(BaseService):
    """
    Production email delivery service.

    Supports HTML + text, retries, attachments preparation, logging,
    and fire-and-forget enqueue for non-blocking API responses.
    """

    service_name = "email"

    def __init__(
        self,
        *,
        settings: Settings,
        renderer: EmailRenderer | None = None,
    ) -> None:
        self._settings = settings
        self._renderer = renderer or EmailRenderer()

    def _validate_recipients(self, recipients: list[str]) -> list[str]:
        if not recipients:
            raise ValidationException("At least one email recipient is required")
        cleaned: list[str] = []
        for raw in recipients:
            value = sanitize_header(raw.strip())
            if not value:
                continue
            try:
                result = validate_email(value, check_deliverability=False)
            except EmailNotValidError as exc:
                raise ValidationException(f"Invalid recipient email: {value}") from exc
            normalized = result.normalized
            if normalized not in cleaned:
                cleaned.append(normalized)
        if not cleaned:
            raise ValidationException("No valid email recipients")
        return cleaned

    def _attachments_for_provider(
        self,
        attachments: list[AttachmentPayload],
    ) -> list[dict[str, Any]] | None:
        """Prepare attachment payloads for Resend (future-ready)."""
        if not attachments:
            return None
        import base64

        prepared: list[dict[str, Any]] = []
        for item in attachments:
            entry: dict[str, Any] = {"filename": sanitize_header(item.filename)}
            if item.content is not None:
                entry["content"] = base64.b64encode(item.content).decode("ascii")
            if item.path:
                entry["path"] = item.path
            if item.content_type:
                entry["content_type"] = item.content_type
            prepared.append(entry)
        return prepared

    async def _persist_log(
        self,
        session: AsyncSession,
        *,
        recipient: str,
        subject: str,
        template_key: EmailTemplateKey,
        status: EmailDeliveryStatus,
        retry_count: int = 0,
        failure_reason: str | None = None,
        provider_message_id: str | None = None,
        sent_at: datetime | None = None,
        order_id: UUID | None = None,
        meta: dict[str, Any] | None = None,
        existing: EmailLog | None = None,
    ) -> EmailLog:
        repo = EmailLogRepository(session)
        if existing is None:
            existing = EmailLog(
                recipient=recipient,
                subject=subject,
                template_key=template_key,
                status=status,
                retry_count=retry_count,
                failure_reason=failure_reason,
                provider_message_id=provider_message_id,
                sent_at=sent_at,
                order_id=order_id,
                meta=meta,
            )
            await repo.add(existing)
        else:
            existing.status = status
            existing.retry_count = retry_count
            existing.failure_reason = failure_reason
            existing.provider_message_id = provider_message_id
            existing.sent_at = sent_at
            if meta is not None:
                existing.meta = meta
        await session.commit()
        await session.refresh(existing)
        return existing

    async def send_message(self, message: EmailMessage) -> EmailLog:
        """
        Send one email synchronously (with retries) and persist an email log.

        Uses an independent DB session so request sessions are never blocked.
        """
        recipients = self._validate_recipients(message.to)
        subject = sanitize_header(message.subject)
        if not subject:
            raise ValidationException("Email subject is required")

        # Multi-recipient: log each separately; send once via provider batch `to`
        primary = recipients[0]

        if not self._settings.is_email_configured or not is_resend_configured():
            logger.warning(
                "Email skipped | reason=not_configured | template={}",
                message.template_key.value,
            )
            async with async_session_factory()() as session:
                return await self._persist_log(
                    session,
                    recipient=",".join(recipients),
                    subject=subject,
                    template_key=message.template_key,
                    status=EmailDeliveryStatus.SKIPPED,
                    failure_reason="Resend not configured or EMAIL_ENABLED=false",
                    order_id=message.order_id,
                    meta={**message.meta, "recipients": recipients},
                )

        async with async_session_factory()() as session:
            log = await self._persist_log(
                session,
                recipient=",".join(recipients) if len(recipients) > 1 else primary,
                subject=subject,
                template_key=message.template_key,
                status=EmailDeliveryStatus.QUEUED,
                order_id=message.order_id,
                meta={**message.meta, "recipients": recipients},
            )
            logger.info(
                "Email queued | email_log_id={} | template={} | recipients={}",
                log.id,
                message.template_key.value,
                len(recipients),
            )

            max_attempts = self._settings.email_max_retries
            backoff = self._settings.email_retry_backoff_seconds
            last_error: str | None = None
            provider_id: str | None = None

            for attempt in range(1, max_attempts + 1):
                try:
                    log.status = EmailDeliveryStatus.SENDING
                    log.retry_count = attempt - 1
                    await session.commit()

                    logger.info(
                        "Retry attempt | email_log_id={} | attempt={}/{}",
                        log.id,
                        attempt,
                        max_attempts,
                    )
                    provider_id = await send_email_via_resend(
                        to=recipients,
                        subject=subject,
                        html=message.html,
                        text=message.text,
                        from_email=get_resend_from_email(),
                        attachments=self._attachments_for_provider(message.attachments),
                        tags=message.tags or None,
                        scheduled_at=message.scheduled_at,
                    )
                    log.status = EmailDeliveryStatus.SENT
                    log.retry_count = attempt - 1
                    log.provider_message_id = provider_id
                    log.sent_at = datetime.now(UTC)
                    log.failure_reason = None
                    await session.commit()
                    logger.info(
                        "Email sent | email_log_id={} | template={}",
                        log.id,
                        message.template_key.value,
                    )
                    return log
                except Exception as exc:
                    last_error = str(exc)[:500]
                    logger.warning(
                        "Email failed | email_log_id={} | attempt={} | error={}",
                        log.id,
                        attempt,
                        type(exc).__name__,
                    )
                    if attempt < max_attempts:
                        await asyncio.sleep(backoff * attempt)

            log.status = EmailDeliveryStatus.FAILED
            log.retry_count = max_attempts
            log.failure_reason = last_error or "Unknown email failure"
            await session.commit()
            logger.error(
                "Email failed | email_log_id={} | template={} | retries_exhausted=true",
                log.id,
                message.template_key.value,
            )
            return log

    def enqueue(self, message: EmailMessage) -> None:
        """
        Queue email delivery on the running event loop (non-blocking).

        Never raises to the caller — order placement must stay fast/safe.
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            logger.error("Email queued failed | no running event loop")
            return

        async def _runner() -> None:
            try:
                await self.send_message(message)
            except Exception:
                logger.exception(
                    "Email failed | background_task | template={}",
                    message.template_key.value,
                )

        loop.create_task(_runner(), name=f"email:{message.template_key.value}")
        logger.info(
            "Email queued | async_task | template={} | recipients={}",
            message.template_key.value,
            len(message.to),
        )

    def build_owner_new_order_message(
        self,
        payload: OrderEmailPayload,
        *,
        recipients: list[str] | None = None,
    ) -> EmailMessage:
        rendered = self._renderer.render_owner_new_order(payload)
        to = recipients or self._settings.owner_email_recipients()
        return EmailMessage(
            template_key=rendered.template_key,
            to=to,
            subject=rendered.subject,
            html=rendered.html,
            text=rendered.text,
            order_id=payload.order_id,
            tags=[{"name": "category", "value": "transactional_order"}],
            meta={"order_number": payload.order_number},
        )

    def build_owner_test_message(
        self,
        *,
        recipients: list[str] | None = None,
        message: str | None = None,
    ) -> EmailMessage:
        payload = OwnerTestEmailPayload(
            brand_name=self._settings.email_brand_name,
            logo_url=self._settings.email_logo_url or None,
            message=message
            or "This is a Prime Pizza transactional email connectivity test.",
        )
        rendered = self._renderer.render_owner_test(payload)
        to = recipients or self._settings.owner_email_recipients()
        return EmailMessage(
            template_key=rendered.template_key,
            to=to,
            subject=rendered.subject,
            html=rendered.html,
            text=rendered.text,
            tags=[{"name": "category", "value": "transactional_test"}],
            meta={"purpose": "owner_test"},
        )

    async def send_owner_test(
        self,
        *,
        to: str | None = None,
        message: str | None = None,
    ) -> EmailLog:
        recipients = [to] if to else None
        envelope = self.build_owner_test_message(recipients=recipients, message=message)
        return await self.send_message(envelope)

    def notify_owner_new_order(self, payload: OrderEmailPayload) -> None:
        """Fire-and-forget owner notification after a committed order."""
        try:
            if payload.logo_url is None and self._settings.email_logo_url:
                payload.logo_url = self._settings.email_logo_url
            if not payload.brand_name:
                payload.brand_name = self._settings.email_brand_name
            envelope = self.build_owner_new_order_message(payload)
            self.enqueue(envelope)
        except Exception:
            logger.exception(
                "Email queued failed | order_id={} | template=owner_new_order",
                payload.order_id,
            )
