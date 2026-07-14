"""Owner new-order transactional template (HTML + plain text)."""

from __future__ import annotations

from app.common.enums import EmailTemplateKey
from app.emails.base_layout import (
    BRAND_BORDER,
    BRAND_DARK,
    BRAND_MUTED,
    BRAND_RED,
    kv_row,
    section_heading,
    wrap_html,
)
from app.emails.payloads import OrderEmailPayload, RenderedEmail
from app.emails.safe import escape_html, format_datetime, format_money, sanitize_header


def _address_html(address: str) -> str:
    return escape_html(address).replace("\n", "<br />")


def _items_html(payload: OrderEmailPayload) -> str:
    rows: list[str] = []
    for item in payload.items:
        extras = ""
        if item.extras:
            bits = [
                f"{escape_html(extra.name)} ×{extra.quantity}"
                for extra in item.extras
            ]
            extras = (
                f'<div style="font-size:12px;color:{BRAND_MUTED};margin-top:4px;">'
                f"Extras: {', '.join(bits)}</div>"
            )
        variant = (
            f'<div style="font-size:12px;color:{BRAND_MUTED};margin-top:2px;">'
            f"{escape_html(item.variant_name)}</div>"
            if item.variant_name
            else ""
        )
        image = ""
        if item.image_url:
            image = (
                f'<td width="64" valign="top" style="padding-right:12px;">'
                f'<img src="{escape_html(item.image_url)}" alt="" width="56" height="56" '
                f'style="display:block;border-radius:6px;object-fit:cover;border:1px solid {BRAND_BORDER};" />'
                f"</td>"
            )
        rows.append(
            f'<tr><td style="padding:12px 24px;border-top:1px solid {BRAND_BORDER};">'
            f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>'
            f"{image}"
            f'<td valign="top" style="font-family:Arial,Helvetica,sans-serif;">'
            f'<div style="font-size:15px;font-weight:600;color:{BRAND_DARK};">'
            f"{escape_html(item.product_name)}</div>"
            f"{variant}{extras}"
            f'<div style="font-size:13px;color:{BRAND_MUTED};margin-top:6px;">'
            f"Qty {item.quantity} · {format_money(item.unit_price, currency=payload.currency)} each</div>"
            f"</td>"
            f'<td valign="top" align="right" style="font-family:Arial,Helvetica,sans-serif;'
            f'font-size:14px;font-weight:600;color:{BRAND_DARK};white-space:nowrap;">'
            f"{format_money(item.subtotal, currency=payload.currency)}</td>"
            f"</tr></table></td></tr>"
        )
    return "".join(rows)


def render_owner_new_order(payload: OrderEmailPayload) -> RenderedEmail:
    subject = sanitize_header(f"🍕 New Prime Pizza Order #{payload.order_number}")
    currency = payload.currency or "PKR"

    body = "".join(
        [
            section_heading("Order Summary"),
            kv_row("Order Number", f"<strong>{escape_html(payload.order_number)}</strong>"),
            kv_row("Order Date", escape_html(format_datetime(payload.order_created_at))),
            kv_row("Order Status", escape_html(payload.order_status)),
            kv_row("Payment Method", escape_html(payload.payment_method)),
            kv_row("Payment Status", escape_html(payload.payment_status)),
            kv_row(
                "Prep Estimate",
                escape_html(
                    f"{payload.estimated_preparation_minutes} minutes"
                    if payload.estimated_preparation_minutes is not None
                    else "—"
                ),
            ),
            section_heading("Customer"),
            kv_row("Name", escape_html(payload.customer_name)),
            kv_row("Phone", escape_html(payload.customer_phone)),
            kv_row("Email", escape_html(payload.customer_email or "—")),
            kv_row("Delivery Address", _address_html(payload.delivery_address)),
            kv_row("Customer Notes", escape_html(payload.customer_notes or "—")),
            section_heading("Ordered Items"),
            _items_html(payload),
            section_heading("Totals"),
            kv_row("Subtotal", format_money(payload.subtotal, currency=currency)),
            kv_row("Discount", format_money(payload.discount, currency=currency)),
            kv_row("Delivery Fee", format_money(payload.delivery_fee, currency=currency)),
            kv_row("Tax", format_money(payload.tax, currency=currency)),
            (
                f'<tr><td style="padding:12px 24px 20px 24px;">'
                f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">'
                f'<tr><td style="font-size:16px;font-weight:700;color:{BRAND_DARK};'
                f'font-family:Arial,Helvetica,sans-serif;">Grand Total</td>'
                f'<td align="right" style="font-size:18px;font-weight:700;color:{BRAND_RED};'
                f'font-family:Arial,Helvetica,sans-serif;">'
                f"{format_money(payload.grand_total, currency=currency)}</td></tr></table></td></tr>"
            ),
        ]
    )

    html = wrap_html(
        brand_name=payload.brand_name,
        logo_url=payload.logo_url,
        title=f"New Order {payload.order_number}",
        body_rows=body,
    )

    item_lines: list[str] = []
    for item in payload.items:
        line = f"- {item.product_name}"
        if item.variant_name:
            line += f" ({item.variant_name})"
        line += f" x{item.quantity} = {format_money(item.subtotal, currency=currency)}"
        item_lines.append(line)
        for extra in item.extras:
            item_lines.append(
                f"    + {extra.name} x{extra.quantity} "
                f"({format_money(extra.unit_price, currency=currency)} each)"
            )

    text = "\n".join(
        [
            f"{payload.brand_name} — New Order Notification",
            f"Order Number: {payload.order_number}",
            f"Order Date: {format_datetime(payload.order_created_at)}",
            f"Order Status: {payload.order_status}",
            f"Payment Method: {payload.payment_method}",
            f"Payment Status: {payload.payment_status}",
            "",
            "Customer",
            f"Name: {payload.customer_name}",
            f"Phone: {payload.customer_phone}",
            f"Email: {payload.customer_email or '—'}",
            f"Address: {payload.delivery_address}",
            f"Notes: {payload.customer_notes or '—'}",
            "",
            "Items",
            *item_lines,
            "",
            f"Subtotal: {format_money(payload.subtotal, currency=currency)}",
            f"Discount: {format_money(payload.discount, currency=currency)}",
            f"Delivery Fee: {format_money(payload.delivery_fee, currency=currency)}",
            f"Tax: {format_money(payload.tax, currency=currency)}",
            f"Grand Total: {format_money(payload.grand_total, currency=currency)}",
            (
                f"Estimated Prep: {payload.estimated_preparation_minutes} minutes"
                if payload.estimated_preparation_minutes is not None
                else "Estimated Prep: —"
            ),
        ]
    )

    return RenderedEmail(
        template_key=EmailTemplateKey.OWNER_NEW_ORDER,
        subject=subject,
        html=html,
        text=text,
    )
