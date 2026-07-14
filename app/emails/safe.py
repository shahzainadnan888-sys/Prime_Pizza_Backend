"""Safe HTML / text helpers for transactional email templates."""

from __future__ import annotations

import html
import re
from decimal import Decimal

_HEADER_UNSAFE = re.compile(r"[\r\n\x00]")


def escape_html(value: object | None) -> str:
    """HTML-escape arbitrary values for safe insertion into templates."""
    if value is None:
        return ""
    return html.escape(str(value), quote=True)


def sanitize_header(value: str) -> str:
    """Strip CR/LF/NUL to prevent email header injection."""
    return _HEADER_UNSAFE.sub(" ", value).strip()


def format_money(amount: Decimal | float | int | str | None, *, currency: str = "PKR") -> str:
    if amount is None:
        return f"{currency} 0.00"
    try:
        value = Decimal(str(amount))
    except Exception:
        return f"{currency} 0.00"
    return f"{currency} {value.quantize(Decimal('0.01'))}"


def format_datetime(value: object | None) -> str:
    if value is None:
        return "—"
    text = str(value)
    if "T" in text:
        return text.replace("T", " ").split("+")[0].split(".")[0] + " UTC"
    return text
