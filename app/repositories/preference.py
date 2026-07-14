"""User preference repository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import UserPreference
from app.repositories.base import BaseRepository


class PreferenceRepository(BaseRepository[UserPreference]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, UserPreference)

    async def get_for_user(self, user_id: UUID) -> UserPreference | None:
        stmt = select(UserPreference).where(
            UserPreference.user_id == user_id,
            UserPreference.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create(self, user_id: UUID) -> UserPreference:
        existing = await self.get_for_user(user_id)
        if existing is not None:
            return existing
        pref = UserPreference(user_id=user_id)
        return await self.add(pref)
