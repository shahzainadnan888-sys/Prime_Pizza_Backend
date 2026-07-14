"""Cloudinary uploads for catalog images (products / categories / deals)."""

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
class CatalogUploadedImage:
    url: str
    public_id: str


class CatalogCloudinaryService(BaseService):
    """Shared Cloudinary uploader for menu media assets."""

    service_name = "catalog_cloudinary"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def validate_upload(self, *, filename: str, content_type: str | None, size: int) -> None:
        if size <= 0:
            raise ValidationException("Empty image upload is not allowed")
        if size > self._settings.product_image_max_bytes:
            raise ValidationException(
                f"Image exceeds maximum size of {self._settings.product_image_max_bytes} bytes",
                details={"max_bytes": self._settings.product_image_max_bytes},
            )
        if not is_allowed_image(filename):
            raise ValidationException("Unsupported image type. Allowed: jpg, jpeg, png, webp, gif")
        if not content_type or content_type not in self._settings.avatar_allowed_content_types:
            raise ValidationException(
                "Unsupported or missing image content type",
                details={"content_type": content_type},
            )

    def upload(
        self,
        *,
        file_obj: BinaryIO,
        folder: str,
        public_id: str | None,
        filename: str,
        content_type: str | None,
        size: int,
    ) -> CatalogUploadedImage:
        self.validate_upload(filename=filename, content_type=content_type, size=size)
        if not is_valid_image_content(file_obj):
            raise ValidationException("Uploaded file is not a valid image")
        if not is_cloudinary_configured():
            raise ExternalServiceException("Cloudinary is not configured", service="cloudinary")

        try:
            kwargs: dict = {
                "folder": folder,
                "resource_type": "image",
                "overwrite": bool(public_id),
            }
            if public_id:
                kwargs["public_id"] = public_id
            result = cloudinary.uploader.upload(file_obj, **kwargs)
            url = str(result.get("secure_url") or result.get("url") or "")
            pid = str(result.get("public_id") or "")
            if not url or not pid:
                raise ExternalServiceException(
                    "Cloudinary upload returned incomplete data",
                    service="cloudinary",
                )
            self.log_info("Catalog image uploaded | public_id={}", pid)
            return CatalogUploadedImage(url=url, public_id=pid)
        except (ValidationException, ExternalServiceException):
            raise
        except Exception as exc:
            logger.error("Cloudinary catalog upload failed | folder={}", folder)
            raise ExternalServiceException(
                "Failed to upload image. Please try again later.",
                service="cloudinary",
            ) from exc

    def delete(self, public_id: str | None) -> None:
        if not public_id:
            return
        if not is_cloudinary_configured():
            raise ExternalServiceException("Cloudinary is not configured", service="cloudinary")
        try:
            cloudinary.uploader.destroy(public_id, invalidate=True)
            self.log_info("Catalog image deleted | public_id={}", public_id)
        except Exception as exc:
            logger.error("Cloudinary catalog delete failed | public_id={}", public_id)
            raise ExternalServiceException(
                "Failed to delete image. Please try again later.",
                service="cloudinary",
            ) from exc
