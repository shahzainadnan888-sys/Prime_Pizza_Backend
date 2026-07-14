"""Cloudinary avatar upload / delete service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import BinaryIO

import cloudinary.uploader
from loguru import logger

from app.config.settings import Settings
from app.core.exceptions import ExternalServiceException, ValidationException
from app.integrations.cloudinary.client import is_cloudinary_configured
from app.services.base import BaseService
from app.utils.images import is_allowed_image, is_valid_image_content


@dataclass(frozen=True)
class UploadedImage:
    url: str
    public_id: str


class AvatarService(BaseService):
    """Upload and remove profile avatars via Cloudinary."""

    service_name = "avatar"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def validate_upload(self, *, filename: str, content_type: str | None, size: int) -> None:
        if size <= 0:
            raise ValidationException("Empty image upload is not allowed")
        if size > self._settings.avatar_max_bytes:
            raise ValidationException(
                f"Image exceeds maximum size of {self._settings.avatar_max_bytes} bytes",
                details={"max_bytes": self._settings.avatar_max_bytes},
            )
        if not is_allowed_image(filename):
            raise ValidationException("Unsupported image type. Allowed: jpg, jpeg, png, webp, gif")
        if not content_type or content_type not in self._settings.avatar_allowed_content_types:
            raise ValidationException(
                "Unsupported or missing image content type",
                details={"content_type": content_type},
            )

    def upload_avatar(
        self,
        *,
        file_obj: BinaryIO,
        user_id: str,
        filename: str,
        content_type: str | None,
        size: int,
    ) -> UploadedImage:
        self.validate_upload(filename=filename, content_type=content_type, size=size)
        if not is_valid_image_content(file_obj):
            raise ValidationException("Uploaded file is not a valid image")
        if not is_cloudinary_configured():
            raise ExternalServiceException("Cloudinary is not configured", service="cloudinary")

        try:
            result = cloudinary.uploader.upload(
                file_obj,
                folder="prime_pizza/avatars",
                public_id=f"user_{user_id}",
                overwrite=True,
                resource_type="image",
                transformation=[{"width": 512, "height": 512, "crop": "fill", "gravity": "face"}],
            )
            url = str(result.get("secure_url") or result.get("url") or "")
            public_id = str(result.get("public_id") or "")
            if not url or not public_id:
                raise ExternalServiceException(
                    "Cloudinary upload returned incomplete data",
                    service="cloudinary",
                )
            self.log_info("Avatar uploaded | user_id={}", user_id)
            return UploadedImage(url=url, public_id=public_id)
        except ValidationException:
            raise
        except ExternalServiceException:
            raise
        except Exception as exc:
            logger.error("Cloudinary avatar upload failed | user_id={}", user_id)
            raise ExternalServiceException(
                "Failed to upload avatar. Please try again later.",
                service="cloudinary",
            ) from exc

    def delete_avatar(self, *, public_id: str | None, user_id: str) -> None:
        if not public_id:
            return
        if not is_cloudinary_configured():
            raise ExternalServiceException("Cloudinary is not configured", service="cloudinary")
        try:
            cloudinary.uploader.destroy(public_id, invalidate=True)
            self.log_info("Avatar deleted from Cloudinary | user_id={}", user_id)
        except Exception as exc:
            logger.error("Cloudinary avatar delete failed | user_id={}", user_id)
            raise ExternalServiceException(
                "Failed to delete avatar. Please try again later.",
                service="cloudinary",
            ) from exc
