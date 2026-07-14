"""Generic service base for future domain modules."""

from __future__ import annotations

from loguru import logger


class BaseService:
    """Application service base with shared logging helpers."""

    service_name: str = "base"

    def log_info(self, message: str, *args: object, **kwargs: object) -> None:
        logger.bind(service=self.service_name).info(message, *args, **kwargs)

    def log_error(self, message: str, *args: object, **kwargs: object) -> None:
        logger.bind(service=self.service_name).error(message, *args, **kwargs)
