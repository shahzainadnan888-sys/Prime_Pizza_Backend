"""Brevo email service — awaited delivery after DB commits; failures raise."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Protocol
from uuid import UUID

from email_validator import EmailNotValidError, validate_email
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import EmailDeliveryStatus, EmailTemplateKey
from app.config.settings import Settings
from app.core.exceptions import ExternalServiceException, ValidationException
from app.database.session import async_session_factory
from app.emails.payloads import EmailMessage, OrderEmailPayload
from app.emails.safe import sanitize_header
from app.integrations.brevo.client import (
    ensure_brevo_initialized,
    is_brevo_configured,
    send_email_via_brevo,
)
from app.models.email_log import EmailLog
from app.repositories.email_log import EmailLogRepository
from app.services.base import BaseService
from app.utils.email_helpers import html_escape, plain_text_from_context, render_template


class EmailQueue(Protocol):
    """Optional queue abstraction (Celery / RQ later)."""

    def enqueue(self, message: EmailMessage) -> None: ...


class InProcessEmailQueue:
    """Background queue kept for optional non-critical mail only."""

    def __init__(self, send_fn: Any) -> None:
        self._send_fn = send_fn

    def enqueue(self, message: EmailMessage) -> None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            logger.error(
                "Email event | status=queue_failed | template={} | reason=no_event_loop",
                message.template_key.value,
            )
            return

        async def _runner() -> None:
            try:
                await self._send_fn(message)
            except Exception:
                logger.exception(
                    "Email event | status=failed | template={} | background_task=true",
                    message.template_key.value,
                )

        loop.create_task(_runner(), name=f"email:{message.template_key.value}")
        logger.info(
            "Email event | status=queued | template={} | recipients={} | subject={}",
            message.template_key.value,
            message.to,
            message.subject,
        )


class EmailService(BaseService):
    """Production email orchestration — templates + Brevo + logs."""

    service_name = "email"

    def __init__(
        self,
        *,
        settings: Settings,
        queue: EmailQueue | None = None,
    ) -> None:
        self._settings = settings
        self._queue: EmailQueue = queue or InProcessEmailQueue(self.send_message)

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

    def _money(self, value: Decimal | float | int | str) -> str:
        return f"{Decimal(str(value)):.2f}"

    def _format_estimated_delivery(self, payload: OrderEmailPayload) -> str:
        if payload.estimated_delivery_time is not None:
            return payload.estimated_delivery_time.isoformat()
        if payload.estimated_preparation_minutes is not None:
            return f"About {payload.estimated_preparation_minutes} minutes"
        return "—"

    def _order_template_context(self, payload: OrderEmailPayload) -> dict[str, Any]:
        brand = payload.brand_name or self._settings.email_brand_name
        return {
            "brand_name": brand,
            "order_number": payload.order_number,
            "order_id": str(payload.order_id),
            "order_status": payload.order_status,
            "order_time": payload.order_created_at.isoformat(),
            "customer_name": payload.customer_name,
            "customer_email": payload.customer_email or "—",
            "customer_phone": payload.customer_phone or "—",
            "delivery_address": payload.delivery_address,
            "payment_method": payload.payment_method,
            "payment_status": payload.payment_status,
            "currency": payload.currency,
            "subtotal": self._money(payload.subtotal),
            "delivery_fee": self._money(payload.delivery_fee),
            "tax": self._money(payload.tax),
            "discount": self._money(payload.discount),
            "grand_total": self._money(payload.grand_total),
            "estimated_delivery": self._format_estimated_delivery(payload),
            "items_rows": self._build_order_items_rows(payload),
            "_raw_html_keys": {"items_rows"},
        }

    def _build_order_items_rows(self, payload: OrderEmailPayload) -> str:
        rows: list[str] = []
        for item in payload.items:
            name = html_escape(item.product_name)
            if item.variant_name:
                name = f"{name} ({html_escape(item.variant_name)})"
            rows.append(
                "<tr>"
                f"<td style='padding:10px 8px;border-bottom:1px solid #eee;'>{name}</td>"
                f"<td align='center' style='padding:10px 8px;border-bottom:1px solid #eee;'>"
                f"{item.quantity}</td>"
                f"<td align='right' style='padding:10px 8px;border-bottom:1px solid #eee;'>"
                f"{html_escape(payload.currency)} {self._money(item.unit_price)}</td>"
                f"<td align='right' style='padding:10px 8px;border-bottom:1px solid #eee;'>"
                f"{html_escape(payload.currency)} {self._money(item.subtotal)}</td>"
                "</tr>"
            )
        return "".join(rows) or (
            "<tr><td colspan='4' style='padding:12px;'>No items</td></tr>"
        )

    def build_welcome_message(self, *, customer_name: str, customer_email: str) -> EmailMessage:
        brand = self._settings.email_brand_name
        html = render_template(
            "welcome_email.html",
            {
                "brand_name": brand,
                "customer_name": customer_name,
                "customer_email": customer_email,
            },
        )
        text = plain_text_from_context(
            [
                f"Welcome to {brand}, {customer_name}!",
                f"Your login email is {customer_email}.",
                "Thanks for joining us — browse the menu and order anytime.",
            ]
        )
        return EmailMessage(
            template_key=EmailTemplateKey.WELCOME,
            to=[customer_email],
            subject=f"Welcome to {brand}",
            html=html,
            text=text,
            tags=[{"name": "category", "value": "welcome"}],
            meta={"purpose": "welcome"},
        )

    def build_chef_notification_message(self, payload: OrderEmailPayload) -> EmailMessage:
        """Kitchen alert for a new order (CHEF_EMAIL)."""
        brand = payload.brand_name or self._settings.email_brand_name
        html = render_template(
            "order_notification.html",
            self._order_template_context(payload),
        )
        text = plain_text_from_context(
            [
                f"New order {payload.order_number}",
                f"Order ID: {payload.order_id}",
                f"Customer: {payload.customer_name}",
                f"Phone: {payload.customer_phone or '—'}",
                f"Address: {payload.delivery_address}",
                f"Total: {payload.currency} {self._money(payload.grand_total)}",
            ]
        )
        to = self._settings.chef_notification_recipients()
        if not to:
            raise ValidationException(
                "CHEF_EMAIL is not configured for kitchen notifications"
            )
        return EmailMessage(
            template_key=EmailTemplateKey.ORDER_NOTIFICATION,
            to=to,
            subject=f"Kitchen — New Order {payload.order_number} — {brand}",
            html=html,
            text=text,
            order_id=payload.order_id,
            tags=[{"name": "category", "value": "chef_notification"}],
            meta={
                "order_number": payload.order_number,
                "purpose": "chef_notification",
            },
        )

    def build_order_notification_message(
        self,
        payload: OrderEmailPayload,
        *,
        recipients: list[str] | None = None,
    ) -> EmailMessage:
        brand = payload.brand_name or self._settings.email_brand_name
        html = render_template(
            "order_notification.html",
            self._order_template_context(payload),
        )
        text = plain_text_from_context(
            [
                f"New order {payload.order_number}",
                f"Customer: {payload.customer_name}",
                f"Email: {payload.customer_email or '—'}",
                f"Phone: {payload.customer_phone or '—'}",
                f"Total: {payload.currency} {self._money(payload.grand_total)}",
                f"Status: {payload.order_status}",
            ]
        )
        to = recipients or self._settings.admin_email_recipients()
        return EmailMessage(
            template_key=EmailTemplateKey.ORDER_NOTIFICATION,
            to=to,
            subject=f"New Order {payload.order_number} — {brand}",
            html=html,
            text=text,
            order_id=payload.order_id,
            tags=[{"name": "category", "value": "order_notification"}],
            meta={"order_number": payload.order_number},
        )

    def build_order_confirmation_message(self, payload: OrderEmailPayload) -> EmailMessage:
        if not payload.customer_email:
            raise ValidationException("Customer email is required for order confirmation")
        brand = payload.brand_name or self._settings.email_brand_name
        html = render_template(
            "order_confirmation.html",
            self._order_template_context(payload),
        )
        text = plain_text_from_context(
            [
                f"Order confirmation {payload.order_number}",
                f"Hi {payload.customer_name},",
                f"Status: {payload.order_status}",
                f"Total: {payload.currency} {self._money(payload.grand_total)}",
                f"Payment: {payload.payment_method}",
                f"Delivery: {payload.delivery_address}",
            ]
        )
        return EmailMessage(
            template_key=EmailTemplateKey.ORDER_CONFIRMATION,
            to=[payload.customer_email],
            subject=f"Order Confirmation {payload.order_number} — {brand}",
            html=html,
            text=text,
            order_id=payload.order_id,
            tags=[{"name": "category", "value": "order_confirmation"}],
            meta={"order_number": payload.order_number, "purpose": "customer_confirmation"},
        )

    def build_contact_admin_message(
        self,
        *,
        name: str,
        email: str,
        phone: str | None,
        subject: str,
        message: str,
        submission_time: datetime | None = None,
        client_ip: str | None = None,
    ) -> EmailMessage:
        brand = self._settings.email_brand_name
        submitted = (submission_time or datetime.now(UTC)).isoformat()
        ip_display = client_ip or "—"
        html = render_template(
            "contact_notification.html",
            {
                "brand_name": brand,
                "name": name,
                "email": email,
                "phone": phone or "—",
                "subject": subject,
                "message": message,
                "submission_time": submitted,
                "client_ip": ip_display,
            },
        )
        text = plain_text_from_context(
            [
                f"Contact from {name} <{email}>",
                f"Phone: {phone or '—'}",
                f"Subject: {subject}",
                f"Submitted at: {submitted}",
                f"IP: {ip_display}",
                "",
                message,
            ]
        )
        return EmailMessage(
            template_key=EmailTemplateKey.CONTACT_NOTIFICATION,
            to=self._settings.contact_notification_recipients(),
            subject=f"[Contact] {subject}",
            html=html,
            text=text,
            tags=[{"name": "category", "value": "contact_admin"}],
            meta={
                "from_email": email,
                "submission_time": submitted,
                "client_ip": client_ip,
            },
        )

    def build_contact_confirmation_message(
        self,
        *,
        name: str,
        email: str,
        subject: str,
    ) -> EmailMessage:
        brand = self._settings.email_brand_name
        html = render_template(
            "contact_confirmation.html",
            {
                "brand_name": brand,
                "name": name,
                "subject": subject,
            },
        )
        text = plain_text_from_context(
            [
                f"Hi {name},",
                f"We received your message about '{subject}'.",
                f"Thanks for contacting {brand}.",
            ]
        )
        return EmailMessage(
            template_key=EmailTemplateKey.CONTACT_CONFIRMATION,
            to=[email],
            subject=f"We received your message - {brand}",
            html=html,
            text=text,
            tags=[{"name": "category", "value": "contact_confirmation"}],
            meta={"purpose": "contact_confirmation"},
        )

    def build_admin_test_message(
        self,
        *,
        recipients: list[str] | None = None,
        message: str | None = None,
    ) -> EmailMessage:
        brand = self._settings.email_brand_name
        body = message or "This is a Prime Pizza Brevo connectivity test."
        html = (
            f"<html><body style='font-family:Arial,sans-serif;padding:24px;'>"
            f"<h2>{html_escape(brand)} test email</h2>"
            f"<p>{html_escape(body)}</p>"
            f"</body></html>"
        )
        to = recipients or self._settings.admin_email_recipients()
        return EmailMessage(
            template_key=EmailTemplateKey.ADMIN_TEST,
            to=to,
            subject=f"{brand} email test",
            html=html,
            text=body,
            tags=[{"name": "category", "value": "admin_test"}],
            meta={"purpose": "admin_test"},
        )

    async def send_message(self, message: EmailMessage) -> EmailLog:
        """
        Send one email with retries and persist delivery logs.

        Raises ExternalServiceException when Brevo is unconfigured or delivery fails.
        Never returns a fake success status.
        """
        recipients = self._validate_recipients(message.to)
        subject = sanitize_header(message.subject)
        if not subject:
            raise ValidationException("Email subject is required")

        primary = recipients[0]
        timestamp = datetime.now(UTC).isoformat()
        ready = ensure_brevo_initialized(self._settings)

        if not self._settings.is_email_configured or not ready or not is_brevo_configured():
            reason = "Brevo not configured or EMAIL_ENABLED=false"
            logger.error(
                "Email event | status=failed | template={} | recipients={} | "
                "subject={} | timestamp={} | reason={}",
                message.template_key.value,
                recipients,
                subject,
                timestamp,
                reason,
            )
            try:
                async with async_session_factory()() as session:
                    await self._persist_log(
                        session,
                        recipient=",".join(recipients),
                        subject=subject,
                        template_key=message.template_key,
                        status=EmailDeliveryStatus.FAILED,
                        failure_reason=reason,
                        order_id=message.order_id,
                        meta={
                            **message.meta,
                            "recipients": recipients,
                            "timestamp": timestamp,
                        },
                    )
            except Exception:
                logger.exception("Failed to persist email failure log | template={}", message.template_key.value)
            raise ExternalServiceException(
                "Email service is not configured. Set BREVO_API_KEY, "
                "BREVO_SENDER_EMAIL, and EMAIL_ENABLED=true.",
                service="brevo",
                details={
                    "template": message.template_key.value,
                    "recipients": recipients,
                    "reason": reason,
                },
            )

        async with async_session_factory()() as session:
            log = await self._persist_log(
                session,
                recipient=",".join(recipients) if len(recipients) > 1 else primary,
                subject=subject,
                template_key=message.template_key,
                status=EmailDeliveryStatus.QUEUED,
                order_id=message.order_id,
                meta={**message.meta, "recipients": recipients, "timestamp": timestamp},
            )
            logger.info(
                "Email event | status=sending | email_log_id={} | template={} | "
                "recipients={} | subject={} | timestamp={}",
                log.id,
                message.template_key.value,
                recipients,
                subject,
                timestamp,
            )

            max_attempts = self._settings.email_max_retries
            backoff = self._settings.email_retry_backoff_seconds
            last_error: str | None = None
            provider_id: str | None = None
            tag_values = [t.get("value", "") for t in message.tags if t.get("value")]

            for attempt in range(1, max_attempts + 1):
                try:
                    log.status = EmailDeliveryStatus.SENDING
                    log.retry_count = attempt - 1
                    await session.commit()

                    logger.info(
                        "Email event | status=brevo_attempt | email_log_id={} | "
                        "template={} | attempt={}/{}",
                        log.id,
                        message.template_key.value,
                        attempt,
                        max_attempts,
                    )
                    provider_id = await send_email_via_brevo(
                        to=recipients,
                        subject=subject,
                        html=message.html,
                        text=message.text,
                        tags=tag_values or None,
                    )
                    log.status = EmailDeliveryStatus.SENT
                    log.retry_count = attempt - 1
                    log.provider_message_id = provider_id
                    log.sent_at = datetime.now(UTC)
                    log.failure_reason = None
                    await session.commit()
                    logger.info(
                        "Email event | status=sent | email_log_id={} | template={} | "
                        "recipients={} | subject={} | provider_response={} | timestamp={}",
                        log.id,
                        message.template_key.value,
                        recipients,
                        subject,
                        provider_id,
                        datetime.now(UTC).isoformat(),
                    )
                    return log
                except Exception as exc:
                    last_error = str(exc)[:2000]
                    logger.warning(
                        "Email event | status=retry | email_log_id={} | template={} | "
                        "attempt={}/{} | failure_reason={} | timestamp={}",
                        log.id,
                        message.template_key.value,
                        attempt,
                        max_attempts,
                        last_error,
                        datetime.now(UTC).isoformat(),
                    )
                    if attempt < max_attempts:
                        await asyncio.sleep(backoff * attempt)

            log.status = EmailDeliveryStatus.FAILED
            log.retry_count = max_attempts
            log.failure_reason = last_error or "Unknown email failure"
            await session.commit()
            logger.error(
                "Email event | status=failed | email_log_id={} | template={} | "
                "recipients={} | subject={} | failure_reason={} | timestamp={}",
                log.id,
                message.template_key.value,
                recipients,
                subject,
                log.failure_reason,
                datetime.now(UTC).isoformat(),
            )
            raise ExternalServiceException(
                f"Failed to send email via Brevo: {log.failure_reason}",
                service="brevo",
                details={
                    "template": message.template_key.value,
                    "recipients": recipients,
                    "email_log_id": str(log.id),
                    "failure_reason": log.failure_reason,
                },
            )

    def _schedule(self, coro: Any, *, label: str) -> None:
        """Fire-and-forget async work with guaranteed failure logging."""

        async def _runner() -> None:
            try:
                await coro
            except Exception:
                logger.exception(
                    "Email event | status=background_failed | label={}",
                    label,
                )

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            logger.error(
                "Email event | status=schedule_failed | label={} | reason=no_event_loop",
                label,
            )
            return

        loop.create_task(_runner(), name=f"email:{label}")
        logger.info("Email event | status=scheduled | label={}", label)

    def enqueue(self, message: EmailMessage) -> None:
        """Schedule non-critical delivery without blocking the HTTP response."""
        self._schedule(self.send_message(message), label=message.template_key.value)

    def schedule_welcome_email(self, *, customer_name: str, customer_email: str) -> None:
        """Send welcome mail after registration without blocking the HTTP response."""

        async def _send() -> None:
            log = await self.send_welcome_email(
                customer_name=customer_name,
                customer_email=customer_email,
            )
            logger.info(
                "Welcome email delivered | email_log_id={} | recipient={}",
                log.id,
                customer_email,
            )

        self._schedule(_send(), label=EmailTemplateKey.WELCOME.value)

    def schedule_order_emails(self, payload: OrderEmailPayload) -> None:
        """Send customer confirmation + chef notification after order commit."""

        async def _send_all() -> None:
            if not payload.brand_name:
                payload.brand_name = self._settings.email_brand_name
            try:
                confirmation = await self.send_order_confirmation(payload)
                logger.info(
                    "Order confirmation delivered | email_log_id={} | order_number={} | recipient={}",
                    confirmation.id,
                    payload.order_number,
                    payload.customer_email,
                )
            except Exception:
                logger.exception(
                    "Order confirmation failed | order_number={} | recipient={}",
                    payload.order_number,
                    payload.customer_email,
                )
            try:
                chef = await self.send_chef_notification(payload)
                logger.info(
                    "Chef notification delivered | email_log_id={} | order_number={} | recipients={}",
                    chef.id,
                    payload.order_number,
                    chef.meta.get("recipients") if chef.meta else None,
                )
            except Exception:
                logger.exception(
                    "Chef notification failed | order_number={}",
                    payload.order_number,
                )

        self._schedule(_send_all(), label="order_emails")

    def enqueue_welcome_email(self, *, customer_name: str, customer_email: str) -> None:
        """Backward-compatible alias for schedule_welcome_email()."""
        self.schedule_welcome_email(
            customer_name=customer_name,
            customer_email=customer_email,
        )

    def enqueue_order_emails(self, payload: OrderEmailPayload) -> None:
        """Backward-compatible alias for schedule_order_emails()."""
        self.schedule_order_emails(payload)

    async def send_welcome_email(self, *, customer_name: str, customer_email: str) -> EmailLog:
        return await self.send_message(
            self.build_welcome_message(
                customer_name=customer_name,
                customer_email=customer_email,
            )
        )

    async def send_chef_notification(self, payload: OrderEmailPayload) -> EmailLog:
        if not payload.brand_name:
            payload.brand_name = self._settings.email_brand_name
        return await self.send_message(self.build_chef_notification_message(payload))

    async def notify_admin_new_order(self, payload: OrderEmailPayload) -> EmailLog:
        if not payload.brand_name:
            payload.brand_name = self._settings.email_brand_name
        return await self.send_message(self.build_order_notification_message(payload))

    async def send_order_confirmation(self, payload: OrderEmailPayload) -> EmailLog:
        if not payload.brand_name:
            payload.brand_name = self._settings.email_brand_name
        return await self.send_message(self.build_order_confirmation_message(payload))

    async def send_contact_email(
        self,
        *,
        name: str,
        email: str,
        phone: str | None,
        subject: str,
        message: str,
        submission_time: datetime | None = None,
        client_ip: str | None = None,
    ) -> EmailLog:
        """Deliver contact-form notification to CONTACT_RECEIVER_EMAIL (awaited)."""
        return await self.send_message(
            self.build_contact_admin_message(
                name=name,
                email=email,
                phone=phone,
                subject=subject,
                message=message,
                submission_time=submission_time,
                client_ip=client_ip,
            )
        )

    def _schedule_contact_confirmation(
        self,
        *,
        name: str,
        email: str,
        subject: str,
    ) -> None:
        async def _send() -> None:
            log = await self.send_message(
                self.build_contact_confirmation_message(
                    name=name,
                    email=email,
                    subject=subject,
                )
            )
            logger.info(
                "Contact confirmation delivered | email_log_id={} | recipient={}",
                log.id,
                email,
            )

        self._schedule(_send(), label=EmailTemplateKey.CONTACT_CONFIRMATION.value)

    async def notify_contact_submission(
        self,
        *,
        name: str,
        email: str,
        phone: str | None,
        subject: str,
        message: str,
        submission_time: datetime | None = None,
        client_ip: str | None = None,
    ) -> None:
        """
        Await admin inbox delivery; queue customer auto-reply best-effort.

        Raises ExternalServiceException (HTTP 502) when Brevo admin delivery fails.
        """
        await self.send_contact_email(
            name=name,
            email=email,
            phone=phone,
            subject=subject,
            message=message,
            submission_time=submission_time,
            client_ip=client_ip,
        )
        self._schedule_contact_confirmation(name=name, email=email, subject=subject)

    async def send_order_emails(self, payload: OrderEmailPayload) -> dict[str, EmailLog]:
        """Send customer confirmation and chef notification in parallel."""
        if not payload.brand_name:
            payload.brand_name = self._settings.email_brand_name
        confirmation, chef = await asyncio.gather(
            self.send_order_confirmation(payload),
            self.send_chef_notification(payload),
        )
        return {"confirmation": confirmation, "chef_notification": chef}

    # Backward-compatible async alias used by OrderService
    async def notify_owner_new_order(self, payload: OrderEmailPayload) -> EmailLog:
        return await self.notify_admin_new_order(payload)

    async def send_admin_test(
        self,
        *,
        to: str | None = None,
        message: str | None = None,
    ) -> EmailLog:
        recipients = [to] if to else None
        return await self.send_message(
            self.build_admin_test_message(recipients=recipients, message=message)
        )

    async def send_owner_test(
        self,
        *,
        to: str | None = None,
        message: str | None = None,
    ) -> EmailLog:
        return await self.send_admin_test(to=to, message=message)
