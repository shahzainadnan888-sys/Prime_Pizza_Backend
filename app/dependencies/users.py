"""FastAPI dependencies for the user module."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import Settings
from app.dependencies.database import get_db_session
from app.dependencies.settings import get_app_settings
from app.services.address import AddressService
from app.services.avatar import AvatarService
from app.services.notification import UserNotificationService
from app.services.preference import PreferenceService
from app.services.profile import ProfileService
from app.services.user import UserService
from app.services.user_sync import UserSyncService


def get_avatar_service(settings: Settings = Depends(get_app_settings)) -> AvatarService:
    return AvatarService(settings)


def get_user_sync_service() -> UserSyncService:
    return UserSyncService()


def get_profile_service(
    session: AsyncSession = Depends(get_db_session),
    user_sync: UserSyncService = Depends(get_user_sync_service),
) -> ProfileService:
    return ProfileService(session=session, user_sync=user_sync)


def get_user_service(
    session: AsyncSession = Depends(get_db_session),
    avatar_service: AvatarService = Depends(get_avatar_service),
    user_sync: UserSyncService = Depends(get_user_sync_service),
    profile_service: ProfileService = Depends(get_profile_service),
) -> UserService:
    return UserService(
        session=session,
        avatar_service=avatar_service,
        user_sync=user_sync,
        profile_service=profile_service,
    )


def get_address_service(
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_app_settings),
) -> AddressService:
    return AddressService(session=session, settings=settings)


def get_preference_service(
    session: AsyncSession = Depends(get_db_session),
) -> PreferenceService:
    return PreferenceService(session=session)


def get_user_notification_service(
    session: AsyncSession = Depends(get_db_session),
) -> UserNotificationService:
    return UserNotificationService(session=session)
