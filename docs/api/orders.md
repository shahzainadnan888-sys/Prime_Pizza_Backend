# Orders

## List My Orders

### Endpoint

`GET /api/v1/orders`

### Description

List My Orders

### Authentication Required

Yes — Bearer access token (verified account)

### Required Role

`customer` (primary) | `chef`

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

## Place Order

### Endpoint

`POST /api/v1/orders`

### Description

Place Order

### Authentication Required

Yes — Bearer access token (verified account)

### Required Role

`customer` (primary) | `chef`

### Headers

| Header | Required |
|--------|----------|
| `Authorization: Bearer <access_token>` | yes |
| `Content-Type: application/json` | yes (JSON bodies) |
| `Idempotency-Key` | recommended for `POST /orders` |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `address_id` | string (uuid) | null | no | — |
| `payment_method` | enum: `cash_on_delivery` | `card` | `online` | `wallet` | no | values: `cash_on_delivery`, `card`, `online`, `wallet` |
| `notes` | string | null | no | — |
| `idempotency_key` | string | null | no | — |
| `latitude` | number | string | null | no | — |
| `longitude` | number | string | null | no | — |
| `gps_accuracy` | number | string | null | no | GPS accuracy in meters, when reported by the device |

### Example Request

```http
POST /api/v1/orders HTTP/1.1
Host: {BASE_URL}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "address_id": null,
  "payment_method": "cash_on_delivery",
  "notes": null,
  "idempotency_key": null,
  "latitude": null,
  "longitude": null,
  "gps_accuracy": null
}
```

### Validation Rules

- `payment_method`: enum=cash_on_delivery|card|online|wallet

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

## Get My Order

### Endpoint

`GET /api/v1/orders/{order_id}`

### Description

Get My Order

### Authentication Required

Yes — Bearer access token (verified account)

### Required Role

`customer` (primary) | `chef`

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

## Cancel My Order

### Endpoint

`PATCH /api/v1/orders/{order_id}/cancel`

### Description

Cancel My Order

### Authentication Required

Yes — Bearer access token (verified account)

### Required Role

`customer` (primary) | `chef`

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

_No fields (or opaque object)._

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

## Track My Order

### Endpoint

`GET /api/v1/orders/{order_id}/tracking`

### Description

Track My Order

### Authentication Required

Yes — Bearer access token (verified account)

### Required Role

`customer` (primary) | `chef`

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
