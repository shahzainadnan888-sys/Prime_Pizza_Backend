"""Soft-delete aware helpers on the generic repository base."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base import Base


class BaseRepository[ModelT: Base]:
    """Thin data-access base prepared for repository pattern adoption."""

    def __init__(self, session: AsyncSession, model: type[ModelT]) -> None:
        self.session = session
        self.model = model

    def _not_deleted(self, stmt: Select[Any]) -> Select[Any]:
        """Apply soft-delete filter when the model exposes `deleted_at`."""
        deleted_at = getattr(self.model, "deleted_at", None)
        if deleted_at is not None:
            return stmt.where(deleted_at.is_(None))
        return stmt

    async def get_by_id(self, entity_id: UUID, *, include_deleted: bool = False) -> ModelT | None:
        entity = await self.session.get(self.model, entity_id)
        if entity is None:
            return None
        if (
            not include_deleted
            and getattr(entity, "deleted_at", None) is not None
        ):
            return None
        return entity

    async def list_all(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
        include_deleted: bool = False,
    ) -> list[ModelT]:
        stmt = select(self.model).limit(limit).offset(offset)
        if not include_deleted:
            stmt = self._not_deleted(stmt)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count(self, *, include_deleted: bool = False) -> int:
        stmt = select(func.count()).select_from(self.model)
        if not include_deleted:
            stmt = self._not_deleted(stmt)
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def add(self, entity: ModelT) -> ModelT:
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def soft_delete(self, entity: ModelT) -> ModelT:
        """Mark an entity as soft-deleted (no hard DELETE)."""
        if not hasattr(entity, "deleted_at"):
            msg = f"{self.model.__name__} does not support soft delete"
            raise TypeError(msg)
        entity.deleted_at = datetime.now(UTC)
        await self.session.flush()
        return entity

    async def delete(self, entity: ModelT) -> None:
        """Hard delete — prefer soft_delete for domain entities."""
        await self.session.delete(entity)
        await self.session.flush()

    async def execute_raw(self, *args: Any, **kwargs: Any) -> Any:
        """Escape hatch for advanced queries in subclasses."""
        return await self.session.execute(*args, **kwargs)
