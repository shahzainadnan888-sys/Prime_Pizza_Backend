# Wishlist

## Get Wishlist

### Endpoint

`GET /api/v1/wishlist`

### Description

Get Wishlist

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

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Add Wishlist Item

### Endpoint

`POST /api/v1/wishlist`

### Description

Add Wishlist Item

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

_None._

### Query Parameters

_None._

### Request Body Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `product_id` | string (uuid) | yes | — |

### Example Request

```http
POST /api/v1/wishlist HTTP/1.1
Host: {BASE_URL}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "product_id": "00000000-0000-4000-8000-000000000001"
}
```

### Validation Rules

- Required body fields: `product_id`

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

## Clear Wishlist

### Endpoint

`DELETE /api/v1/wishlist/clear`

### Description

Clear Wishlist

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

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Remove Wishlist Item

### Endpoint

`DELETE /api/v1/wishlist/{product_id}`

### Description

Remove Wishlist Item

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
| `product_id` | yes | string (uuid) | — |

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
