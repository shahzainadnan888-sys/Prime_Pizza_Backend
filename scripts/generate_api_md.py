#!/usr/bin/env python3
"""
Generate frontend API docs.

- api.md              lean integration guide (opens in Cursor)
- docs/api/*.md       per-module endpoint details
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

TAG_ORDER = [
    "Health",
    "Authentication",
    "Users",
    "Catalog",
    "Cart",
    "Wishlist",
    "Checkout",
    "Orders",
    "Admin Catalog",
    "Admin Orders",
    "Admin Email",
    "Admin Dashboard",
    "Admin Customers",
    "Admin Coupons",
    "Admin Notifications",
    "Admin Settings",
    "Admin Audit",
    "Admin Search",
]

GUIDE = r'''# Prime Pizza API - Frontend Integration Guide

> **For the frontend team.** Everything needed to integrate the backend without reading source code.
>
> Deep per-endpoint docs (large): see [`docs/api/`](docs/api/README.md)  
> Live Swagger (dev): http://127.0.0.1:8000/docs

**Version:** 1.0.0  
**API prefix:** `/api/v1`  
**Auth:** JWT Bearer after phone OTP (local Redis)
**Roles:** `customer` | `owner`

---

## 1. Base URL

| Environment | Example |
|-------------|---------|
| Local | `http://127.0.0.1:8000` |
| Staging | `https://api-staging.yourdomain.com` |
| Production | `https://api.yourdomain.com` |

Business routes: `{BASE_URL}/api/v1/...`

---

## 2. Response format (every endpoint)

### Success

```json
{
  "success": true,
  "message": "Human readable message",
  "data": {},
  "meta": null,
  "request_id": "uuid"
}
```

### Paginated list

```json
{
  "success": true,
  "message": "Success",
  "data": [],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 100,
    "total_pages": 5,
    "has_next": true,
    "has_previous": false
  },
  "request_id": "uuid"
}
```

### Error

```json
{
  "success": false,
  "message": "Human readable error",
  "error": { "code": "validation_error", "details": {} },
  "request_id": "uuid",
  "status_code": 422
}
```

Always check HTTP status + `success` + `error.code`.

---

## 3. Headers

| Header | When | Example |
|--------|------|---------|
| `Content-Type` | JSON POST/PUT/PATCH | `application/json` |
| `Authorization` | Protected routes | `Bearer <access_token>` |
| `X-Request-ID` | Optional tracing | any UUID |
| `Idempotency-Key` | Recommended on `POST /orders` | unique 8-64 char string |

Rate-limit headers on responses: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Policy`, `Retry-After` (on 429).

---

## 4. Authentication (must implement first)

```text
1. POST /api/v1/auth/send-otp     { "phone_number": "+923001234567" }
2. User enters SMS OTP
3. POST /api/v1/auth/verify-otp   { "phone_number": "+923001234567", "code": "123456" }
4. Save data.tokens.access_token + data.tokens.refresh_token
5. Send Authorization: Bearer <access_token> on protected calls
6. On 401 expired_token → POST /api/v1/auth/refresh { "refresh_token": "..." }
7. Logout → POST /api/v1/auth/logout (Bearer) optional body { "refresh_token" }
```

**Phone:** E.164 only (`+923001234567`).

**Tokens:**

| Token | Default lifetime | Note |
|-------|------------------|------|
| access | ~30 min (`expires_in`) | Put in Authorization header |
| refresh | ~30 days | Rotates on each refresh; discard old one |

**Roles:**

| Role | Meaning |
|------|---------|
| `customer` | Shopper app |
| `owner` | Dashboard (`/api/v1/admin/*`) — phone must match server `OWNER_PHONE_NUMBER` |

Confirm role via `GET /api/v1/auth/me` or `GET /api/v1/users/me`.

### Verify OTP success (example)

```json
{
  "success": true,
  "message": "Authentication successful",
  "data": {
    "user": {
      "id": "uuid",
      "phone_number": "+923001234567",
      "full_name": "Guest",
      "role": "customer",
      "is_verified": true,
      "is_active": true,
      "created_at": "2026-01-15T12:00:00Z"
    },
    "tokens": {
      "access_token": "<jwt>",
      "refresh_token": "<jwt>",
      "token_type": "bearer",
      "expires_in": 1800
    },
    "is_new_user": true
  }
}
```

---

## 5. Who can call what

| Area | Auth |
|------|------|
| Health, Catalog GET (categories/products/deals/search) | Public |
| Auth send-otp / verify-otp / refresh | Public |
| Auth logout / me | Bearer |
| Users, Cart, Wishlist, Checkout, Orders | Bearer + verified customer |
| All `/api/v1/admin/*` | Bearer + **owner** |

If a customer asks for someone else’s order/address → API returns **404** (not 403).

---

## 6. Customer journey (copy this order)

```text
GET  /api/v1/categories
GET  /api/v1/products
GET  /api/v1/products/{slug}
POST /api/v1/auth/send-otp → verify-otp
POST /api/v1/cart/items
POST /api/v1/users/addresses
POST /api/v1/cart/apply-coupon          (optional)
POST /api/v1/checkout/validate
POST /api/v1/orders                     (+ Idempotency-Key header or body)
GET  /api/v1/orders/{id}/tracking
```

---

## 7. Owner journey

```text
OTP login with owner phone
GET  /api/v1/admin/dashboard
GET  /api/v1/admin/orders
PATCH /api/v1/admin/orders/{id}/status
POST /api/v1/admin/products
POST /api/v1/admin/products/{id}/images   (multipart)
```

---

## 8. Money, IDs, dates

- IDs are UUIDs.
- Public catalog uses **slugs**; admin uses **UUIDs**.
- Money is decimal-safe JSON (string or number — treat as decimal).
- Timestamps are ISO-8601 UTC.

---

## 9. File uploads

| Endpoint | Form field | Limits |
|----------|------------|--------|
| `POST /api/v1/users/avatar` | `file` | ~5MB, jpeg/png/webp/gif |
| `POST /api/v1/admin/products/{id}/images` | `file`, optional `alt_text`, `is_primary` | same |

Do not set `Content-Type` manually when using `FormData`.

---

## 10. Pagination

`page` (default 1), `page_size` (default 20, max 100).

Product `sort`: `newest` | `oldest` | `price_asc` | `price_desc` | `popularity` | `name_asc` | `name_desc` | `preparation_time`

---

## 11. Enums (use exactly these strings)

**OrderStatus:** `pending`, `confirmed`, `preparing`, `ready`, `out_for_delivery`, `delivered`, `cancelled`, `refunded`

**PaymentMethod:** `cash_on_delivery`, `card`, `online`, `wallet`

**PaymentStatus:** `pending`, `paid`, `failed`, `refunded`, `partially_refunded`, `cancelled`

**StockStatus:** `in_stock`, `out_of_stock`, `limited`

**CouponType:** `percentage`, `fixed`

**UserRole:** `customer`, `owner`

---

## 12. Error codes

| HTTP | code | Frontend action |
|------|------|-----------------|
| 401 | `unauthorized` / `invalid_token` / `expired_token` | refresh or login |
| 403 | `forbidden` | hide feature |
| 404 | `not_found` | not found UI |
| 409 | `conflict` | show conflict |
| 413 | `payload_too_large` | smaller body/file |
| 422 | `validation_error` | map `details` to fields |
| 429 | `rate_limit_exceeded` | wait `Retry-After` |
| 503 | `maintenance_mode` | maintenance screen |

---

## 13. CORS

Origin must match server `FRONTEND_URL`. Auth via Bearer header (no cookies / CSRF).

---

## 14. TypeScript helper

```typescript
const BASE = import.meta.env.VITE_API_BASE; // e.g. http://127.0.0.1:8000

type Ok<T> = {
  success: true;
  message: string;
  data: T;
  meta?: Record<string, unknown> | null;
  request_id?: string | null;
};

type Err = {
  success: false;
  message: string;
  error: { code: string; details?: unknown };
  status_code?: number;
};

export async function api<T>(
  path: string,
  init: RequestInit & { token?: string } = {},
): Promise<Ok<T>> {
  const headers = new Headers(init.headers);
  if (init.token) headers.set("Authorization", `Bearer ${init.token}`);
  if (init.body && !(init.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const res = await fetch(`${BASE}${path}`, { ...init, headers });
  const json = (await res.json()) as Ok<T> | Err;
  if (!res.ok || json.success === false) throw json;
  return json as Ok<T>;
}
```

---

## 15. Endpoint index (quick reference)

Full details for each route: [`docs/api/`](docs/api/README.md)

'''


def _schema_name(schema: dict[str, Any] | None) -> str:
    if not schema:
        return ""
    ref = schema.get("$ref")
    if isinstance(ref, str) and "/schemas/" in ref:
        return ref.rsplit("/", 1)[-1]
    if schema.get("type") == "array":
        return f"array[{_schema_name(schema.get('items'))}]"
    return str(schema.get("type") or "object")


def _auth_label(path: str, method: str) -> str:
    lower = path.lower()
    if "/admin/" in lower:
        return "Bearer + owner"
    if any(
        x in lower
        for x in (
            "/users",
            "/cart",
            "/wishlist",
            "/checkout",
            "/orders",
            "/auth/me",
            "/auth/logout",
        )
    ):
        return "Bearer"
    if "/auth/send-otp" in lower or "/auth/verify-otp" in lower or "/auth/refresh" in lower:
        return "Public"
    if method == "GET" and any(
        lower.startswith(p)
        for p in ("/api/v1/categories", "/api/v1/products", "/api/v1/deals", "/health", "/")
    ):
        return "Public"
    if lower.startswith("/health") or lower in {"/", "/api/v1/", "/api/v1"}:
        return "Public"
    return "See docs"


def _slug(tag: str) -> str:
    return tag.lower().replace(" ", "-")


def generate() -> None:
    from app.main import create_app

    root = Path(__file__).resolve().parents[1]
    api_dir = root / "docs" / "api"
    api_dir.mkdir(parents=True, exist_ok=True)

    app = create_app()
    openapi = app.openapi()

    by_tag: dict[str, list[tuple[str, str, dict[str, Any]]]] = {}
    for path, methods in openapi.get("paths", {}).items():
        for method, operation in methods.items():
            if method.startswith("x-") or not isinstance(operation, dict):
                continue
            tag = (operation.get("tags") or ["Untagged"])[0]
            by_tag.setdefault(tag, []).append((method.upper(), path, operation))

    ordered = [t for t in TAG_ORDER if t in by_tag] + sorted(t for t in by_tag if t not in TAG_ORDER)

    # ---- Compact api.md ----
    guide_lines = [GUIDE]
    guide_lines.append("| Tag | Endpoints | Doc file |")
    guide_lines.append("|-----|-----------|----------|")
    for tag in ordered:
        guide_lines.append(
            f"| {tag} | {len(by_tag[tag])} | [`{_slug(tag)}.md`](docs/api/{_slug(tag)}.md) |"
        )
    guide_lines.append("")
    guide_lines.append("### All routes (one-liners)")
    guide_lines.append("")
    guide_lines.append("| Method | Path | Auth | Summary |")
    guide_lines.append("|--------|------|------|---------|")
    for tag in ordered:
        for method, path, op in by_tag[tag]:
            summary = (op.get("summary") or "").replace("|", "/")
            guide_lines.append(
                f"| `{method}` | `{path}` | {_auth_label(path, method)} | {summary} |"
            )
    guide_lines.append("")
    guide_lines.append("---")
    guide_lines.append("")
    guide_lines.append("Regenerate docs:")
    guide_lines.append("")
    guide_lines.append("```bash")
    guide_lines.append("python scripts/generate_api_md.py")
    guide_lines.append("```")
    guide_lines.append("")

    (root / "api.md").write_text("\n".join(guide_lines), encoding="utf-8")

    # ---- docs/api/README.md ----
    readme = [
        "# API endpoint details",
        "",
        "Split by module so files open quickly in the editor.",
        "",
        "Start with the lean guide: [`../../api.md`](../../api.md)",
        "",
    ]
    for tag in ordered:
        readme.append(f"- [{tag}]({_slug(tag)}.md) — {len(by_tag[tag])} endpoints")
    readme.append("")
    (api_dir / "README.md").write_text("\n".join(readme), encoding="utf-8")

    # ---- Per-tag files ----
    for tag in ordered:
        lines: list[str] = [
            f"# {tag}",
            "",
            f"Back to [`api.md`](../../api.md) · [`index`](README.md)",
            "",
        ]
        for method, path, op in by_tag[tag]:
            summary = op.get("summary") or ""
            lines.append(f"## `{method} {path}`")
            lines.append("")
            lines.append(f"**Summary:** {summary}")
            lines.append("")
            lines.append(f"**Auth:** {_auth_label(path, method)}")
            lines.append("")
            if op.get("description"):
                lines.append(str(op["description"]).strip())
                lines.append("")

            params = op.get("parameters") or []
            path_params = [p for p in params if p.get("in") == "path"]
            query_params = [p for p in params if p.get("in") == "query"]
            if path_params:
                lines.append("**Path params**")
                lines.append("")
                for p in path_params:
                    schema = p.get("schema") or {}
                    lines.append(
                        f"- `{p.get('name')}` ({schema.get('type', 'string')}"
                        f"{', required' if p.get('required') else ''})"
                    )
                lines.append("")
            if query_params:
                lines.append("**Query params**")
                lines.append("")
                for p in query_params:
                    schema = p.get("schema") or {}
                    default = schema.get("default", "")
                    lines.append(
                        f"- `{p.get('name')}` ({_schema_name(schema) or schema.get('type', 'string')}"
                        f", default=`{default}`)"
                    )
                lines.append("")

            body = (op.get("requestBody") or {}).get("content") or {}
            if body:
                lines.append("**Body**")
                lines.append("")
                for ctype, meta in body.items():
                    schema = meta.get("schema") or {}
                    lines.append(f"- Content-Type: `{ctype}`")
                    name = _schema_name(schema)
                    if name and name not in {"object", "array[object]"}:
                        lines.append(f"- Schema: `{name}`")
                    # Compact property list from $ref
                    ref = schema.get("$ref")
                    if ref:
                        sname = ref.rsplit("/", 1)[-1]
                        sdef = openapi.get("components", {}).get("schemas", {}).get(sname, {})
                        props = sdef.get("properties") or {}
                        required = set(sdef.get("required") or [])
                        if props:
                            lines.append("")
                            lines.append("| Field | Type | Required |")
                            lines.append("|-------|------|----------|")
                            for fname, fschema in props.items():
                                ftype = fschema.get("type") or _schema_name(fschema) or "object"
                                if "anyOf" in fschema:
                                    ftype = "nullable"
                                lines.append(
                                    f"| `{fname}` | `{ftype}` | "
                                    f"{'yes' if fname in required else 'no'} |"
                                )
                lines.append("")

            lines.append("**Success responses:** " + ", ".join(
                f"`{code}`" for code in sorted(op.get("responses", {}), key=str) if str(code).startswith("2")
            ))
            lines.append("")
            lines.append("---")
            lines.append("")

        (api_dir / f"{_slug(tag)}.md").write_text("\n".join(lines), encoding="utf-8")

    main = root / "api.md"
    print(f"Wrote {main} ({main.stat().st_size} bytes)")
    print(f"Wrote {len(ordered)} module files under {api_dir}")


if __name__ == "__main__":
    generate()
