"""Phone number helpers."""

from __future__ import annotations

import re

_E164_PATTERN = re.compile(r"^\+[1-9]\d{7,14}$")


def normalize_phone(phone: str) -> str:
    """Strip spaces/dashes; keep leading + for E.164-ish numbers."""
    cleaned = re.sub(r"[\s\-()]", "", phone.strip())
    return cleaned


def is_valid_e164(phone: str) -> bool:
    """Validate E.164 phone format."""
    return bool(_E164_PATTERN.match(normalize_phone(phone)))
