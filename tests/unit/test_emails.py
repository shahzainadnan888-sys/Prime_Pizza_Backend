"""Unit tests for transactional email templates and delivery helpers."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from app.common.enums import EmailDeliveryStatus, EmailTemplateKey
from app.config.settings import Settings
from app.emails.payloads import (
    EmailMessage,
    OrderEmailLineExtra,
    OrderEmailLineItem,
    OrderEmailPayload,
    OwnerTestEmailPayload,
)
from app.emails.renderer import EmailRenderer
from app.emails.safe import escape_html, sanitize_header
from app.emails.templates.owner_new_order import render_owner_new_order
from app.emails.templates.owner_test import render_owner_test
from app.services.email import EmailService


def _minimal_settings(**overrides: object) -> Settings:
    base = {
        "SECRET_KEY": "x" * 32,
        "DATABASE_URL": "postgresql+asyncpg://u:p@localhost/db",
        "REDIS_URL": "redis://localhost:6379/0",
        "CLOUDINARY_CLOUD_NAME": "c",
        "CLOUDINARY_API_KEY": "k",
        "CLOUDINARY_API_SECRET": "s",
        "OWNER_PHONE_NUMBER": "+923001234567",
        "OWNER_EMAIL": "owner@example.com",
        "RESEND_API_KEY": "re_test",
        "EMAIL_ENABLED": True,
        "EMAIL_MAX_RETRIES": 3,
        "EMAIL_RETRY_BACKOFF_SECONDS": 0.1,
    }
    base.update(overrides)
    return Settings(**base)  # type: ignore[arg-type]


def _order_payload() -> OrderEmailPayload:
    return OrderEmailPayload(
        order_id=uuid4(),
        order_number="PP-2026-000001",
        order_created_at=datetime(2026, 7, 14, 12, 0, tzinfo=UTC),
        customer_name="Ali <script>",
        customer_phone="+923001112233",
        customer_email="ali@example.com",
        delivery_address="Street 1\nLahore",
        payment_method="Cash On Delivery",
        payment_status="Pending",
        order_status="Pending",
        currency="PKR",
        subtotal=Decimal("1000.00"),
        delivery_fee=Decimal("150.00"),
        tax=Decimal("0.00"),
        discount=Decimal("50.00"),
        grand_total=Decimal("1100.00"),
        customer_notes="Extra spicy",
        estimated_preparation_minutes=35,
        items=[
            OrderEmailLineItem(
                product_name="Pepperoni",
                quantity=2,
                unit_price=Decimal("500.00"),
                subtotal=Decimal("1000.00"),
                variant_name="Large",
                image_url="https://cdn.example.com/p.png",
                extras=[
                    OrderEmailLineExtra(
                        name="Olives",
                        quantity=1,
                        unit_price=Decimal("50.00"),
                    )
                ],
            )
        ],
        brand_name="Prime Pizza",
        logo_url=None,
    )


def test_html_escapes_customer_name() -> None:
    rendered = render_owner_new_order(_order_payload())
    assert "<script>" not in rendered.html
    assert "Ali &lt;script&gt;" in rendered.html
    assert "PP-2026-000001" in rendered.html
    assert "cdn.example.com/p.png" in rendered.html


def test_plain_text_contains_totals_and_items() -> None:
    rendered = render_owner_new_order(_order_payload())
    assert "Order Number: PP-2026-000001" in rendered.text
    assert "Pepperoni" in rendered.text
    assert "Olives" in rendered.text
    assert "Grand Total: PKR 1100.00" in rendered.text


def test_subject_is_professional() -> None:
    rendered = render_owner_new_order(_order_payload())
    assert rendered.subject == "🍕 New Prime Pizza Order #PP-2026-000001"
    assert "\n" not in rendered.subject


def test_sanitize_header_blocks_injection() -> None:
    assert "\n" not in sanitize_header("Hello\nBcc: evil@x.com")
    assert escape_html("<b>") == "&lt;b&gt;"


def test_owner_test_template() -> None:
    rendered = render_owner_test(OwnerTestEmailPayload(message="ping"))
    assert rendered.template_key == EmailTemplateKey.OWNER_TEST
    assert "ping" in rendered.html
    assert "ping" in rendered.text


def test_renderer_registry() -> None:
    renderer = EmailRenderer()
    rendered = renderer.render_owner_new_order(_order_payload())
    assert rendered.template_key == EmailTemplateKey.OWNER_NEW_ORDER


def test_owner_email_recipients_merges_extras() -> None:
    settings = _minimal_settings(
        OWNER_NOTIFICATION_EMAILS="second@example.com, owner@example.com",
    )
    recipients = settings.owner_email_recipients()
    assert recipients[0] == "owner@example.com"
    assert recipients.count("owner@example.com") == 1
    assert "second@example.com" in recipients


def test_build_owner_new_order_message() -> None:
    service = EmailService(settings=_minimal_settings())
    message = service.build_owner_new_order_message(_order_payload())
    assert message.template_key == EmailTemplateKey.OWNER_NEW_ORDER
    assert "PP-2026-000001" in message.subject
    assert message.to == ["owner@example.com"]


@pytest.mark.asyncio
async def test_retry_exhaustion_marks_failed(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = _minimal_settings()
    service = EmailService(settings=settings)
    calls = {"n": 0}

    async def _boom(**_kwargs: object) -> str:
        calls["n"] += 1
        raise RuntimeError("network")

    class FakeLog:
        def __init__(self) -> None:
            self.id = uuid4()
            self.status = EmailDeliveryStatus.QUEUED
            self.retry_count = 0
            self.failure_reason: str | None = None
            self.provider_message_id: str | None = None
            self.sent_at = None
            self.meta = {"recipients": ["owner@example.com"]}
            self.recipient = "owner@example.com"
            self.subject = "Test"
            self.template_key = EmailTemplateKey.OWNER_TEST

    log = FakeLog()

    class FakeSession:
        async def commit(self) -> None:
            return None

        async def refresh(self, _obj: object) -> None:
            return None

    class SessionCtx:
        async def __aenter__(self) -> FakeSession:
            return FakeSession()

        async def __aexit__(self, *_args: object) -> bool:
            return False

    async def _persist(_session: object, **kwargs: object) -> FakeLog:
        log.status = kwargs["status"]  # type: ignore[assignment]
        return log

    async def _sleep(_delay: float) -> None:
        return None

    monkeypatch.setattr("app.services.email.is_resend_configured", lambda: True)
    monkeypatch.setattr("app.services.email.send_email_via_resend", _boom)
    monkeypatch.setattr("app.services.email.get_resend_from_email", lambda: "onboarding@resend.dev")
    monkeypatch.setattr(service, "_persist_log", _persist)
    monkeypatch.setattr("app.services.email.async_session_factory", lambda: (lambda: SessionCtx()))
    monkeypatch.setattr(asyncio, "sleep", _sleep)

    result = await service.send_message(
        EmailMessage(
            template_key=EmailTemplateKey.OWNER_TEST,
            to=["owner@example.com"],
            subject="Test",
            html="<p>hi</p>",
            text="hi",
        )
    )
    assert calls["n"] == 3
    assert result.status == EmailDeliveryStatus.FAILED
    assert result.retry_count == 3


@pytest.mark.asyncio
async def test_send_skipped_when_unconfigured(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = _minimal_settings(RESEND_API_KEY="", EMAIL_ENABLED=True)
    service = EmailService(settings=settings)

    class FakeLog:
        def __init__(self) -> None:
            self.id = uuid4()
            self.status = EmailDeliveryStatus.SKIPPED
            self.retry_count = 0
            self.failure_reason = "Resend not configured or EMAIL_ENABLED=false"
            self.provider_message_id = None
            self.sent_at = None
            self.meta = {"recipients": ["owner@example.com"]}
            self.recipient = "owner@example.com"
            self.subject = "Test"
            self.template_key = EmailTemplateKey.OWNER_TEST

    class FakeSession:
        async def commit(self) -> None:
            return None

        async def refresh(self, _obj: object) -> None:
            return None

    class SessionCtx:
        async def __aenter__(self) -> FakeSession:
            return FakeSession()

        async def __aexit__(self, *_args: object) -> bool:
            return False

    async def _persist(_session: object, **kwargs: object) -> FakeLog:
        log = FakeLog()
        log.status = kwargs["status"]  # type: ignore[assignment]
        return log

    monkeypatch.setattr(service, "_persist_log", _persist)
    monkeypatch.setattr("app.services.email.async_session_factory", lambda: (lambda: SessionCtx()))
    monkeypatch.setattr("app.services.email.is_resend_configured", lambda: False)

    result = await service.send_message(
        EmailMessage(
            template_key=EmailTemplateKey.OWNER_TEST,
            to=["owner@example.com"],
            subject="Test",
            html="<p>hi</p>",
            text="hi",
        )
    )
    assert result.status == EmailDeliveryStatus.SKIPPED
