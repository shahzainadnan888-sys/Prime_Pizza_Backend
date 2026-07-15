# Admin Coupons

## List Coupons

### Endpoint

`GET /api/v1/admin/coupons`

### Description

List Coupons

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

_None._

### Query Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `q` | no | string | null | — |
| `is_active` | no | boolean | null | — |
| `coupon_type` | no | enum: `percentage` | `fixed` | null | — |
| `sort` | no | string | — |
| `page` | no | integer | Page number |
| `page_size` | no | integer | Items per page |

### Request Body Schema

_No request body._

### Validation Rules

- `page`: min=1
- `page_size`: min=1, max=100

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Example Response

```json
{
  "success": true,
  "message": "Success",
  "data": [
    {
      "usage_limit": null,
      "created_at": "2026-07-15T12:00:00Z",
      "value": "string",
      "per_user_limit": null,
      "coupon_type": "percentage",
      "code": "string",
      "updated_at": "2026-07-15T12:00:00Z",
      "description": null,
      "is_active": true,
      "id": "00000000-0000-4000-8000-000000000001",
      "used_count": 1,
      "starts_at": null,
      "minimum_order_amount": null,
      "expires_at": null,
      "maximum_discount": null
    }
  ],
  "request_id": "00000000-0000-4000-8000-000000000099",
  "meta": {
    "page": 1,
    "page_size": 20,
    "total_items": 1,
    "total_pages": 1,
    "has_next": false,
    "has_previous": false
  }
}
```

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Create Coupon

### Endpoint

`POST /api/v1/admin/coupons`

### Description

Create Coupon

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |
| `Content-Type: application/json` | yes (JSON bodies) |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `code` | string | yes | minLength=3; maxLength=50 |
| `description` | string | null | no | — |
| `coupon_type` | enum: `percentage` | `fixed` | yes | values: `percentage`, `fixed` |
| `value` | number | string | yes | — |
| `minimum_order_amount` | number | string | null | no | — |
| `maximum_discount` | number | string | null | no | — |
| `usage_limit` | integer | null | no | — |
| `per_user_limit` | integer | null | no | — |
| `is_active` | boolean | no | default=`true` |
| `starts_at` | string (date-time) | null | no | — |
| `expires_at` | string (date-time) | null | no | — |

### Example Request

```http
POST /api/v1/admin/coupons HTTP/1.1
Host: {BASE_URL}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "coupon_type": "percentage",
  "code": "string",
  "value": null,
  "description": null,
  "minimum_order_amount": null,
  "maximum_discount": null,
  "usage_limit": null,
  "per_user_limit": null,
  "is_active": true,
  "starts_at": null,
  "expires_at": null
}
```

### Validation Rules

- Required body fields: `code`, `coupon_type`, `value`
- `code`: minLength=3, maxLength=50
- `coupon_type`: enum=percentage|fixed

### Response Schema

Success status: **201**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `201` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `201` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Delete Coupon

### Endpoint

`DELETE /api/v1/admin/coupons/{coupon_id}`

### Description

Delete Coupon

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `coupon_id` | yes | string (uuid) | — |

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `success` | boolean | no | default=`true` |
| `message` | string | yes | — |
| `request_id` | string | null | no | — |

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Get Coupon

### Endpoint

`GET /api/v1/admin/coupons/{coupon_id}`

### Description

Get Coupon

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `coupon_id` | yes | string (uuid) | — |

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Update Coupon

### Endpoint

`PATCH /api/v1/admin/coupons/{coupon_id}`

### Description

Update Coupon

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |
| `Content-Type: application/json` | yes (JSON bodies) |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `coupon_id` | yes | string (uuid) | — |

### Query Parameters

_None._

### Request Body Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `description` | string | null | no | — |
| `coupon_type` | enum: `percentage` | `fixed` | null | no | — |
| `value` | number | string | null | no | — |
| `minimum_order_amount` | number | string | null | no | — |
| `maximum_discount` | number | string | null | no | — |
| `usage_limit` | integer | null | no | — |
| `per_user_limit` | integer | null | no | — |
| `is_active` | boolean | null | no | — |
| `starts_at` | string (date-time) | null | no | — |
| `expires_at` | string (date-time) | null | no | — |

### Example Request

```http
PATCH /api/v1/admin/coupons/{coupon_id} HTTP/1.1
Host: {BASE_URL}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "description": null,
  "coupon_type": null,
  "value": null,
  "minimum_order_amount": null,
  "maximum_discount": null,
  "usage_limit": null,
  "per_user_limit": null,
  "is_active": null,
  "starts_at": null,
  "expires_at": null
}
```

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Disable Coupon

### Endpoint

`PATCH /api/v1/admin/coupons/{coupon_id}/disable`

### Description

Disable Coupon

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `coupon_id` | yes | string (uuid) | — |

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Enable Coupon

### Endpoint

`PATCH /api/v1/admin/coupons/{coupon_id}/enable`

### Description

Enable Coupon

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `coupon_id` | yes | string (uuid) | — |

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Get Coupon Usage

### Endpoint

`GET /api/v1/admin/coupons/{coupon_id}/usage`

### Description

Get Coupon Usage

### Authentication Required

Yes — Bearer access token

### Required Role

`chef` (permission-gated; no separate admin role)

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `coupon_id` | yes | string (uuid) | — |

### Query Parameters

_None._

### Request Body Schema

_No request body._

### Validation Rules

_See field constraints in the request schema table (and query/path params)._

### Response Schema

Success status: **200**

Envelope: `success`, `message`, `data`, `request_id` (and `meta` when paginated).

**`data` schema**

_No fields (or opaque object)._

### Success Responses

- `200` — success (see Example Response / Response Schema)

### Error Responses

| Code | Description |
|------|-------------|
| `200` | Successful Response |
| `422` | Validation Error |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---
