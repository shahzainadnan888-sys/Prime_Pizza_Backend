"""User synchronization between PostgreSQL and user.json."""

from __future__ import annotations

from loguru import logger

from app.data_mirror.users import UsersJsonMirror
from app.models.user import User
from app.services.base import BaseService


class UserSyncService(BaseService):
    """Keep `data/user.json` / `data/users.json` synchronized after Postgres user writes."""

    service_name = "user_sync"

    def __init__(self, mirror: UsersJsonMirror | None = None) -> None:
        self._mirror = mirror or UsersJsonMirror()

    async def sync_user(self, user: User) -> None:
        """Upsert user into the JSON mirror after a successful DB write."""
        await self._mirror.upsert(user)
        self.log_info("User sync completed | user_id={}", user.id)

    async def remove_user(self, user_id: str) -> None:
        await self._mirror.remove(user_id)
        self.log_info("User sync removal completed | user_id={}", user_id)

    async def sync_user_best_effort(self, user: User) -> None:
        """
        Sync without failing the auth response.

        Postgres remains source of truth; mirror issues are logged for ops.
        """
        try:
            await self.sync_user(user)
        except Exception:
            logger.exception(
                "User JSON mirror failed after Postgres commit | user_id={}",
                user.id,
            )
