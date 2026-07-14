"""Base layout shared by transactional HTML emails."""

from __future__ import annotations

from app.emails.safe import escape_html

BRAND_RED = "#C41E3A"
BRAND_DARK = "#1A1A1A"
BRAND_MUTED = "#6B7280"
BRAND_BG = "#F7F3EF"
BRAND_CARD = "#FFFFFF"
BRAND_BORDER = "#E8E0D8"


def wrap_html(*, brand_name: str, logo_url: str | None, title: str, body_rows: str) -> str:
    """Table-based responsive shell compatible with Gmail / Outlook / Apple Mail."""
    brand = escape_html(brand_name)
    safe_title = escape_html(title)
    if logo_url:
        logo_block = (
            f'<img src="{escape_html(logo_url)}" alt="{brand}" width="120" '
            f'style="display:block;border:0;outline:none;text-decoration:none;max-width:120px;" />'
        )
    else:
        logo_block = (
            f'<div style="font-size:22px;font-weight:700;color:{BRAND_RED};'
            f'letter-spacing:0.5px;">{brand}</div>'
            f'<div style="font-size:12px;color:{BRAND_MUTED};margin-top:4px;">Restaurant Order Alert</div>'
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta http-equiv="X-UA-Compatible" content="IE=edge" />
  <title>{safe_title}</title>
</head>
<body style="margin:0;padding:0;background-color:{BRAND_BG};font-family:Georgia,'Times New Roman',serif;">
  <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color:{BRAND_BG};">
    <tr>
      <td align="center" style="padding:24px 12px;">
        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="600" style="width:100%;max-width:600px;background-color:{BRAND_CARD};border:1px solid {BRAND_BORDER};">
          <tr>
            <td style="background-color:{BRAND_DARK};padding:20px 24px;">
              {logo_block}
            </td>
          </tr>
          <tr>
            <td style="padding:8px 24px 0 24px;">
              <div style="height:4px;background-color:{BRAND_RED};width:72px;"></div>
            </td>
          </tr>
          <tr>
            <td style="padding:16px 24px 8px 24px;">
              <h1 style="margin:0;font-size:22px;line-height:1.3;color:{BRAND_DARK};font-family:Arial,Helvetica,sans-serif;">{safe_title}</h1>
            </td>
          </tr>
          {body_rows}
          <tr>
            <td style="padding:24px;border-top:1px solid {BRAND_BORDER};">
              <p style="margin:0;font-size:12px;line-height:1.5;color:{BRAND_MUTED};font-family:Arial,Helvetica,sans-serif;">
                This is an automated transactional notification from {brand}.
                Do not reply to this message if the mailbox is unmonitored.
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def section_heading(text: str) -> str:
    return (
        f'<tr><td style="padding:20px 24px 8px 24px;">'
        f'<div style="font-size:13px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;'
        f'color:{BRAND_RED};font-family:Arial,Helvetica,sans-serif;">{escape_html(text)}</div>'
        f"</td></tr>"
    )


def kv_row(label: str, value: str) -> str:
    return (
        f'<tr><td style="padding:4px 24px;">'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">'
        f'<tr>'
        f'<td width="38%" style="font-size:13px;color:{BRAND_MUTED};font-family:Arial,Helvetica,sans-serif;'
        f'vertical-align:top;padding:6px 0;">{escape_html(label)}</td>'
        f'<td style="font-size:14px;color:{BRAND_DARK};font-family:Arial,Helvetica,sans-serif;'
        f'vertical-align:top;padding:6px 0;">{value}</td>'
        f"</tr></table></td></tr>"
    )
