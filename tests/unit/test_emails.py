"""Unit tests for Brevo email templates and delivery helpers."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from app.common.enums import EmailDeliveryStatus, EmailTemplateKey
from app.config.settings import Settings
from app.emails.payloads import EmailMessage, OrderEmailLineItem, OrderEmailPayload
from app.emails.safe import escape_html, sanitize_header
from app.services.email_service import EmailService
from app.utils.email_helpers import render_template


def _minimal_settings(**overrides: object) -> Settings:
    base = {
        "SECRET_KEY": "x" * 32,
        "DATABASE_URL": "postgresql+asyncpg://u:p@localhost/db",
        "REDIS_URL": "redis://localhost:6379/0",
        "CLOUDINARY_CLOUD_NAME": "c",
        "CLOUDINARY_API_KEY": "k",
        "CLOUDINARY_API_SECRET": "s",
        "CHEF_EMAIL": "chef123@gmail.com",
        "CHEF_PASSWORD": "Chef123",
        "ADMIN_EMAIL": "admin@example.com",
        "CONTACT_RECEIVER_EMAIL": "contact@example.com",
        "OWNER_EMAIL": "owner@example.com",
        "BREVO_API_KEY": "xkeysib-test",
        "BREVO_SENDER_EMAIL": "noreply@example.com",
        "BREVO_SENDER_NAME": "Prime Pizza",
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
        delivery_address="Street 1, Lahore",
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
            )
        ],
        brand_name="Prime Pizza",
    )


def test_welcome_template_escapes_and_renders() -> None:
    html = render_template(
        "welcome_email.html",
        {
            "brand_name": "Prime Pizza",
            "customer_name": "Ada <script>",
            "customer_email": "ada@example.com",
        },
    )
    assert "<script>" not in html
    assert "Ada &lt;script&gt;" in html
    assert "ada@example.com" in html


def test_chef_notification_message_targets_chef_inbox() -> None:
    service = EmailService(settings=_minimal_settings())
    message = service.build_chef_notification_message(_order_payload())
    assert message.template_key == EmailTemplateKey.ORDER_NOTIFICATION
    assert message.to == ["chef123@gmail.com"]
    assert "PP-2026-000001" in message.subject
    assert "Kitchen" in message.subject


def test_chef_notification_recipients() -> None:
    settings = _minimal_settings(CHEF_EMAIL="Chef123@gmail.com")
    assert settings.chef_notification_recipients() == ["chef123@gmail.com"]


def test_validate_brevo_required_skips_test_env() -> None:
    settings = _minimal_settings(APP_ENV="test", BREVO_API_KEY="")
    settings.validate_brevo_required()  # must not raise


def test_validate_brevo_required_raises_when_missing() -> None:
    settings = _minimal_settings(APP_ENV="development", BREVO_API_KEY="")
    with pytest.raises(ValueError, match="BREVO_API_KEY"):
        settings.validate_brevo_required()


def test_order_notification_message_builds_invoice() -> None:
    service = EmailService(settings=_minimal_settings())
    message = service.build_order_notification_message(_order_payload())
    assert message.template_key == EmailTemplateKey.ORDER_NOTIFICATION
    assert "PP-2026-000001" in message.subject
    assert "Ali &lt;script&gt;" in message.html
    assert "Pepperoni" in message.html
    assert "1100.00" in message.html
    assert message.to == ["admin@example.com"]


def test_welcome_message() -> None:
    service = EmailService(settings=_minimal_settings())
    message = service.build_welcome_message(
        customer_name="Ada",
        customer_email="ada@example.com",
    )
    assert message.template_key == EmailTemplateKey.WELCOME
    assert message.to == ["ada@example.com"]


def test_contact_messages() -> None:
    service = EmailService(settings=_minimal_settings())
    admin = service.build_contact_admin_message(
        name="Bob",
        email="bob@example.com",
        phone="+923001234567",
        subject="Catering",
        message="Need 20 pizzas",
    )
    confirm = service.build_contact_confirmation_message(
        name="Bob",
        email="bob@example.com",
        subject="Catering",
    )
    assert admin.template_key == EmailTemplateKey.CONTACT_NOTIFICATION
    assert confirm.template_key == EmailTemplateKey.CONTACT_CONFIRMATION
    assert admin.to[0] == "contact@example.com"
    assert "admin@example.com" in admin.to
    assert confirm.to == ["bob@example.com"]
    assert "Submitted at" in admin.text or "submission" in admin.html.lower() or "Submitted" in admin.html


def test_order_confirmation_message() -> None:
    service = EmailService(settings=_minimal_settings())
    message = service.build_order_confirmation_message(_order_payload())
    assert message.template_key == EmailTemplateKey.ORDER_CONFIRMATION
    assert message.to == ["ali@example.com"]
    assert "Tax" in message.html or "tax" in message.html
    assert "1100.00" in message.html


def test_sanitize_header_blocks_injection() -> None:
    assert "\n" not in sanitize_header("Hello\nBcc: evil@x.com")
    assert escape_html("<b>") == "&lt;b&gt;"


def test_admin_email_recipients_merges_extras() -> None:
    settings = _minimal_settings(
        OWNER_NOTIFICATION_EMAILS="second@example.com, admin@example.com",
    )
    recipients = settings.admin_email_recipients()
    assert recipients[0] == "admin@example.com"
    assert recipients.count("admin@example.com") == 1
    assert "second@example.com" in recipients


def test_contact_notification_recipients_prefer_contact_inbox() -> None:
    settings = _minimal_settings()
    recipients = settings.contact_notification_recipients()
    assert recipients[0] == "contact@example.com"
    assert "admin@example.com" in recipients


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
            self.meta = {"recipients": ["admin@example.com"]}
            self.recipient = "admin@example.com"
            self.subject = "Test"
            self.template_key = EmailTemplateKey.ADMIN_TEST

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
        log.retry_count = int(kwargs.get("retry_count") or 0)
        if kwargs.get("failure_reason"):
            log.failure_reason = str(kwargs["failure_reason"])
        return log

    async def _sleep(_delay: float) -> None:
        return None

    monkeypatch.setattr("app.services.email_service.is_brevo_configured", lambda: True)
    monkeypatch.setattr("app.services.email_service.ensure_brevo_initialized", lambda _s: True)
    monkeypatch.setattr("app.services.email_service.send_email_via_brevo", _boom)
    monkeypatch.setattr(service, "_persist_log", _persist)
    monkeypatch.setattr(
        "app.services.email_service.async_session_factory",
        lambda: (lambda: SessionCtx()),
    )
    monkeypatch.setattr(asyncio, "sleep", _sleep)

    from app.core.exceptions import ExternalServiceException

    with pytest.raises(ExternalServiceException):
        await service.send_message(
            EmailMessage(
                template_key=EmailTemplateKey.ADMIN_TEST,
                to=["admin@example.com"],
                subject="Test",
                html="<p>hi</p>",
                text="hi",
            )
        )
    assert calls["n"] == 3
    assert log.status == EmailDeliveryStatus.FAILED


@pytest.mark.asyncio
async def test_send_skipped_when_unconfigured(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = _minimal_settings(BREVO_API_KEY="", EMAIL_ENABLED=True)
    service = EmailService(settings=settings)

    class FakeLog:
        def __init__(self) -> None:
            self.id = uuid4()
            self.status = EmailDeliveryStatus.SKIPPED
            self.retry_count = 0
            self.failure_reason = "Brevo not configured or EMAIL_ENABLED=false"
            self.provider_message_id = None
            self.sent_at = None
            self.meta = {"recipients": ["admin@example.com"]}
            self.recipient = "admin@example.com"
            self.subject = "Test"
            self.template_key = EmailTemplateKey.ADMIN_TEST

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
    monkeypatch.setattr(
        "app.services.email_service.async_session_factory",
        lambda: (lambda: SessionCtx()),
    )
    monkeypatch.setattr("app.services.email_service.is_brevo_configured", lambda: False)
    monkeypatch.setattr("app.services.email_service.ensure_brevo_initialized", lambda _s: False)

    from app.core.exceptions import ExternalServiceException

    with pytest.raises(ExternalServiceException):
        await service.send_message(
            EmailMessage(
                template_key=EmailTemplateKey.ADMIN_TEST,
                to=["admin@example.com"],
                subject="Test",
                html="<p>hi</p>",
                text="hi",
            )
        )
