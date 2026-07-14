"""User management API tests (profile, addresses, avatar, notifications)."""

from __future__ import annotations

from datetime import UTC, datetime
from io import BytesIO
from uuid import uuid4

from app.common.enums import NotificationType, UserRole
from app.config.settings import get_settings
from app.core.exceptions import NotFoundException, ValidationException
from app.main import create_app
from app.models.user import User
from app.schemas.users import (
    AddressResponse,
    AvatarUploadResponse,
    NotificationResponse,
    PreferenceResponse,
    UserProfileResponse,
)
from fastapi.testclient import TestClient


def _user(*, role: UserRole = UserRole.CUSTOMER, verified: bool = True) -> User:
    return User(
        id=uuid4(),
        phone_number="+923001234567",
        full_name="Customer 4567",
        email="customer@example.com",
        role=role,
        is_active=True,
        is_verified=verified,
        avatar_url=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        version=1,
    )


def _override_auth(app, user: User) -> None:
    from app.dependencies import auth as auth_deps

    async def _current_user() -> User:
        return user

    app.dependency_overrides[auth_deps.get_current_user] = _current_user
    app.dependency_overrides[auth_deps.get_verified_user] = _current_user


def _profile_response(user: User, **overrides) -> UserProfileResponse:
    base = {
        "id": user.id,
        "full_name": user.full_name,
        "phone_number": user.phone_number,
        "email": user.email,
        "avatar_url": user.avatar_url,
        "role": user.role,
        "is_verified": user.is_verified,
        "is_active": user.is_active,
        "created_at": user.created_at,
        "last_login": None,
    }
    base.update(overrides)
    return UserProfileResponse(**base)


def test_get_me_unauthorized() -> None:
    app = create_app(settings=get_settings())
    with TestClient(app) as client:
        response = client.get("/api/v1/users/me")
        assert response.status_code == 401


def test_get_and_patch_profile(monkeypatch) -> None:
    app = create_app(settings=get_settings())
    user = _user()
    _override_auth(app, user)

    async def _update(self, current, payload):
        if payload.full_name:
            current.full_name = payload.full_name
        if payload.email is not None:
            current.email = str(payload.email)
        return _profile_response(current)

    monkeypatch.setattr("app.services.user.UserService.get_profile", lambda self, u: _profile_response(u))
    monkeypatch.setattr("app.services.user.UserService.update_profile", _update)

    with TestClient(app) as client:
        get_resp = client.get("/api/v1/users/me")
        assert get_resp.status_code == 200
        assert get_resp.json()["data"]["phone_number"] == "+923001234567"

        patch_resp = client.patch(
            "/api/v1/users/me",
            json={"full_name": "Updated Name", "email": "new@example.com"},
        )
        assert patch_resp.status_code == 200
        assert patch_resp.json()["data"]["full_name"] == "Updated Name"
        assert patch_resp.json()["data"]["email"] == "new@example.com"

    app.dependency_overrides.clear()


def test_avatar_upload_and_delete(monkeypatch) -> None:
    app = create_app(settings=get_settings())
    user = _user()
    _override_auth(app, user)

    async def _upload(self, current, *, file_obj, filename, content_type, size):
        assert filename.endswith(".jpg")
        assert size > 0
        return AvatarUploadResponse(avatar_url="https://res.cloudinary.com/demo/image/upload/v1/avatar.jpg")

    async def _delete(self, current):
        current.avatar_url = None
        return _profile_response(current, avatar_url=None)

    monkeypatch.setattr("app.services.user.UserService.upload_avatar", _upload)
    monkeypatch.setattr("app.services.user.UserService.delete_avatar", _delete)

    # Minimal JPEG magic bytes
    jpeg = b"\xff\xd8\xff\xe0" + b"\x00" * 32

    with TestClient(app) as client:
        upload = client.post(
            "/api/v1/users/avatar",
            files={"file": ("avatar.jpg", BytesIO(jpeg), "image/jpeg")},
        )
        assert upload.status_code == 200
        assert "cloudinary" in upload.json()["data"]["avatar_url"]

        delete = client.delete("/api/v1/users/avatar")
        assert delete.status_code == 200
        assert delete.json()["data"]["avatar_url"] is None

    app.dependency_overrides.clear()


