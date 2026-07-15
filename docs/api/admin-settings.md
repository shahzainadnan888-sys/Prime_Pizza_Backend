# Admin Settings

## List Settings

### Endpoint

`GET /api/v1/admin/settings`

### Description

List Settings

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

## Bulk Update Settings

### Endpoint

`PUT /api/v1/admin/settings`

### Description

Bulk Update Settings

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
| `settings` | Settings | yes | — |

### Example Request

```http
PUT /api/v1/admin/settings HTTP/1.1
Host: {BASE_URL}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "settings": {}
}
```

### Validation Rules

- Required body fields: `settings`

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

## Get Restaurant Settings

### Endpoint

`GET /api/v1/admin/settings/restaurant`

### Description

Get Restaurant Settings

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

## Get Setting

### Endpoint

`GET /api/v1/admin/settings/{key}`

### Description

Get Setting

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
| `key` | yes | string | — |

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

## Upsert Setting

### Endpoint

`PUT /api/v1/admin/settings/{key}`

### Description

Upsert Setting

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
| `key` | yes | string | — |

### Query Parameters

_None._

### Request Body Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `value` | string | null | no | — |
| `value_json` | object | array<any> | null | no | — |
| `description` | string | null | no | — |
| `is_public` | boolean | null | no | — |

### Example Request

```http
PUT /api/v1/admin/settings/{key} HTTP/1.1
Host: {BASE_URL}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "value": null,
  "value_json": null,
  "description": null,
  "is_public": null
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
