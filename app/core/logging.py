"""Enterprise Loguru logging configuration."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

from loguru import logger

from app.config.settings import Settings

_SENSITIVE_PAIR = re.compile(
    r"(?i)(authorization|password|passwd|secret|api[_-]?key|refresh[_-]?token|"
    r"access[_-]?token|otp[_-]?code|verification[_-]?code)"
    r"([\"'=:\s]+)([^\s,\"']+)",
)
_BEARER_TOKEN = re.compile(r"(?i)bearer\s+[A-Za-z0-9\-_\.=]+")
_JWT_TOKEN = re.compile(r"eyJ[A-Za-z0-9_\-]+=*\.[A-Za-z0-9_\-]+=*\.[A-Za-z0-9_\-]+=*")


def _redact_record(record: dict[str, Any]) -> bool:
    """Strip secrets from log messages before they hit sinks."""
    try:
        message = str(record["message"])
        # Bearer / JWT first so keyword redaction does not leave token fragments.
        message = _BEARER_TOKEN.sub("Bearer [REDACTED]", message)
        message = _JWT_TOKEN.sub("[REDACTED_JWT]", message)
        message = _SENSITIVE_PAIR.sub(r"\1\2[REDACTED]", message)
        record["message"] = message
    except Exception:
        pass
    return True


def setup_logging(settings: Settings) -> None:
    """Configure console + rotating file logging for the active environment."""
    logger.remove()

    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "{extra[request_id]} | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    # Ensure request_id always exists for format string
    logger.configure(extra={"request_id": "-"})

    # Console
    logger.add(
        sys.stdout,
        level=settings.log_level,
        format=log_format,
        colorize=settings.is_development,
        backtrace=settings.debug,
        diagnose=settings.debug,
        enqueue=True,
        filter=_redact_record,
    )

    # File (daily rotation)
    logs_dir = Path("logs")
    logs_dir.mkdir(parents=True, exist_ok=True)

    logger.add(
        logs_dir / "prime_pizza_{time:YYYY-MM-DD}.log",
        level=settings.log_level,
        format=log_format,
        rotation="00:00",
        retention="30 days",
        compression="zip",
        enqueue=True,
        backtrace=settings.debug,
        diagnose=settings.debug,
        filter=_redact_record,
    )

    # Security / audit trail (auth failures, rate limits, ownership denials)
    def _security_only(record: dict[str, Any]) -> bool:
        msg = str(record["message"])
        if "Security event" not in msg and "auth failure" not in msg.lower():
            return False
        return _redact_record(record)

    logger.add(
        logs_dir / "prime_pizza_security_{time:YYYY-MM-DD}.log",
        level="WARNING",
        format=log_format,
        rotation="00:00",
        retention="90 days",
        compression="zip",
        enqueue=True,
        filter=_security_only,
    )

    if settings.is_production or settings.app_env == "staging":
        logger.add(
            logs_dir / "prime_pizza_structured_{time:YYYY-MM-DD}.log",
            level=settings.log_level,
            format="{message}",
            serialize=True,
            rotation="00:00",
            retention="30 days",
            compression="zip",
            enqueue=True,
            filter=_redact_record,
        )

    logger.info(
        "Logging initialized | env={} | level={}",
        settings.app_env,
        settings.log_level,
    )
