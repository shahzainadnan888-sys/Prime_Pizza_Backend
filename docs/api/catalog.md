# Catalog

## List Categories

### Endpoint

`GET /api/v1/categories`

### Description

List Categories

### Authentication Required

No

### Required Role

—

### Headers

| Header | Required |
|--------|----------|
| — | — |

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

## Get Category

### Endpoint

`GET /api/v1/categories/{slug}`

### Description

Get Category

### Authentication Required

No

### Required Role

—

### Headers

| Header | Required |
|--------|----------|
| — | — |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `slug` | yes | string | — |

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

## List Deals

### Endpoint

`GET /api/v1/deals`

### Description

List Deals

### Authentication Required

No

### Required Role

—

### Headers

| Header | Required |
|--------|----------|
| — | — |

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

## Get Deal

### Endpoint

`GET /api/v1/deals/{slug}`

### Description

Get Deal

### Authentication Required

No

### Required Role

—

### Headers

| Header | Required |
|--------|----------|
| — | — |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `slug` | yes | string | — |

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

## List Products

### Endpoint

`GET /api/v1/products`

### Description

List Products

### Authentication Required

No

### Required Role

—

### Headers

| Header | Required |
|--------|----------|
| — | — |

### Path Parameters

_None._

### Query Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `category` | no | string | null | — |
| `category_id` | no | string (uuid) | null | — |
| `min_price` | no | number | string | null | — |
| `max_price` | no | number | string | null | — |
| `is_available` | no | boolean | null | — |
| `is_featured` | no | boolean | null | — |
| `is_popular` | no | boolean | null | — |
| `is_best_seller` | no | boolean | null | — |
| `vegetarian` | no | boolean | null | — |
| `tag` | no | enum: `popular` | `featured` | `new` | `limited` | `spicy` | `vegetarian` | `best_seller` | `chef_special` | `kids_favorite` | null | — |
| `min_calories` | no | integer | null | — |
| `max_calories` | no | integer | null | — |
| `max_preparation_time` | no | integer | null | — |
| `sort` | no | enum: `newest` | `oldest` | `price_asc` | `price_desc` | `popularity` | `alphabetical` | `preparation_time` | — |
| `q` | no | string | null | — |
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
      "is_available": true,
      "sort_order": 1,
      "stock_status": "in_stock",
      "name": "string",
      "created_at": "2026-07-15T12:00:00Z",
      "id": "00000000-0000-4000-8000-000000000001",
      "is_best_seller": true,
      "base_price": "string",
      "slug": "string",
      "is_popular": true,
      "category_id": "00000000-0000-4000-8000-000000000001",
      "is_featured": true,
      "short_description": null,
      "discount_price": null,
      "image_url": null,
      "preparation_time_minutes": null,
      "calories": null,
      "tags": [
        "string"
      ]
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

## Featured Products

### Endpoint

`GET /api/v1/products/featured`

### Description

Featured Products

### Authentication Required

No

### Required Role

—

### Headers

| Header | Required |
|--------|----------|
| — | — |

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

## Popular Products

### Endpoint

`GET /api/v1/products/popular`

### Description

Popular Products

### Authentication Required

No

### Required Role

—

### Headers

| Header | Required |
|--------|----------|
| — | — |

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

## Recommended Products

### Endpoint

`GET /api/v1/products/recommended`

### Description

Recommended Products

### Authentication Required

No

### Required Role

—

### Headers

| Header | Required |
|--------|----------|
| — | — |

### Path Parameters

_None._

### Query Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `product_slug` | no | string | null | — |
| `category` | no | string | null | — |

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

## Search Products

### Endpoint

`GET /api/v1/products/search`

### Description

Search Products

### Authentication Required

No

### Required Role

—

### Headers

| Header | Required |
|--------|----------|
| — | — |

### Path Parameters

_None._

### Query Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `q` | yes | string | — |
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
      "is_available": true,
      "sort_order": 1,
      "stock_status": "in_stock",
      "name": "string",
      "created_at": "2026-07-15T12:00:00Z",
      "id": "00000000-0000-4000-8000-000000000001",
      "is_best_seller": true,
      "base_price": "string",
      "slug": "string",
      "is_popular": true,
      "category_id": "00000000-0000-4000-8000-000000000001",
      "is_featured": true,
      "short_description": null,
      "discount_price": null,
      "image_url": null,
      "preparation_time_minutes": null,
      "calories": null,
      "tags": [
        "string"
      ]
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

## Get Product

### Endpoint

`GET /api/v1/products/{slug}`

### Description

Get Product

### Authentication Required

No

### Required Role

—

### Headers

| Header | Required |
|--------|----------|
| — | — |

### Path Parameters

| Name | Required | Type | Description |
|------|----------|------|-------------|
| `slug` | yes | string | — |

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
