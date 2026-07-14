"""Unit tests for users.json mirror synchronization."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
from app.common.enums import UserRole
from app.data_mirror.users import UsersJsonMirror
from app.models.user import User


@pytest.mark.asyncio
async def test_users_json_mirror_upsert_and_update(tmp_path: Path) -> None:
    path = tmp_path / "users.json"
    mirror = UsersJsonMirror(path)
    user = User(
        id=uuid4(),
        phone_number="+923001234567",
        full_name="Customer 4567",
        role=UserRole.CUSTOMER,
        is_active=True,
        is_verified=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        version=1,
    )
    await mirror.upsert(user)
    rows = mirror.read_all()
    assert len(rows) == 1
    assert rows[0]["phone_number"] == "+923001234567"

    user.full_name = "Updated Name"
    await mirror.upsert(user)
    rows = mirror.read_all()
    assert len(rows) == 1
    assert rows[0]["full_name"] == "Updated Name"

    await mirror.remove(str(user.id))
    assert mirror.read_all() == []
