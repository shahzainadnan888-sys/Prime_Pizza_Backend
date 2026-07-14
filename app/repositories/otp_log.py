"""OTP log repository for audit trail (no raw OTP codes)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import OTPVerificationStatus
from app.models.otp_log import OTPLog
from app.repositories.base import BaseRepository


class OTPLogRepository(BaseRepository[OTPLog]):
    """Persist OTP challenge metadata for auditing."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, OTPLog)

    async def record_send(
        self,
        *,
        phone_number: str,
        provider_sid: str | None,
        expire_seconds: int,
    ) -> OTPLog:
        entry = OTPLog(
            phone_number=phone_number,
            status=OTPVerificationStatus.PENDING,
            expires_at=datetime.now(UTC) + timedelta(seconds=expire_seconds),
            attempt_count=0,
            provider_sid=provider_sid,
            code_hash=None,
        )
        return await self.add(entry)

    async def record_result(
        self,
        *,
        phone_number: str,
        status: OTPVerificationStatus,
        attempt_count: int,
        provider_sid: str | None = None,
    ) -> OTPLog:
        entry = OTPLog(
            phone_number=phone_number,
            status=status,
            expires_at=datetime.now(UTC),
            attempt_count=attempt_count,
            provider_sid=provider_sid,
            code_hash=None,
        )
        return await self.add(entry)
