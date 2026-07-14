"""System settings repository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.system_setting import SystemSetting
from app.repositories.base import BaseRepository


class SystemSettingRepository(BaseRepository[SystemSetting]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, SystemSetting)

    async def get_by_key(self, key: str) -> SystemSetting | None:
        stmt = select(SystemSetting).where(
            SystemSetting.key == key,
            SystemSetting.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all_settings(self) -> list[SystemSetting]:
        stmt = (
            select(SystemSetting)
            .where(SystemSetting.deleted_at.is_(None))
            .order_by(SystemSetting.key.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
