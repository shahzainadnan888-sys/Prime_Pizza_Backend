# Admin Orders

## List Orders

### Endpoint

`GET /api/v1/admin/orders`

### Description

List Orders

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
| `status` | no | enum: `pending` | `confirmed` | `preparing` | `ready` | `out_for_delivery` | `delivered` | `cancelled` | `refunded` | null | — |
| `payment_status` | no | enum: `pending` | `paid` | `failed` | `refunded` | `partially_refunded` | `cancelled` | null | — |
| `date_from` | no | string (date-time) | null | — |
| `date_to` | no | string (date-time) | null | — |
| `sort` | no | string | — |
| `q` | no | string | null | — |
| `user_id` | no | string (uuid) | null | — |
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
      "order_number": "string",
      "created_at": "2026-07-15T12:00:00Z",
      "payment_method": "cash_on_delivery",
      "currency": "string",
      "updated_at": "2026-07-15T12:00:00Z",
      "id": "00000000-0000-4000-8000-000000000001",
      "status": "pending",
      "grand_total": "string",
      "payment_status": "pending",
      "item_count": 0
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

## Get Order

### Endpoint

`GET /api/v1/admin/orders/{order_id}`

### Description

Get Order

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
| `order_id` | yes | string (uuid) | — |

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

## Update Order Notes

### Endpoint

`PATCH /api/v1/admin/orders/{order_id}/notes`

### Description

Update Order Notes

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
| `order_id` | yes | string (uuid) | — |

### Query Parameters

_None._

### Request Body Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `notes` | string | null | no | — |
| `kitchen_notes` | string | null | no | — |
| `internal_notes` | string | null | no | — |

### Example Request

```http
PATCH /api/v1/admin/orders/{order_id}/notes HTTP/1.1
Host: {BASE_URL}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "notes": null,
  "kitchen_notes": null,
  "internal_notes": null
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

## Update Payment Status

### Endpoint

`PATCH /api/v1/admin/orders/{order_id}/payment`

### Description

Update Payment Status

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
| `order_id` | yes | string (uuid) | — |

### Query Parameters

_None._

### Request Body Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `payment_status` | enum: `pending` | `paid` | `failed` | `refunded` | `partially_refunded` | `cancelled` | yes | values: `pending`, `paid`, `failed`, `refunded`, `partially_refunded`, `cancelled` |
| `notes` | string | null | no | — |

### Example Request

```http
PATCH /api/v1/admin/orders/{order_id}/payment HTTP/1.1
Host: {BASE_URL}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "payment_status": "pending",
  "notes": null
}
```

### Validation Rules

- Required body fields: `payment_status`
- `payment_status`: enum=pending|paid|failed|refunded|partially_refunded|cancelled

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

## Update Order Status

### Endpoint

`PATCH /api/v1/admin/orders/{order_id}/status`

### Description

Update Order Status

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
| `order_id` | yes | string (uuid) | — |

### Query Parameters

_None._

### Request Body Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `status` | enum: `pending` | `confirmed` | `preparing` | `ready` | `out_for_delivery` | `delivered` | `cancelled` | `refunded` | yes | values: `pending`, `confirmed`, `preparing`, `ready`, `out_for_delivery`, `delivered`, `cancelled`, `refunded` |
| `notes` | string | null | no | — |

### Example Request

```http
PATCH /api/v1/admin/orders/{order_id}/status HTTP/1.1
Host: {BASE_URL}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "status": "pending",
  "notes": null
}
```

### Validation Rules

- Required body fields: `status`
- `status`: enum=pending|confirmed|preparing|ready|out_for_delivery|delivered|cancelled|refunded

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
