"""Users JSON mirror — dual-write companion to PostgreSQL."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from loguru import logger

from app.data_mirror.base import BaseJsonMirror

DEFAULT_USERS_JSON_PATH = Path("data") / "user.json"
# Legacy filename kept for one release of dual-compat reads during migration.
LEGACY_USERS_JSON_PATH = Path("data") / "users.json"


class UsersJsonMirror(BaseJsonMirror):
    """
    Mirrors `User` rows into `data/user.json` after Postgres writes.

    PostgreSQL remains the source of truth. Mirror failures are logged and
    re-raised so callers can decide whether to surface them.
    """

    def __init__(self, file_path: Path | None = None) -> None:
        path = file_path or DEFAULT_USERS_JSON_PATH
        # Migrate legacy users.json → user.json once when creating the default path.
        if file_path is None and not path.exists() and LEGACY_USERS_JSON_PATH.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(LEGACY_USERS_JSON_PATH.read_text(encoding="utf-8"), encoding="utf-8")
            logger.info("Migrated legacy users.json → user.json")
        super().__init__(path)

    def serialize(self, entity: Any) -> dict[str, Any]:
        role = getattr(entity, "role", None)
        return {
            "id": str(getattr(entity, "id", "")),
            "first_name": getattr(entity, "first_name", None),
            "last_name": getattr(entity, "last_name", None),
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
            rows = await self.read_all_async()
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
            await self.write_all_async(rows)
            logger.info("User mirrored to user.json | id={}", entity_id)
        except Exception:
            logger.exception(
                "Failed to mirror user to user.json | id={}",
                getattr(entity, "id", None),
            )
            raise

    async def remove(self, entity_id: str) -> None:
        try:
            rows = await self.read_all_async()
            filtered = [row for row in rows if str(row.get("id")) != entity_id]
            await self.write_all_async(filtered)
            logger.info("User removed from user.json | id={}", entity_id)
        except Exception:
            logger.exception("Failed to remove user from user.json | id={}", entity_id)
            raise
