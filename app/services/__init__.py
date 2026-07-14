"""Service layer public exports.

Keep this module free of FastAPI dependency imports to avoid circular imports
with `app.authorization.policy` (which imports `BaseService`).
"""

from app.services.auth import AuthService
from app.services.avatar import AvatarService
from app.services.base import BaseService
from app.services.otp_provider import LocalOTPProvider, OTPProvider, OTPService
from app.services.phone import PhoneValidationService
from app.services.profile import ProfileService
from app.services.user import UserService
from app.services.user_sync import UserSyncService

__all__ = [
    "AuthService",
    "AvatarService",
    "BaseService",
    "LocalOTPProvider",
    "OTPProvider",
    "OTPService",
    "PhoneValidationService",
    "ProfileService",
    "UserService",
    "UserSyncService",
]
