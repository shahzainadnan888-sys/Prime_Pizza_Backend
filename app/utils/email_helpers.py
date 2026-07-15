"""HTML email template loading and placeholder rendering helpers."""

from __future__ import annotations

import re
from html import escape
from pathlib import Path
from typing import Any

TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"

_PLACEHOLDER_RE = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")


def load_template(filename: str) -> str:
    """Load an HTML template from ``app/templates``."""
    path = TEMPLATES_DIR / filename
    if not path.is_file():
        msg = f"Email template not found: {filename}"
        raise FileNotFoundError(msg)
    return path.read_text(encoding="utf-8")


def html_escape(value: Any) -> str:
    """Escape a value for safe HTML interpolation."""
    if value is None:
        return ""
    return escape(str(value), quote=True)


def render_template(filename: str, context: dict[str, Any], *, autoescape: bool = True) -> str:
    """
    Render ``{{placeholder}}`` values from an HTML template.

    By default values are HTML-escaped. Pass pre-sanitized HTML fragments
    (e.g. table rows) with autoescape disabled for that key by embedding
    already-escaped HTML in the context and setting ``autoescape=False``.
    """
    template = load_template(filename)

    def _replace(match: re.Match[str]) -> str:
        key = match.group(1)
        raw = context.get(key, "")
        if raw is None:
            return ""
        if autoescape and key not in context.get("_raw_html_keys", set()):
            # Keys listed in _raw_html_keys are inserted as trusted HTML fragments.
            raw_keys = context.get("_raw_html_keys") or set()
            if key in raw_keys:
                return str(raw)
            return html_escape(raw)
        return str(raw)

    # Support _raw_html_keys for fragments like product rows
    raw_keys = set(context.get("_raw_html_keys") or set())

    def _replace_with_raw(match: re.Match[str]) -> str:
        key = match.group(1)
        raw = context.get(key, "")
        if raw is None:
            return ""
        if key in raw_keys:
            return str(raw)
        return html_escape(raw) if autoescape else str(raw)

    return _PLACEHOLDER_RE.sub(_replace_with_raw, template)


def plain_text_from_context(lines: list[str]) -> str:
    """Build a simple plaintext alternative body."""
    return "\n".join(line for line in lines if line is not None)
