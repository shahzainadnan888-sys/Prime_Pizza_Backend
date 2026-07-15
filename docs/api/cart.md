# Cart

## Get Cart

### Endpoint

`GET /api/v1/cart`

### Description

Get Cart

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

## Apply Coupon

### Endpoint

`POST /api/v1/cart/apply-coupon`

### Description

Apply Coupon

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
| `code` | string | yes | minLength=2; maxLength=50 |

### Example Request

```http
POST /api/v1/cart/apply-coupon HTTP/1.1
Host: {BASE_URL}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "code": "string"
}
```

### Validation Rules

- Required body fields: `code`
- `code`: minLength=2, maxLength=50

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

## Clear Cart

### Endpoint

`DELETE /api/v1/cart/clear`

### Description

Clear Cart

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

## Add Cart Item

### Endpoint

`POST /api/v1/cart/items`

### Description

Add Cart Item

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
| `variant_id` | string (uuid) | null | no | — |
| `quantity` | integer | no | min=1.0; max=100.0; default=`1` |
| `extra_option_ids` | array<string (uuid)> | no | — |
| `extras` | array<CartExtraInput> | no | — |
| `special_instructions` | string | null | no | — |

### Example Request

```http
POST /api/v1/cart/items HTTP/1.1
Host: {BASE_URL}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "product_id": "00000000-0000-4000-8000-000000000001",
  "variant_id": null,
  "quantity": 1,
  "extra_option_ids": [
    "00000000-0000-4000-8000-000000000001"
  ],
  "extras": [
    {
      "option_id": "00000000-0000-4000-8000-000000000001",
      "quantity": 1
    }
  ],
  "special_instructions": null
}
```

### Validation Rules

- Required body fields: `product_id`
- `quantity`: min=1.0, max=100.0

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

## Remove Cart Item

### Endpoint

`DELETE /api/v1/cart/items/{item_id}`

### Description

Remove Cart Item

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
| `item_id` | yes | string (uuid) | — |

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

## Update Cart Item

### Endpoint

`PATCH /api/v1/cart/items/{item_id}`

### Description

Update Cart Item

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
| `item_id` | yes | string (uuid) | — |

### Query Parameters

_None._

### Request Body Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `quantity` | integer | null | no | — |
| `special_instructions` | string | null | no | — |
| `extra_option_ids` | array<string (uuid)> | null | no | — |
| `extras` | array<CartExtraInput> | null | no | — |

### Example Request

```http
PATCH /api/v1/cart/items/{item_id} HTTP/1.1
Host: {BASE_URL}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "quantity": null,
  "special_instructions": null,
  "extra_option_ids": null,
  "extras": null
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

## Remove Coupon

### Endpoint

`DELETE /api/v1/cart/remove-coupon`

### Description

Remove Coupon

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

## Get Cart Summary

### Endpoint

`GET /api/v1/cart/summary`

### Description

Get Cart Summary

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
