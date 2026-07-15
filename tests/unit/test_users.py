"""Unit tests for avatar validation, schemas, and sync."""

from __future__ import annotations

from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from uuid import uuid4

import pytest
from app.common.enums import UserRole
from app.config.settings import get_settings
from app.core.exceptions import ValidationException
from app.data_mirror.users import UsersJsonMirror
from app.models.user import User
from app.schemas.users import AddressCreateRequest, UserProfileUpdateRequest
from app.services.avatar import AvatarService
from app.services.user_sync import UserSyncService
from app.utils.images import is_valid_image_content, sniff_image_type
from pydantic import ValidationError


def test_avatar_rejects_oversized_file() -> None:
    settings = get_settings()
    service = AvatarService(settings)
    with pytest.raises(ValidationException):
        service.validate_upload(
            filename="avatar.jpg",
            content_type="image/jpeg",
            size=settings.avatar_max_bytes + 1,
        )


def test_avatar_rejects_bad_extension() -> None:
    settings = get_settings()
    service = AvatarService(settings)
    with pytest.raises(ValidationException):
        service.validate_upload(
            filename="avatar.exe",
            content_type="image/jpeg",
            size=100,
        )


def test_avatar_rejects_bad_content_type() -> None:
    settings = get_settings()
    service = AvatarService(settings)
    with pytest.raises(ValidationException):
        service.validate_upload(
            filename="avatar.jpg",
            content_type="application/pdf",
            size=100,
        )


def test_image_magic_bytes_detection() -> None:
    jpeg = BytesIO(b"\xff\xd8\xff\xe0" + b"\x00" * 20)
    png = BytesIO(b"\x89PNG\r\n\x1a\n" + b"\x00" * 20)
    fake = BytesIO(b"not-an-image")
    assert sniff_image_type(jpeg) == "jpeg"
    assert sniff_image_type(png) == "png"
    assert is_valid_image_content(jpeg) is True
    assert is_valid_image_content(fake) is False


def test_address_schema_validates_phone_and_coords() -> None:
    AddressCreateRequest(
        title="Home",
        recipient_name="Ali Khan",
        phone_number="+923001234567",
        street="123 Main Street",
        city="Lahore",
        province="Punjab",
        postal_code="54000",
        latitude="31.5204",
        longitude="74.3587",
    )
    with pytest.raises(ValidationError):
        AddressCreateRequest(
            title="Home",
            recipient_name="Ali Khan",
            phone_number="bad",
            street="123 Main Street",
            city="Lahore",
            province="Punjab",
            postal_code="54000",
        )
    with pytest.raises(ValidationError):
        AddressCreateRequest(
            title="Home",
            recipient_name="Ali Khan",
            phone_number="+923001234567",
            street="123 Main Street",
            city="Lahore",
            province="Punjab",
            postal_code="54000",
            latitude="999",
        )


def test_profile_update_schema_lengths() -> None:
    UserProfileUpdateRequest(full_name="Ab")
    with pytest.raises(ValidationError):
        UserProfileUpdateRequest(full_name="A")


@pytest.mark.asyncio
async def test_user_sync_includes_avatar_url(tmp_path: Path) -> None:
    path = tmp_path / "users.json"
    sync = UserSyncService(mirror=UsersJsonMirror(path))
    user = User(
        id=uuid4(),
        first_name="Customer",
        last_name="4567",
        phone_number="+923001234567",
        full_name="Customer 4567",
        email="customer@example.com",
        password_hash="hashed",
        role=UserRole.CUSTOMER,
        is_active=True,
        is_verified=True,
        avatar_url="https://res.cloudinary.com/demo/image/upload/v1/a.jpg",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        version=1,
    )
    await sync.sync_user(user)
    rows = UsersJsonMirror(path).read_all()
    assert rows[0]["avatar_url"] == user.avatar_url
    assert rows[0]["full_name"] == "Customer 4567"

    user.full_name = "Synced Name"
    await sync.sync_user_best_effort(user)
    rows = UsersJsonMirror(path).read_all()
    assert rows[0]["full_name"] == "Synced Name"

