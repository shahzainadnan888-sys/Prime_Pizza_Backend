"""API tests for owner transactional email endpoints."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.common.enums import EmailDeliveryStatus, EmailTemplateKey, UserRole
from app.config.settings import get_settings
from app.main import create_app
from app.models.email_log import EmailLog
from app.models.user import User
from fastapi.testclient import TestClient


def _user(*, role: UserRole) -> User:
    return User(
        id=uuid4(),
        first_name="Test",
        last_name="User",
        phone_number="+923001234567",
        full_name="Tester",
        email="test@example.com",
        password_hash="hashed",
        role=role,
        is_active=True,
        is_verified=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        version=1,
    )


def _override_auth(app, user: User) -> None:
    from app.dependencies import auth as auth_deps

    async def _current() -> User:
        return user

    app.dependency_overrides[auth_deps.get_current_user] = _current
    app.dependency_overrides[auth_deps.get_verified_user] = _current


def test_test_email_requires_auth() -> None:
    app = create_app(settings=get_settings())
    with TestClient(app) as client:
        assert client.post("/api/v1/admin/test-email").status_code == 401


def test_customer_cannot_send_test_email() -> None:
    app = create_app(settings=get_settings())
    _override_auth(app, _user(role=UserRole.CUSTOMER))
    with TestClient(app) as client:
        assert client.post("/api/v1/admin/test-email", json={}).status_code == 403


def test_owner_test_email_endpoint(monkeypatch) -> None:
    app = create_app(settings=get_settings())
    _override_auth(app, _user(role=UserRole.CHEF))

    from app.dependencies.email import get_email_service
    from app.services.email import EmailService

    async def _send(self, *, to=None, message=None):
        return EmailLog(
            id=uuid4(),
            recipient=to or "owner@example.com",
            subject="Prime Pizza — Email System Test",
            template_key=EmailTemplateKey.OWNER_TEST,
            status=EmailDeliveryStatus.SENT,
            retry_count=0,
            failure_reason=None,
            provider_message_id="msg_123",
            sent_at=datetime.now(UTC),
            meta={"recipients": [to or "owner@example.com"]},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            version=1,
        )

    monkeypatch.setattr(EmailService, "send_owner_test", _send)
    app.dependency_overrides[get_email_service] = lambda: EmailService(settings=get_settings())

    with TestClient(app) as client:
        resp = client.post("/api/v1/admin/test-email", json={"message": "hello"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["status"] == "sent"
        assert body["data"]["email_log_id"] is not None

