"""User profile and account settings service."""

from __future__ import annotations

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.users import (
    AvatarUploadResponse,
    UserProfileResponse,
    UserProfileUpdateRequest,
)
from app.services.avatar import AvatarService
from app.services.base import BaseService
from app.services.profile import ProfileService
from app.services.user_sync import UserSyncService


class UserService(BaseService):
    """Account settings and avatar orchestration for the authenticated user."""

    service_name = "user"

    def __init__(
        self,
        *,
        session: AsyncSession,
        avatar_service: AvatarService,
        user_sync: UserSyncService,
        profile_service: ProfileService | None = None,
    ) -> None:
        self._session = session
        self._users = UserRepository(session)
        self._avatar = avatar_service
        self._sync = user_sync
        self._profile = profile_service or ProfileService(session=session, user_sync=user_sync)

    def get_profile(self, user: User) -> UserProfileResponse:
        return self._profile.get_profile(user)

    async def update_profile(
        self,
        user: User,
        payload: UserProfileUpdateRequest,
    ) -> UserProfileResponse:
        return await self._profile.update_profile(user, payload)

    async def upload_avatar(
        self,
        user: User,
        *,
        file_obj,
        filename: str,
        content_type: str | None,
        size: int,
    ) -> AvatarUploadResponse:
        uploaded = self._avatar.upload_avatar(
            file_obj=file_obj,
            user_id=str(user.id),
            filename=filename,
            content_type=content_type,
            size=size,
        )
        user.avatar_url = uploaded.url
        user.avatar_public_id = uploaded.public_id
        await self._session.flush()
        await self._session.commit()
        await self._session.refresh(user)
        await self._sync.sync_user_best_effort(user)
        logger.info("Avatar uploaded | user_id={}", user.id)
        return AvatarUploadResponse(avatar_url=uploaded.url)

    async def delete_avatar(self, user: User) -> UserProfileResponse:
        public_id = user.avatar_public_id
        self._avatar.delete_avatar(public_id=public_id, user_id=str(user.id))
        user.avatar_url = None
        user.avatar_public_id = None
        await self._session.flush()
        await self._session.commit()
        await self._session.refresh(user)
        await self._sync.sync_user_best_effort(user)
        logger.info("Avatar deleted | user_id={}", user.id)
        return UserProfileResponse.model_validate(user)

    async def deactivate_account(self, user: User) -> UserProfileResponse:
        await self._users.deactivate(user)
        await self._session.commit()
        await self._session.refresh(user)
        await self._sync.sync_user_best_effort(user)
        logger.info("Account deactivated | user_id={}", user.id)
        return UserProfileResponse.model_validate(user)

    async def soft_delete_account(self, user: User) -> None:
        await self._users.soft_delete_account(user)
        await self._session.commit()
        await self._sync.remove_user(str(user.id))
        logger.info("Account soft-deleted | user_id={}", user.id)
