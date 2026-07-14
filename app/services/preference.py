"""User preference service."""

from __future__ import annotations

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationException
from app.models.user import User
from app.repositories.preference import PreferenceRepository
from app.schemas.users import PreferenceResponse, PreferenceUpdateRequest
from app.services.base import BaseService


class PreferenceService(BaseService):
    service_name = "preference"

    def __init__(self, *, session: AsyncSession) -> None:
        self._session = session
        self._prefs = PreferenceRepository(session)

    async def get_preferences(self, user: User) -> PreferenceResponse:
        pref = await self._prefs.get_or_create(user.id)
        await self._session.commit()
        await self._session.refresh(pref)
        return PreferenceResponse.model_validate(pref)

    async def update_preferences(
        self,
        user: User,
        payload: PreferenceUpdateRequest,
    ) -> PreferenceResponse:
        data = payload.model_dump(exclude_unset=True)
        if not data:
            raise ValidationException("No preference fields provided")
        pref = await self._prefs.get_or_create(user.id)
        for key, value in data.items():
            setattr(pref, key, value)
        await self._session.flush()
        await self._session.commit()
        await self._session.refresh(pref)
        logger.info("Preference updated | user_id={}", user.id)
        return PreferenceResponse.model_validate(pref)
