"""Cloudinary client wrapper (configuration only)."""

from __future__ import annotations

import cloudinary
from loguru import logger

from app.config.settings import Settings

_configured: bool = False


def init_cloudinary(settings: Settings) -> None:
    """Configure the Cloudinary SDK globally."""
    global _configured

    cloud_name = (settings.cloudinary_cloud_name or "").strip()
    if not cloud_name or " " in cloud_name:
        logger.error(
            "Invalid CLOUDINARY_CLOUD_NAME={!r}. Use the cloud name from the "
            "Cloudinary dashboard (no spaces), e.g. 'dxxxxx' or 'prime-pizza'.",
            settings.cloudinary_cloud_name,
        )
        _configured = False
        return

    cloudinary.config(
        cloud_name=cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True,
    )
    _configured = True
    logger.info("Cloudinary client configured | cloud_name={}", cloud_name)


def close_cloudinary() -> None:
    """Mark Cloudinary as uninitialized."""
    global _configured
    _configured = False
    logger.info("Cloudinary client closed")


def is_cloudinary_configured() -> bool:
    return _configured


def get_cloudinary_config() -> dict[str, str | bool | None]:
    if not _configured:
        msg = "Cloudinary is not initialized."
        raise RuntimeError(msg)
    cfg = cloudinary.config()
    return {
        "cloud_name": cfg.cloud_name,
        "api_key": cfg.api_key,
        "secure": bool(cfg.secure),
    }
