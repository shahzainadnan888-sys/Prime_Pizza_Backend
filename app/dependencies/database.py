"""Database session dependency."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db


async def get_db_session() -> AsyncGenerator[AsyncSession]:
    """Yield a request-scoped SQLAlchemy async session."""
    async for session in get_db():
        yield session
