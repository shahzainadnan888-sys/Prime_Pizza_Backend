"""OTP verification log model (storage only — no auth flow)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.common.enums import OTPVerificationStatus
from app.database.types import pg_enum
from app.models.base import BaseModel


class OTPLog(BaseModel):
    """Audit trail for OTP challenge attempts."""

    __tablename__ = "otp_logs"
    __table_args__ = (
        Index("ix_otp_logs_phone_number", "phone_number"),
        Index("ix_otp_logs_status", "status"),
        Index("ix_otp_logs_created_at", "created_at"),
        Index("ix_otp_logs_expires_at", "expires_at"),
    )

    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[OTPVerificationStatus] = mapped_column(
        pg_enum(OTPVerificationStatus, name="otp_verification_status"),
        nullable=False,
        default=OTPVerificationStatus.PENDING,
        server_default=OTPVerificationStatus.PENDING.value,
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    provider_sid: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # Never store raw OTP codes in production logs; hash placeholder for future use.
    code_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