def test_address_crud_and_ownership(monkeypatch) -> None:
    app = create_app(settings=get_settings())
    user = _user()
    _override_auth(app, user)
    address_id = uuid4()
    now = datetime.now(UTC)

    stored: dict = {}

    async def _list(self, current):
        return list(stored.values())

    async def _create(self, current, payload):
        row = AddressResponse(
            id=address_id,
            title=payload.title,
            recipient_name=payload.recipient_name,
            phone_number=payload.phone_number,
            street=payload.street,
            area=payload.area,
            city=payload.city,
            province=payload.province,
            postal_code=payload.postal_code,
            country=payload.country,
            latitude=payload.latitude,
            longitude=payload.longitude,
            delivery_notes=payload.delivery_notes,
            is_default=True,
            created_at=now,
            updated_at=now,
        )
        stored[row.id] = row
        return row

    async def _update(self, current, addr_id, payload):
        if addr_id not in stored:
            raise NotFoundException("Address not found")
        row = stored[addr_id]
        data = payload.model_dump(exclude_unset=True)
        stored[addr_id] = row.model_copy(update=data)
        return stored[addr_id]

    async def _delete(self, current, addr_id):
        if addr_id not in stored:
            raise NotFoundException("Address not found")
        del stored[addr_id]

    async def _default(self, current, addr_id):
        if addr_id not in stored:
            raise NotFoundException("Address not found")
        stored[addr_id] = stored[addr_id].model_copy(update={"is_default": True})
        return stored[addr_id]

    monkeypatch.setattr("app.services.address.AddressService.list_addresses", _list)
    monkeypatch.setattr("app.services.address.AddressService.create_address", _create)
    monkeypatch.setattr("app.services.address.AddressService.update_address", _update)
    monkeypatch.setattr("app.services.address.AddressService.delete_address", _delete)
    monkeypatch.setattr("app.services.address.AddressService.set_default", _default)

    payload = {
        "title": "Home",
        "recipient_name": "Ali Khan",
        "phone_number": "+923001234567",
        "street": "123 Main Street",
        "area": "Gulberg",
        "city": "Lahore",
        "province": "Punjab",
        "postal_code": "54000",
        "country": "Pakistan",
        "is_default": True,
    }

    with TestClient(app) as client:
        create = client.post("/api/v1/users/addresses", json=payload)
        assert create.status_code == 201
        assert create.json()["data"]["is_default"] is True

        listing = client.get("/api/v1/users/addresses")
        assert listing.status_code == 200
        assert len(listing.json()["data"]) == 1

        patch = client.patch(
            f"/api/v1/users/addresses/{address_id}",
            json={"title": "Office"},
        )
        assert patch.status_code == 200
        assert patch.json()["data"]["title"] == "Office"

        default = client.patch(f"/api/v1/users/addresses/{address_id}/default")
        assert default.status_code == 200

        foreign = client.patch(f"/api/v1/users/addresses/{uuid4()}", json={"title": "X"})
        assert foreign.status_code == 404

        delete = client.delete(f"/api/v1/users/addresses/{address_id}")
        assert delete.status_code == 200

    app.dependency_overrides.clear()


def test_address_validation_rejects_bad_phone() -> None:
    app = create_app(settings=get_settings())
    user = _user()
    _override_auth(app, user)

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/users/addresses",
            json={
                "title": "Home",
                "recipient_name": "Ali Khan",
                "phone_number": "12345",
                "street": "123 Main Street",
                "city": "Lahore",
                "province": "Punjab",
                "postal_code": "54000",
            },
        )
        assert response.status_code == 422

    app.dependency_overrides.clear()


