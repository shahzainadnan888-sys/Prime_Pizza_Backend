#!/usr/bin/env python3
"""
Generate production-ready api.md from the LIVE FastAPI OpenAPI schema.

Only documents endpoints that exist in the running app. Kitchen URL aliases are
documented once. Hidden routes (trailing-slash contact, etc.) are noted under
the canonical endpoint.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
API_MD = ROOT / "api.md"
DOCS_API = ROOT / "docs" / "api"

# Duplicate kitchen mounts — same handlers as /api/v1/kitchen/*
_KITCHEN_ALIAS_PREFIXES = (
    "/api/v1/chef/",
    "/api/v1/orders/kitchen/",
    "/api/v1/dashboard/chef/",
)

TAG_ORDER = [
    "Health",
    "Authentication",
    "Account",
    "Users",
    "Catalog",
    "Cart",
    "Wishlist",
    "Checkout",
    "Orders",
    "Contact",
    "Kitchen Dashboard",
    "Admin Email",
    "Admin Dashboard",
    "Admin Orders",
    "Admin Customers",
    "Admin Catalog",
    "Admin Coupons",
    "Admin Notifications",
    "Admin Settings",
    "Admin Audit",
    "Admin Search",
]


def _load_openapi() -> dict[str, Any]:
    from fastapi.testclient import TestClient

    from app.main import create_app

    app = create_app()
    with TestClient(app) as client:
        return client.get("/openapi.json").json()


def _resolve_ref(spec: dict[str, Any], ref: str) -> dict[str, Any]:
    # "#/components/schemas/Foo" -> components.schemas.Foo
    parts = ref.lstrip("#/").split("/")
    node: Any = spec
    for part in parts:
        node = node[part]
    return node


def _deref(spec: dict[str, Any], schema: dict[str, Any] | None) -> dict[str, Any]:
    if not schema:
        return {}
    if "$ref" in schema:
        return _deref(spec, _resolve_ref(spec, schema["$ref"]))
    if "allOf" in schema:
        merged: dict[str, Any] = {"properties": {}, "required": []}
        for part in schema["allOf"]:
            resolved = _deref(spec, part)
            merged["properties"].update(resolved.get("properties") or {})
            merged["required"] = list(
                dict.fromkeys([*(merged.get("required") or []), *(resolved.get("required") or [])])
            )
            for key in ("title", "type", "description"):
                if key in resolved and key not in merged:
                    merged[key] = resolved[key]
        return merged
    return schema


def _type_label(spec: dict[str, Any], schema: dict[str, Any] | None) -> str:
    if not schema:
        return "any"
    schema = _deref(spec, schema)
    if "anyOf" in schema or "oneOf" in schema:
        variants = schema.get("anyOf") or schema.get("oneOf") or []
        labels = []
        for v in variants:
            if v.get("type") == "null":
                labels.append("null")
            else:
                labels.append(_type_label(spec, v))
        return " | ".join(labels)
    if schema.get("enum"):
        return "enum: " + " | ".join(f"`{x}`" for x in schema["enum"])
    t = schema.get("type")
    if t == "array":
        return f"array<{_type_label(spec, schema.get('items'))}>"
    if t == "object" or schema.get("properties"):
        title = schema.get("title") or "object"
        return title
    fmt = schema.get("format")
    if fmt:
        return f"{t} ({fmt})" if t else fmt
    return str(t or "any")


def _auth_for_path(path: str, method: str, operation: dict[str, Any]) -> tuple[str, str]:
    """Return (auth_required_label, role_label)."""
    lower = path.lower()
    security = operation.get("security")
    # Explicit empty security = public
    if security == []:
        return "No", "—"

    if any(lower.startswith(p) for p in ("/api/v1/kitchen/", "/api/v1/chef/", "/api/v1/orders/kitchen/", "/api/v1/dashboard/chef/")):
        return "Yes — Bearer access token", "`chef` (verified)"
    if "/admin/" in lower:
        return "Yes — Bearer access token", "`chef` (permission-gated; no separate admin role)"
    if lower.startswith("/api/v1/auth/register") or lower.startswith("/api/v1/auth/login") or lower.startswith("/api/v1/auth/refresh"):
        return "No", "—"
    if "/contact" in lower:
        return "No", "—"
    if lower.startswith("/health") or lower in {"/", "/api/v1", "/api/v1/"} or lower.startswith("/api/v1/health"):
        return "No", "—"
    if method == "GET" and any(
        lower.startswith(p)
        for p in ("/api/v1/categories", "/api/v1/products", "/api/v1/deals")
    ):
        return "No", "—"
    if lower.startswith("/api/v1/auth/logout") or lower.startswith("/api/v1/auth/me"):
        return "Yes — Bearer access token", "`customer` | `chef`"
    if any(
        x in lower
        for x in (
            "/users",
            "/account",
            "/addresses",
            "/cart",
            "/wishlist",
            "/checkout",
            "/orders",
        )
    ):
        # customer-owned paths; chef also has these permissions typically for own cart
        if "/admin/" in lower:
            return "Yes — Bearer access token", "`chef`"
        return "Yes — Bearer access token (verified account)", "`customer` (primary) | `chef`"
    # Fallback: if HTTPBearer is declared, require auth
    if security:
        return "Yes — Bearer access token", "See permissions"
    return "See endpoint", "—"


def _is_kitchen_alias(path: str) -> bool:
    return any(path.startswith(prefix) for prefix in _KITCHEN_ALIAS_PREFIXES)


def _schema_fields_table(spec: dict[str, Any], schema: dict[str, Any] | None) -> str:
    schema = _deref(spec, schema)
    props = schema.get("properties") or {}
    if not props:
        return "_No fields (or opaque object)._"
    required = set(schema.get("required") or [])
    lines = ["| Field | Type | Required | Notes |", "|-------|------|----------|-------|"]
    for name, prop in props.items():
        prop = _deref(spec, prop)
        req = "yes" if name in required else "no"
        notes = []
        if prop.get("description"):
            notes.append(str(prop["description"]))
        if prop.get("minLength") is not None:
            notes.append(f"minLength={prop['minLength']}")
        if prop.get("maxLength") is not None:
            notes.append(f"maxLength={prop['maxLength']}")
        if prop.get("minimum") is not None:
            notes.append(f"min={prop['minimum']}")
        if prop.get("maximum") is not None:
            notes.append(f"max={prop['maximum']}")
        if prop.get("default") is not None:
            notes.append(f"default=`{json.dumps(prop['default'])}`")
        if prop.get("enum"):
            notes.append("values: " + ", ".join(f"`{e}`" for e in prop["enum"]))
        lines.append(
            f"| `{name}` | {_type_label(spec, prop)} | {req} | {'; '.join(notes) or '—'} |"
        )
    return "\n".join(lines)


def _example_from_schema(spec: dict[str, Any], schema: dict[str, Any] | None) -> Any:
    schema = _deref(spec, schema)
    if not schema:
        return None
    if "example" in schema:
        return schema["example"]
    if "examples" in schema and isinstance(schema["examples"], list) and schema["examples"]:
        return schema["examples"][0]
    if schema.get("enum"):
        return schema["enum"][0]
    t = schema.get("type")
    props = schema.get("properties") or {}
    if props or t == "object":
        required = set(schema.get("required") or [])
        # Prefer required fields first so examples are valid.
        ordered = list(required) + [k for k in props if k not in required]
        out: dict[str, Any] = {}
        for key in ordered[:24]:
            out[key] = _example_from_schema(spec, props[key])
        return out
    if t == "array":
        item = _example_from_schema(spec, schema.get("items"))
        return [item] if item is not None else []
    if t == "integer":
        return schema.get("default", 1)
    if t == "number":
        return schema.get("default", 0)
    if t == "boolean":
        return schema.get("default", True)
    if schema.get("format") == "email":
        return "user@example.com"
    if schema.get("format") == "uuid":
        return "00000000-0000-4000-8000-000000000001"
    if schema.get("format") == "date-time":
        return "2026-07-15T12:00:00Z"
    if t == "string":
        return schema.get("default") or "string"
    return None


def _request_body_schema(spec: dict[str, Any], operation: dict[str, Any]) -> dict[str, Any] | None:
    body = operation.get("requestBody") or {}
    content = body.get("content") or {}
    for ct in ("application/json", "multipart/form-data", "application/x-www-form-urlencoded"):
        if ct in content:
            return _deref(spec, content[ct].get("schema"))
    if content:
        first = next(iter(content.values()))
        return _deref(spec, first.get("schema"))
    return None


def _success_response_schema(spec: dict[str, Any], operation: dict[str, Any]) -> tuple[str, dict[str, Any] | None]:
    responses = operation.get("responses") or {}
    for code in ("200", "201", "202", "204"):
        if code not in responses:
            continue
        content = (responses[code].get("content") or {})
        if "application/json" in content:
            return code, _deref(spec, content["application/json"].get("schema"))
        return code, None
    return "200", None


def _parameters(operation: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    path_params: list[dict[str, Any]] = []
    query_params: list[dict[str, Any]] = []
    for p in operation.get("parameters") or []:
        if p.get("in") == "path":
            path_params.append(p)
        elif p.get("in") == "query":
            query_params.append(p)
    return path_params, query_params


def _params_table(params: list[dict[str, Any]], spec: dict[str, Any]) -> str:
    if not params:
        return "_None._"
    lines = ["| Name | Required | Type | Description |", "|------|----------|------|-------------|"]
    for p in params:
        sch = p.get("schema") or {}
        lines.append(
            f"| `{p.get('name')}` | {'yes' if p.get('required') else 'no'} | "
            f"{_type_label(spec, sch)} | {p.get('description') or '—'} |"
        )
    return "\n".join(lines)


def _status_codes(operation: dict[str, Any]) -> str:
    responses = operation.get("responses") or {}
    if not responses:
        return "_See global error table._"
    lines = ["| Code | Description |", "|------|-------------|"]
    for code in sorted(responses.keys(), key=lambda c: (len(c), c)):
        desc = responses[code].get("description") or "—"
        lines.append(f"| `{code}` | {desc} |")
    return "\n".join(lines)


def _render_endpoint(
    *,
    spec: dict[str, Any],
    path: str,
    method: str,
    operation: dict[str, Any],
) -> str:
    summary = operation.get("summary") or f"{method.upper()} {path}"
    description = (operation.get("description") or "").strip() or summary
    auth, role = _auth_for_path(path, method.upper(), operation)
    path_params, query_params = _parameters(operation)
    req_schema = _request_body_schema(spec, operation)
    ok_code, res_schema = _success_response_schema(spec, operation)

    headers = ["| Header | Required |", "|--------|----------|"]
    if auth.startswith("Yes"):
        headers.append("| `Authorization: Bearer <access_token>` | yes |")
    body_meta = operation.get("requestBody") or {}
    content_types = list((body_meta.get("content") or {}).keys())
    if "multipart/form-data" in content_types:
        headers.append("| `Content-Type: multipart/form-data` | yes |")
    elif req_schema is not None:
        headers.append("| `Content-Type: application/json` | yes (JSON bodies) |")
    if "idempotency" in path.lower() or (
        path.rstrip("/").endswith("/orders") and method.lower() == "post"
    ):
        headers.append("| `Idempotency-Key` | recommended for `POST /orders` |")
    if len(headers) == 2:
        headers.append("| — | — |")

    # Validation rules from schema constraints
    validation_notes: list[str] = []
    if req_schema:
        props = (_deref(spec, req_schema).get("properties") or {})
        required = set((_deref(spec, req_schema).get("required") or []))
        if required:
            validation_notes.append(
                "Required body fields: " + ", ".join(f"`{r}`" for r in sorted(required))
            )
        for name, prop in props.items():
            prop = _deref(spec, prop)
            bits = []
            if prop.get("minLength") is not None:
                bits.append(f"minLength={prop['minLength']}")
            if prop.get("maxLength") is not None:
                bits.append(f"maxLength={prop['maxLength']}")
            if prop.get("minimum") is not None:
                bits.append(f"min={prop['minimum']}")
            if prop.get("maximum") is not None:
                bits.append(f"max={prop['maximum']}")
            if prop.get("pattern"):
                bits.append(f"pattern=`{prop['pattern']}`")
            if prop.get("enum"):
                bits.append("enum=" + "|".join(str(e) for e in prop["enum"]))
            if bits:
                validation_notes.append(f"`{name}`: " + ", ".join(bits))
    for p in (*path_params, *query_params):
        sch = p.get("schema") or {}
        bits = []
        if sch.get("minimum") is not None:
            bits.append(f"min={sch['minimum']}")
        if sch.get("maximum") is not None:
            bits.append(f"max={sch['maximum']}")
        if bits:
            validation_notes.append(f"`{p.get('name')}`: " + ", ".join(bits))

    parts: list[str] = [
        f"## {summary}",
        "",
        "### Endpoint",
        "",
        f"`{method.upper()} {path}`",
        "",
        "### Description",
        "",
        description,
        "",
        "### Authentication Required",
        "",
        auth,
        "",
        "### Required Role",
        "",
        role,
        "",
        "### Headers",
        "",
        "\n".join(headers),
        "",
        "### Path Parameters",
        "",
        _params_table(path_params, spec),
        "",
        "### Query Parameters",
        "",
        _params_table(query_params, spec),
        "",
        "### Request Body Schema",
        "",
    ]

    if req_schema is None:
        parts.append("_No request body._")
    else:
        parts.append(_schema_fields_table(spec, req_schema))
        example = _example_from_schema(spec, req_schema)
        if example is not None:
            ct = (
                "multipart/form-data"
                if "multipart/form-data" in content_types
                else "application/json"
            )
            parts.extend(
                [
                    "",
                    "### Example Request",
                    "",
                    "```http",
                    f"{method.upper()} {path} HTTP/1.1",
                    "Host: {BASE_URL}",
                ]
            )
            if auth.startswith("Yes"):
                parts.append("Authorization: Bearer <access_token>")
            parts.append(f"Content-Type: {ct}")
            if ct == "application/json":
                parts.extend(
                    [
                        "",
                        json.dumps(example, indent=2, default=str),
                        "```",
                    ]
                )
            else:
                parts.extend(
                    [
                        "",
                        "(multipart form fields — see Request Body Schema)",
                        "```",
                    ]
                )

    parts.extend(
        [
            "",
            "### Validation Rules",
            "",
            (
                "\n".join(f"- {n}" for n in validation_notes)
                if validation_notes
                else "_See field constraints in the request schema table (and query/path params)._"
            ),
            "",
            "### Response Schema",
            "",
            f"Success status: **{ok_code}**",
            "",
        ]
    )
    if res_schema is None:
        parts.append("_See response envelope._")
    else:
        # Prefer documenting `data` property if SuccessResponse wrapper
        props = res_schema.get("properties") or {}
        if "data" in props:
            parts.append("Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).")
            parts.append("")
            parts.append("**`data` schema**")
            parts.append("")
            data_schema = _deref(spec, props["data"])
            parts.append(_schema_fields_table(spec, data_schema))
            data_example = _example_from_schema(spec, data_schema)
            if data_example is not None:
                envelope = {
                    "success": True,
                    "message": "Success",
                    "data": data_example,
                    "request_id": "00000000-0000-4000-8000-000000000099",
                }
                if "meta" in props:
                    envelope["meta"] = {
                        "page": 1,
                        "page_size": 20,
                        "total_items": 1,
                        "total_pages": 1,
                        "has_next": False,
                        "has_previous": False,
                    }
                parts.extend(
                    [
                        "",
                        "### Example Response",
                        "",
                        "```json",
                        json.dumps(envelope, indent=2, default=str),
                        "```",
                    ]
                )
        else:
            parts.append(_schema_fields_table(spec, res_schema))

    parts.extend(
        [
            "",
            "### Success Responses",
            "",
            f"- `{ok_code}` — success (see Example Response / Response Schema)",
            "",
            "### Error Responses",
            "",
            _status_codes(operation),
            "",
            "Also see [Global error responses](#global-error-responses). Common for this route:",
            "",
            "- `401` — missing/invalid Bearer token (protected routes)",
            "- `403` — authenticated but wrong role/permission",
            "- `422` — validation failure (body/query/path)",
            "- `429` — rate limited",
            "",
            "---",
            "",
        ]
    )
    return "\n".join(parts)


FRONT_MATTER = r'''# Prime Pizza API — Frontend Source of Truth

> Generated from the **live** FastAPI OpenAPI schema for the current backend.
> Interactive docs: `{{BASE_URL}}/docs` · OpenAPI JSON: `{{BASE_URL}}/openapi.json`
>
> Do **not** invent endpoints. If it is not listed here, it is not part of this API.

**Generated operations in this file:** {OP_COUNT} canonical endpoints  
**Roles:** `customer` | `chef` only (there is **no** separate `admin` role; chef uses `/admin/*` with permissions)  
**Auth:** email + password → JWT Bearer (**no OTP / Twilio / Resend**)  
**Email provider:** Brevo (server-side only — API keys never leave the backend)

---

## Table of contents

1. [Base URL](#base-url)
2. [Response envelope](#response-envelope)
3. [Authentication & JWT](#authentication--jwt)
4. [Roles & permissions](#roles--permissions)
5. [Brevo emails](#brevo-emails)
6. [File uploads](#file-uploads)
7. [Order status values](#order-status-values)
8. [Pagination, filtering & sorting](#pagination-filtering--sorting)
9. [Environment & infrastructure](#environment--infrastructure)
10. [Global error responses](#global-error-responses)
11. [Frontend integration notes](#frontend-integration-notes)
12. [Endpoint catalog](#endpoint-catalog)
13. [Detailed endpoints](#detailed-endpoints)
14. [Integration summary](#integration-summary)

---

## Base URL

| Environment | Example |
|-------------|---------|
| Local | `http://127.0.0.1:8000` |
| Production | set by deployment |

All business routes: `{{BASE_URL}}/api/v1/...`

Health probes also exist without the `/api/v1` prefix (`/health`, `/health/database`, …).

---

## Response envelope

### Success

```json
{{
  "success": true,
  "message": "Success",
  "data": {{}},
  "meta": null,
  "request_id": "uuid"
}}
```

### Paginated success

`data` is an array. Paging metadata is in `meta`:

```json
{{
  "success": true,
  "message": "Success",
  "data": [],
  "meta": {{
    "page": 1,
    "page_size": 20,
    "total_items": 100,
    "total_pages": 5,
    "has_next": true,
    "has_previous": false
  }},
  "request_id": "uuid"
}}
```

### Error

```json
{{
  "success": false,
  "message": "Human-readable message",
  "error": {{
    "code": "validation_error",
    "details": []
  }},
  "status_code": 422,
  "request_id": "uuid"
}}
```

---

## Authentication & JWT

### Flows

| Action | Method & path | Auth | Notes |
|--------|---------------|------|-------|
| Register | `POST /api/v1/auth/register` | Public | Saves user to Neon + `data/user.json`; schedules Welcome email |
| Login | `POST /api/v1/auth/login` | Public | Returns JWT pair + `role` |
| Refresh | `POST /api/v1/auth/refresh` | Public (body has refresh token) | Rotates tokens |
| Logout | `POST /api/v1/auth/logout` | Bearer access token | Blacklists access token |
| Current user (auth) | `GET /api/v1/auth/me` | Bearer | Auth-centric me payload |
| Current profile | `GET /api/v1/users/me` | Bearer | Full profile |
| Profile alias | `GET /api/v1/account` | Bearer | Alias of `GET /users/me` |
| Profile update | `PATCH /api/v1/users/me` | Bearer | Partial profile update |
| Avatar upload | `POST /api/v1/users/avatar` | Bearer | `multipart/form-data` |
| Avatar delete | `DELETE /api/v1/users/avatar` | Bearer | |
| Password change | — | — | **Not implemented** in this backend |

### Register body (required)

| Field | Rules |
|-------|-------|
| `first_name`, `last_name` | 1–80 chars, non-empty after trim |
| `email` | valid email, stored lowercase |
| `password` | 8–128 chars; must include upper, lower, and digit |
| `confirm_password` | must match `password` |
| `phone_number` | optional; if set, E.164 (e.g. `+923001234567`) |

### Login body

| Field | Rules |
|-------|-------|
| `email` | required |
| `password` | required |

### Auth success `data` (register / login / refresh)

Flattened fields are included for frontend convenience:

- `access_token`, `refresh_token`, `token_type` (`bearer`), `expires_in` (seconds)
- `role` (`customer` | `chef`)
- `user` object (`id`, `first_name`, `last_name`, `email`, `phone_number`, `full_name`, `name`, `role`, `is_verified`, `is_active`, `created_at`)
- `tokens` nested pair (same tokens)
- `is_new_user` (register = true)

### Authorization header (all protected routes)

```http
Authorization: Bearer <access_token>
```

### JWT claims (access + refresh)

Issued claims include: `sub` / `user_id`, `email`, `phone_number`, `role`, `token_type` (`access`|`refresh`), `iat`, `exp`, `jti`.

**Authorization decisions use the database role**, not a forged JWT `role` claim.

### Protected routes

Any route marked “Bearer” below requires a valid, non-blacklisted access token. Unverified accounts may be rejected on verified-only routes.

---

## Roles & permissions

| Role | Purpose |
|------|---------|
| `customer` | Storefront: profile, cart, wishlist, checkout, own orders |
| `chef` | Kitchen dashboard + `/api/v1/admin/*` (chef permissions) |

There is **no** `admin` role string. Chef account is bootstrapped from env:

- Email: `CHEF_EMAIL`
- Password: `CHEF_PASSWORD`

Customers calling kitchen or `/admin/*` routes receive **403**.

### Public (no auth)

Health probes, register/login/refresh, public catalog (categories/products/deals GET), contact form.

### Customer endpoints (primary)

`/users/*`, `/account`, `/addresses`, `/cart/*`, `/wishlist/*`, `/checkout/*`, `/orders/*` (own orders).

### Chef endpoints

- Kitchen: `/api/v1/kitchen/*` (aliases: `/chef/*`, `/orders/kitchen/*`, `/dashboard/chef/*`)
- Owner console: `/api/v1/admin/*` (catalog, orders, customers, coupons, settings, notifications, audit, search, test-email)

---

## Brevo emails

Frontend **never** calls Brevo. The frontend only hits backend APIs; the backend `EmailService` sends via Brevo using server env vars. **Never put `BREVO_API_KEY` in frontend code or public env.**

| Trigger API | Email(s) | Delivery behavior |
|-------------|----------|-------------------|
| `POST /api/v1/auth/register` | **Welcome** → customer email | Best-effort after Neon + `user.json` save; registration **never fails** if email fails (logged) |
| `POST /api/v1/contact` | **Contact notification** → `CONTACT_RECEIVER_EMAIL` (+ admin inbox); optional customer confirmation | Admin inbox is **awaited**; Brevo failure → **HTTP 502** `brevo_service_error` |
| `POST /api/v1/orders` | **Order confirmation** → customer; **Chef notification** → `CHEF_EMAIL` | Scheduled after Neon + `order.json` save; place-order **HTTP success is not blocked** on Brevo |
| `POST /api/v1/admin/test-email` | Explicit connectivity test | Awaited; chef only; 502 on failure |

### Order confirmation content (customer)

Order number, customer name, line items (qty + prices), delivery address, payment method, order total, estimated delivery / prep time.

### Chef notification content

Customer name, phone, address, items, total, order ID / order number → inbox from `CHEF_EMAIL`.

### Related env names only (no values)

`BREVO_API_KEY`, `BREVO_SENDER_EMAIL`, `BREVO_SENDER_NAME`, `EMAIL_ENABLED`, `EMAIL_BRAND_NAME`, `EMAIL_LOGO_URL`, `ADMIN_EMAIL`, `CONTACT_RECEIVER_EMAIL`, `CHEF_EMAIL`, `OWNER_NOTIFICATION_EMAILS`

Startup **fails fast** when `EMAIL_ENABLED=true` and required Brevo vars are missing (skipped when `APP_ENV=test`).

---

## File uploads

| Endpoint | Auth | Multipart field | Max size (env) | Accepted types (env) |
|----------|------|-----------------|----------------|----------------------|
| `POST /api/v1/users/avatar` | Bearer | `file` | `AVATAR_MAX_BYTES` (default 5 MiB) | `AVATAR_ALLOWED_CONTENT_TYPES` — jpeg, png, webp, gif |
| `POST /api/v1/admin/products/{{product_id}}/images` | Bearer + chef | `file` (+ optional `alt_text`, `is_primary`) | `PRODUCT_IMAGE_MAX_BYTES` (default 5 MiB) | Image types validated server-side; max `MAX_PRODUCT_IMAGES` per product |

Uploaded assets are stored via **Cloudinary** (credentials server-side only).

---

## Order status values

Canonical enum:

`pending` | `confirmed` | `preparing` | `ready` | `out_for_delivery` | `delivered` | `cancelled` | `refunded`

### Kitchen vocabulary (boards / PATCH status)

| Kitchen term | Maps to |
|--------------|---------|
| `pending` / `incoming` | pending + confirmed board |
| `preparing` | preparing |
| `ready` | ready (+ out_for_delivery on board) |
| `completed` | delivered |
| `cancelled` | cancelled (+ refunded on board) |

Kitchen `PATCH .../status` accepts: `pending`, `preparing`, `ready`, `completed`, `cancelled` (aliases like `incoming` → pending).

---

## Pagination, filtering & sorting

### Pagination (when present)

| Param | Default | Constraints |
|-------|---------|-------------|
| `page` | `1` | ≥ 1 |
| `page_size` | `20` | 1–100 |

Used on: product lists/search, customer orders, admin orders/customers/coupons/audit, etc.

### Catalog filtering / search (examples)

`GET /api/v1/products` and `GET /api/v1/products/search` accept query params documented per endpoint (category, featured, search `q`, sort, etc.). See each endpoint’s **Query Parameters** table below.

### Cart quantity validation

Env-driven: `CART_MIN_ITEM_QUANTITY`, `CART_MAX_ITEM_QUANTITY`, `CART_MAX_ITEMS`.

---

## Environment & infrastructure

### Environment variables (names only — never commit values)

| Group | Variable names |
|-------|----------------|
| App | `APP_NAME`, `APP_ENV`, `DEBUG`, `API_V1_PREFIX`, `HOST`, `PORT`, `ALLOWED_HOSTS`, `FRONTEND_URL`, `ENABLE_DOCS`, `LOG_LEVEL` |
| Security | `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS`, `TRUST_X_FORWARDED_FOR`, `TRUSTED_PROXY_IPS`, `ENABLE_HSTS`, `HSTS_MAX_AGE_SECONDS`, `ENABLE_CSP`, `CONTENT_SECURITY_POLICY`, `MAX_REQUEST_BODY_BYTES` |
| Neon / DB | `DATABASE_URL`, `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, `DB_POOL_RECYCLE_SECONDS`, `DB_POOL_TIMEOUT_SECONDS` |
| Redis | `REDIS_URL`, `REDIS_MAX_CONNECTIONS` |
| Cloudinary | `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET` |
| Brevo | `BREVO_API_KEY`, `BREVO_SENDER_NAME`, `BREVO_SENDER_EMAIL`, `EMAIL_ENABLED`, `EMAIL_MAX_RETRIES`, `EMAIL_RETRY_BACKOFF_SECONDS`, `EMAIL_BRAND_NAME`, `EMAIL_LOGO_URL` |
| Inboxes | `ADMIN_EMAIL`, `CONTACT_RECEIVER_EMAIL`, `OWNER_EMAIL`, `OWNER_NOTIFICATION_EMAILS`, `CHEF_EMAIL`, `CHEF_PASSWORD`, `OWNER_PHONE_NUMBER` |
| Rate limits | `RATE_LIMIT_*`, `AUTH_*_LIMIT`, `AUTH_*_WINDOW_SECONDS` |
| Catalog / uploads | `AVATAR_MAX_BYTES`, `AVATAR_ALLOWED_CONTENT_TYPES`, `MAX_PRODUCT_IMAGES`, `PRODUCT_IMAGE_MAX_BYTES`, `CATALOG_CACHE_TTL_SECONDS` |
| Cart / orders | `CART_*`, `DELIVERY_FEE_FLAT`, `FREE_DELIVERY_THRESHOLD`, `TAX_RATE_PERCENT`, `ORDER_*`, `CHECKOUT_LOCK_TTL_SECONDS`, `ESTIMATED_*` |

### Required services

| Service | Purpose |
|---------|---------|
| **Neon PostgreSQL** | Primary system of record (users, orders, catalog, contact messages, email logs, …) |
| **Redis** (e.g. Upstash `rediss://`) | Auth rate limits, token blacklist, HTTP rate limiting, caches |
| **Brevo** | Transactional email (welcome, contact, order confirmation, chef notification) |
| **Cloudinary** | Avatar + product image storage |

### Local JSON mirrors (dual-write)

| File | Written when |
|------|----------------|
| `data/user.json` | After successful registration / user sync |
| `data/order.json` | After successful order placement / order sync |

These complement Neon; the API does **not** expose raw file contents as HTTP endpoints.

### CORS

Driven by `FRONTEND_URL`. In `APP_ENV=development`, local Vite/Next origins (`localhost:3000`, `5173`, `4173`, etc.) are also allowed. Production should set HTTPS `FRONTEND_URL` and proper `ALLOWED_HOSTS`.

---

## Global error responses

| HTTP | Typical `error.code` | When |
|------|----------------------|------|
| 400 | `app_error` / domain codes | Bad request |
| 401 | `unauthorized` / `invalid_token` / `expired_token` | Missing/invalid/expired/revoked token |
| 403 | `forbidden` | Authenticated but not allowed (e.g. customer → kitchen) |
| 404 | `not_found` | Missing resource |
| 409 | `conflict` | Duplicate email/phone, checkout lock, etc. |
| 422 | `validation_error` | Pydantic / business validation |
| 429 | `rate_limit` | Too many requests (`Retry-After` header) |
| 500 | `internal_error` | Unhandled server error |
| 502 | `brevo_service_error` | Contact admin email / admin test-email Brevo failure |
| 503 | `database_error` / `redis_error` / `rate_limit_unavailable` | Infrastructure |

### Example 401

```json
{{
  "success": false,
  "message": "Authentication required",
  "error": {{ "code": "unauthorized", "details": null }},
  "status_code": 401,
  "request_id": "..."
}}
```

### Example 403

```json
{{
  "success": false,
  "message": "Chef role required",
  "error": {{ "code": "forbidden", "details": null }},
  "status_code": 403,
  "request_id": "..."
}}
```

### Example 422

```json
{{
  "success": false,
  "message": "Validation error",
  "error": {{
    "code": "validation_error",
    "details": [
      {{
        "type": "missing",
        "loc": ["body", "confirm_password"],
        "msg": "Field required"
      }}
    ]
  }},
  "status_code": 422,
  "request_id": "..."
}}
```

### Example 502 (contact form Brevo failure)

```json
{{
  "success": false,
  "message": "Failed to send email via Brevo: …",
  "error": {{ "code": "brevo_service_error", "details": {{}} }},
  "status_code": 502,
  "request_id": "..."
}}
```

---

## Frontend integration notes

### Account aliases

| Frontend-friendly | Canonical |
|-------------------|-----------|
| `GET /api/v1/account` | `GET /api/v1/users/me` |
| `GET /api/v1/addresses` | `GET /api/v1/users/addresses` |
| `GET /api/v1/cart` | Active cart (stored totals; mutations recalculate) |

Always use the `/api/v1` prefix.

### Contact (frontend call)

```http
POST /api/v1/contact HTTP/1.1
Host: {{BASE_URL}}
Content-Type: application/json

{{
  "name": "Sara Ahmed",
  "email": "sara@example.com",
  "phone": "+923001112233",
  "subject": "Catering",
  "message": "Do you cater for 50 guests?"
}}
```

Aliases (same handler): `POST /api/v1/contact/`, `POST /api/v1/contacts`.

Success **201** — message saved and contact inbox email accepted by Brevo. On Brevo admin-send failure → **502**.

### Kitchen aliases (same handlers)

Prefer: `/api/v1/kitchen/*`

Also identical:

- `/api/v1/chef/*`
- `/api/v1/orders/kitchen/*`
- `/api/v1/dashboard/chef/*`

### Role routing after login

```ts
// data.role === "chef" → kitchen / admin UI
// data.role === "customer" → storefront
const token = data.access_token;
localStorage.setItem("access_token", token);
```

### Bearer example (profile)

```http
GET /api/v1/users/me HTTP/1.1
Host: {{BASE_URL}}
Authorization: Bearer <access_token>
```

### Create order

`POST /api/v1/orders` with Bearer token. Default payment method: `cash_on_delivery`. Optional `Idempotency-Key` header / `idempotency_key` body field.

After success the backend dual-writes `data/order.json` and schedules customer confirmation + chef notification emails.

### Order GPS (checkout)

Optional live device coordinates on `POST /api/v1/orders`:

| Field | Required | Rules |
|-------|----------|-------|
| `latitude` | no | -90..90; must be sent with `longitude` |
| `longitude` | no | -180..180; must be sent with `latitude` |
| `gps_accuracy` | no | meters, >= 0; requires lat/lng |

Stored on the order row, echoed on `OrderDetailResponse` (`GET/POST /orders…`), kitchen cards, and mirrored into `data/order.json`. When omitted, lat/lng may fall back to the saved address coordinates; `gps_accuracy` stays null unless provided.

Example:

```json
{{
  "address_id": "00000000-0000-4000-8000-000000000001",
  "payment_method": "cash_on_delivery",
  "latitude": 24.8607,
  "longitude": 67.0011,
  "gps_accuracy": 12.5
}}
```

Response `data` includes the same three fields.

---

## Endpoint catalog

{CATALOG}

### Kitchen URL aliases (not repeated below)

Same operations as `/api/v1/kitchen/*` are also mounted at:

`/api/v1/chef/*`, `/api/v1/orders/kitchen/*`, `/api/v1/dashboard/chef/*`

---

## Detailed endpoints

'''


def _catalog_lines(grouped: dict[str, list[tuple[str, str, str, str]]]) -> str:
    lines: list[str] = []
    for tag in TAG_ORDER:
        rows = grouped.get(tag) or []
        if not rows:
            continue
        lines.append(f"### {tag}")
        lines.append("")
        lines.append("| Method | Path | Auth | Summary |")
        lines.append("|--------|------|------|---------|")
        for method, path, auth, summary in rows:
            if auth.startswith("No"):
                auth_short = "Public"
            elif "chef` (verified)" in auth or "permission-gated" in auth:
                auth_short = "Bearer + chef"
            else:
                auth_short = "Bearer"
            lines.append(f"| `{method}` | `{path}` | {auth_short} | {summary} |")
        lines.append("")
    # leftover tags
    for tag, rows in grouped.items():
        if tag in TAG_ORDER or not rows:
            continue
        lines.append(f"### {tag}")
        lines.append("")
        lines.append("| Method | Path | Auth | Summary |")
        lines.append("|--------|------|------|---------|")
        for method, path, auth, summary in rows:
            auth_short = "Public" if auth.startswith("No") else "Bearer"
            if "chef" in auth.lower():
                auth_short = "Bearer + chef"
            lines.append(f"| `{method}` | `{path}` | {auth_short} | {summary} |")
        lines.append("")
    return "\n".join(lines)


def _write_module_docs(
    *,
    spec: dict[str, Any],
    grouped_ops: dict[str, list[tuple[str, str, dict[str, Any]]]],
) -> None:
    DOCS_API.mkdir(parents=True, exist_ok=True)
    index: list[str] = [
        "# API modules",
        "",
        "Per-tag endpoint dumps generated with `api.md`.",
        "",
    ]
    for tag in list(TAG_ORDER) + [t for t in grouped_ops if t not in TAG_ORDER]:
        ops = grouped_ops.get(tag) or []
        if not ops:
            continue
        slug = re.sub(r"[^a-z0-9]+", "-", tag.lower()).strip("-")
        path = DOCS_API / f"{slug}.md"
        chunks = [f"# {tag}", ""]
        for method, route, operation in ops:
            chunks.append(
                _render_endpoint(spec=spec, path=route, method=method, operation=operation)
            )
        path.write_text("\n".join(chunks), encoding="utf-8")
        index.append(f"- [{tag}]({slug}.md) ({len(ops)})")
    (DOCS_API / "README.md").write_text("\n".join(index) + "\n", encoding="utf-8")


def _classify_access(path: str, method: str, operation: dict[str, Any]) -> str:
    """Return public | customer | chef for integration summary."""
    auth, _role = _auth_for_path(path, method, operation)
    if auth.startswith("No"):
        return "public"
    lower = path.lower()
    if any(
        lower.startswith(p)
        for p in (
            "/api/v1/kitchen/",
            "/api/v1/chef/",
            "/api/v1/orders/kitchen/",
            "/api/v1/dashboard/chef/",
        )
    ):
        return "chef"
    if "/admin/" in lower:
        return "chef"
    return "customer"


def _is_upload_endpoint(path: str, method: str, operation: dict[str, Any]) -> bool:
    if method.upper() != "POST":
        return False
    body = operation.get("requestBody") or {}
    content = body.get("content") or {}
    if "multipart/form-data" in content:
        return True
    return path.rstrip("/").endswith("/avatar") or "/images" in path


def _is_email_related(path: str, method: str) -> bool:
    lower = path.lower()
    if lower.endswith("/contact") or lower.endswith("/contacts"):
        return True
    if "/admin/test-email" in lower:
        return True
    # Triggers that schedule email (documented as email-related API behavior)
    if lower.endswith("/auth/register") and method.upper() == "POST":
        return True
    if lower.rstrip("/") == "/api/v1/orders" and method.upper() == "POST":
        return True
    return False


def _integration_summary(
    *,
    items: list[tuple[str, str, str, dict[str, Any]]],
    kitchen_alias_ops: int,
) -> str:
    public = customer = chef = uploads = email_related = 0
    for _tag, method, path, operation in items:
        kind = _classify_access(path, method.upper(), operation)
        if kind == "public":
            public += 1
        elif kind == "chef":
            chef += 1
        else:
            customer += 1
        if _is_upload_endpoint(path, method, operation):
            uploads += 1
        if _is_email_related(path, method):
            email_related += 1

    total = len(items)
    return "\n".join(
        [
            "",
            "---",
            "",
            "## Integration summary",
            "",
            "Counts below are **canonical** routes documented in this file "
            "(kitchen URL aliases are counted separately and are not duplicate handlers).",
            "",
            "| Metric | Count |",
            "|--------|------:|",
            f"| **Total canonical endpoints** | **{total}** |",
            f"| Public endpoints | {public} |",
            f"| Customer-primary endpoints | {customer} |",
            f"| Chef-only endpoints (kitchen + `/admin/*`) | {chef} |",
            f"| File upload endpoints | {uploads} |",
            f"| Email-related endpoints (trigger or send) | {email_related} |",
            f"| Kitchen URL alias mounts (same handlers) | {kitchen_alias_ops} |",
            "| Deprecated endpoints | 0 |",
            "",
            "### Email-related endpoints (API behavior)",
            "",
            "| Endpoint | Behavior |",
            "|----------|----------|",
            "| `POST /api/v1/auth/register` | Schedules Welcome email (non-blocking) |",
            "| `POST /api/v1/contact` | Awaits contact inbox email via Brevo (502 on failure) |",
            "| `POST /api/v1/orders` | Schedules order confirmation + chef notification |",
            "| `POST /api/v1/admin/test-email` | Awaited Brevo connectivity test (chef) |",
            "",
            "### Not implemented",
            "",
            "- Dedicated **change-password** endpoint — not present; omit from frontend flows.",
            "- **OTP / Twilio / Resend** — removed; do not integrate against them.",
            "",
            "### Frontend checklist",
            "",
            "1. Use `Authorization: Bearer <access_token>` on every protected call.",
            "2. Route UI by `data.role` (`customer` | `chef`) after login/register.",
            "3. Prefer `/api/v1/kitchen/*` for the chef dashboard.",
            "4. Call contact/register/orders through this API only — never Brevo from the browser.",
            "5. Keep this `api.md` as the contract; regenerate with "
            "`uv run python scripts/generate_api_md.py` after backend route changes.",
            "",
        ]
    )


def main() -> None:
    spec = _load_openapi()
    paths: dict[str, Any] = spec.get("paths") or {}

    catalog_grouped: dict[str, list[tuple[str, str, str, str]]] = defaultdict(list)
    detail_grouped: dict[str, list[tuple[str, str, dict[str, Any]]]] = defaultdict(list)
    detail_blocks: list[str] = []
    op_count = 0
    kitchen_alias_ops = 0

    for path, path_item in paths.items():
        if _is_kitchen_alias(path):
            for method, operation in path_item.items():
                if method in {"get", "post", "put", "patch", "delete"} and isinstance(
                    operation, dict
                ):
                    kitchen_alias_ops += 1

    items: list[tuple[str, str, str, dict[str, Any]]] = []
    for path, path_item in sorted(paths.items()):
        if _is_kitchen_alias(path):
            continue
        for method, operation in path_item.items():
            if method not in {"get", "post", "put", "patch", "delete"}:
                continue
            if not isinstance(operation, dict):
                continue
            tags = operation.get("tags") or ["Other"]
            tag = tags[0]
            items.append((tag, method, path, operation))

    def sort_key(item: tuple[str, str, str, dict[str, Any]]) -> tuple[int, str, str]:
        tag, method, path, _ = item
        try:
            idx = TAG_ORDER.index(tag)
        except ValueError:
            idx = 999
        return (idx, path, method)

    for tag, method, path, operation in sorted(items, key=sort_key):
        auth, _role = _auth_for_path(path, method.upper(), operation)
        summary = operation.get("summary") or path
        catalog_grouped[tag].append((method.upper(), path, auth, summary))
        detail_grouped[tag].append((method.upper(), path, operation))
        detail_blocks.append(
            _render_endpoint(spec=spec, path=path, method=method, operation=operation)
        )
        op_count += 1

    catalog = _catalog_lines(catalog_grouped)
    front = FRONT_MATTER.format(OP_COUNT=op_count, CATALOG=catalog)
    summary = _integration_summary(items=items, kitchen_alias_ops=kitchen_alias_ops)
    body = front + "\n".join(detail_blocks) + summary
    API_MD.write_text(body, encoding="utf-8")
    _write_module_docs(spec=spec, grouped_ops=detail_grouped)
    print(f"Wrote {API_MD} ({API_MD.stat().st_size} bytes, {op_count} endpoints)")
    print(f"Wrote module docs under {DOCS_API}")
    print(f"Kitchen alias operations (not duplicated in detail): {kitchen_alias_ops}")


if __name__ == "__main__":
    main()
