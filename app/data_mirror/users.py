"""Users JSON mirror — dual-write companion to PostgreSQL."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from loguru import logger

from app.data_mirror.base import BaseJsonMirror

DEFAULT_USERS_JSON_PATH = Path("data") / "users.json"


class UsersJsonMirror(BaseJsonMirror):
    """
    Mirrors `User` rows into `data/users.json` after Postgres writes.

    PostgreSQL remains the source of truth. Mirror failures are logged and
    re-raised so callers can decide whether to surface them.
    """

    def __init__(self, file_path: Path | None = None) -> None:
        super().__init__(file_path or DEFAULT_USERS_JSON_PATH)

    def serialize(self, entity: Any) -> dict[str, Any]:
        role = getattr(entity, "role", None)
        return {
            "id": str(getattr(entity, "id", "")),
            "phone_number": getattr(entity, "phone_number", None),
            "full_name": getattr(entity, "full_name", None),
            "email": getattr(entity, "email", None),
            "role": getattr(role, "value", str(role) if role is not None else None),
            "is_active": getattr(entity, "is_active", None),
            "is_verified": getattr(entity, "is_verified", None),
            "avatar_url": getattr(entity, "avatar_url", None),
            "last_login": getattr(entity, "last_login", None),
            "created_at": getattr(entity, "created_at", None),
            "updated_at": getattr(entity, "updated_at", None),
        }

    async def upsert(self, entity: Any) -> None:
        try:
            rows = self.read_all()
            serialized = self.serialize(entity)
            entity_id = serialized["id"]
            replaced = False
            for index, row in enumerate(rows):
                if str(row.get("id")) == entity_id:
                    rows[index] = serialized
                    replaced = True
                    break
            if not replaced:
                rows.append(serialized)
            self.write_all(rows)
            logger.info("User mirrored to users.json | id={}", entity_id)
        except Exception:
            logger.exception("Failed to mirror user to users.json | id={}", getattr(entity, "id", None))
            raise

    async def remove(self, entity_id: str) -> None:
        try:
            rows = self.read_all()
            filtered = [row for row in rows if str(row.get("id")) != entity_id]
            self.write_all(filtered)
            logger.info("User removed from users.json | id={}", entity_id)
        except Exception:
            logger.exception("Failed to remove user from users.json | id={}", entity_id)
            raise
