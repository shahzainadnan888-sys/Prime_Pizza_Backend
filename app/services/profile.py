"""User profile service (read / update own profile)."""

from __future__ import annotations

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, ValidationException
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.users import UserProfileResponse, UserProfileUpdateRequest
from app.services.base import BaseService
from app.services.user_sync import UserSyncService


class ProfileService(BaseService):
    """Authenticated user's own profile operations."""

    service_name = "profile"

    def __init__(
        self,
        *,
        session: AsyncSession,
        user_sync: UserSyncService,
    ) -> None:
        self._session = session
        self._users = UserRepository(session)
        self._sync = user_sync

    def get_profile(self, user: User) -> UserProfileResponse:
        return UserProfileResponse.model_validate(user)

    async def update_profile(
        self,
        user: User,
        payload: UserProfileUpdateRequest,
    ) -> UserProfileResponse:
        data = payload.model_dump(exclude_unset=True)
        if not data:
            raise ValidationException("No profile fields provided")

        if "email" in data and data["email"] is not None:
            existing = await self._users.get_by_email(str(data["email"]))
            if existing is not None and existing.id != user.id:
                raise ConflictException("Email is already in use")
            user.email = str(data["email"])

        if "full_name" in data and data["full_name"] is not None:
            user.full_name = str(data["full_name"]).strip()

        await self._session.flush()
        await self._session.commit()
        await self._session.refresh(user)
        await self._sync.sync_user_best_effort(user)
        logger.info("Profile updated | user_id={}", user.id)
        return UserProfileResponse.model_validate(user)
