"""Owner connectivity test email template."""

from __future__ import annotations

from app.common.enums import EmailTemplateKey
from app.emails.base_layout import kv_row, section_heading, wrap_html
from app.emails.payloads import OwnerTestEmailPayload, RenderedEmail
from app.emails.safe import escape_html, sanitize_header


def render_owner_test(payload: OwnerTestEmailPayload) -> RenderedEmail:
    subject = sanitize_header(f"{payload.brand_name} — Email System Test")
    body = "".join(
        [
            section_heading("Connectivity Check"),
            kv_row("Status", "<strong>Resend configuration verified</strong>"),
            kv_row("Message", escape_html(payload.message)),
        ]
    )
    html = wrap_html(
        brand_name=payload.brand_name,
        logo_url=payload.logo_url,
        title="Email System Test",
        body_rows=body,
    )
    text = "\n".join(
        [
            f"{payload.brand_name} — Email System Test",
            "Status: Resend configuration verified",
            f"Message: {payload.message}",
        ]
    )
    return RenderedEmail(
        template_key=EmailTemplateKey.OWNER_TEST,
        subject=subject,
        html=html,
        text=text,
    )