def test_preferences_get_and_update(monkeypatch) -> None:
    app = create_app(settings=get_settings())
    user = _user()
    _override_auth(app, user)

    prefs = PreferenceResponse(
        dark_mode=False,
        language="en",
        marketing_emails=False,
        marketing_sms=False,
        push_notifications=True,
        order_updates=True,
        promotional_notifications=False,
        preferred_currency="PKR",
        preferred_timezone="Asia/Karachi",
    )

    async def _get(self, current):
        return prefs

    async def _update(self, current, payload):
        data = payload.model_dump(exclude_unset=True)
        return prefs.model_copy(update=data)

    monkeypatch.setattr("app.services.preference.PreferenceService.get_preferences", _get)
    monkeypatch.setattr("app.services.preference.PreferenceService.update_preferences", _update)

    with TestClient(app) as client:
        get_resp = client.get("/api/v1/users/preferences")
        assert get_resp.status_code == 200
        assert get_resp.json()["data"]["language"] == "en"

        patch = client.patch("/api/v1/users/preferences", json={"dark_mode": True, "language": "ur"})
        assert patch.status_code == 200
        assert patch.json()["data"]["dark_mode"] is True
        assert patch.json()["data"]["language"] == "ur"

    app.dependency_overrides.clear()


def test_notification_apis(monkeypatch) -> None:
    app = create_app(settings=get_settings())
    user = _user()
    _override_auth(app, user)
    note_id = uuid4()
    now = datetime.now(UTC)
    note = NotificationResponse(
        id=note_id,
        title="Welcome",
        message="Thanks for joining Prime Pizza",
        notification_type=NotificationType.SYSTEM,
        is_read=False,
        created_at=now,
    )

    async def _list(self, current):
        return [note]

    async def _read(self, current, notification_id):
        if notification_id != note_id:
            raise NotFoundException("Notification not found")
        return note.model_copy(update={"is_read": True})

    async def _read_all(self, current):
        return 1

    async def _delete(self, current, notification_id):
        if notification_id != note_id:
            raise NotFoundException("Notification not found")

    monkeypatch.setattr(
        "app.services.notification.UserNotificationService.list_notifications",
        _list,
    )
    monkeypatch.setattr("app.services.notification.UserNotificationService.mark_read", _read)
    monkeypatch.setattr(
        "app.services.notification.UserNotificationService.mark_all_read",
        _read_all,
    )
    monkeypatch.setattr(
        "app.services.notification.UserNotificationService.delete_notification",
        _delete,
    )

    with TestClient(app) as client:
        listing = client.get("/api/v1/users/notifications")
        assert listing.status_code == 200
        assert len(listing.json()["data"]) == 1

        read_all = client.patch("/api/v1/users/notifications/read-all")
        assert read_all.status_code == 200
        assert "Marked 1" in read_all.json()["message"]

        read_one = client.patch(f"/api/v1/users/notifications/{note_id}/read")
        assert read_one.status_code == 200
        assert read_one.json()["data"]["is_read"] is True

        foreign = client.patch(f"/api/v1/users/notifications/{uuid4()}/read")
        assert foreign.status_code == 404

        delete = client.delete(f"/api/v1/users/notifications/{note_id}")
        assert delete.status_code == 200

    app.dependency_overrides.clear()


def test_account_deactivate(monkeypatch) -> None:
    app = create_app(settings=get_settings())
    user = _user()
    _override_auth(app, user)

    async def _deactivate(self, current):
        current.is_active = False
        return _profile_response(current, is_active=False)

    monkeypatch.setattr("app.services.user.UserService.deactivate_account", _deactivate)

    with TestClient(app) as client:
        response = client.post("/api/v1/users/me/deactivate")
        assert response.status_code == 200
        assert response.json()["data"]["is_active"] is False

    app.dependency_overrides.clear()


def test_max_addresses_enforced(monkeypatch) -> None:
    app = create_app(settings=get_settings())
    user = _user()
    _override_auth(app, user)

    async def _create(self, current, payload):
        raise ValidationException("Maximum of 10 addresses allowed")

    monkeypatch.setattr("app.services.address.AddressService.create_address", _create)

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/users/addresses",
            json={
                "title": "Home",
                "recipient_name": "Ali Khan",
                "phone_number": "+923001234567",
                "street": "123 Main Street",
                "city": "Lahore",
                "province": "Punjab",
                "postal_code": "54000",
            },
        )
        assert response.status_code == 422

    app.dependency_overrides.clear()
