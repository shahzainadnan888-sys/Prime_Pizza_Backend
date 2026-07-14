"""Phone number validation and normalization service."""

from __future__ import annotations

from app.core.exceptions import InvalidPhoneException
from app.utils.phone import is_valid_e164, normalize_phone


class PhoneValidationService:
    """Validate and normalize international phone numbers to E.164."""

    def normalize_and_validate(self, phone_number: str) -> str:
        normalized = normalize_phone(phone_number)
        if not is_valid_e164(normalized):
            raise InvalidPhoneException(
                "Phone number must be a valid E.164 number (e.g. +923001234567)",
                details={"phone_number": phone_number},
            )
        return normalized
