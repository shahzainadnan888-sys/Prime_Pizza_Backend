# Authentication

## Login with email and password

### Endpoint

`POST /api/v1/auth/login`

### Description

Validates credentials and issues a JWT access + refresh pair.

### Authentication Required

No

### Required Role

—

### Headers

| Header | Required |
|--------|----------|
| `Content-Type: application/json` | yes (JSON bodies) |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `email` | string (email) | yes | — |
| `password` | string | yes | minLength=1; maxLength=128 |

### Example Request

```http
POST /api/v1/auth/login HTTP/1.1
Host: {BASE_URL}
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "string"
}
```

### Validation Rules

- Required body fields: `email`, `password`
- `password`: minLength=1, maxLength=128

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
| `200` | Authenticated |
| `401` | Invalid credentials |
| `422` | Validation Error |
| `429` | Rate limited |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---

## Logout and revoke tokens

### Endpoint

`POST /api/v1/auth/logout`

### Description

Logout and revoke tokens

### Authentication Required

Yes — Bearer access token

### Required Role

`customer` | `chef`

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

_No fields (or opaque object)._

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

## Current authenticated user

### Endpoint

`GET /api/v1/auth/me`

### Description

Current authenticated user

### Authentication Required

Yes — Bearer access token

### Required Role

`customer` | `chef`

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

## Refresh access token

### Endpoint

`POST /api/v1/auth/refresh`

### Description

Refresh access token

### Authentication Required

No

### Required Role

—

### Headers

| Header | Required |
|--------|----------|
| `Content-Type: application/json` | yes (JSON bodies) |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `refresh_token` | string | yes | minLength=20 |

### Example Request

```http
POST /api/v1/auth/refresh HTTP/1.1
Host: {BASE_URL}
Content-Type: application/json

{
  "refresh_token": "string"
}
```

### Validation Rules

- Required body fields: `refresh_token`
- `refresh_token`: minLength=20

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

## Register a customer account

### Endpoint

`POST /api/v1/auth/register`

### Description

Creates a customer with email/password (bcrypt), persists to PostgreSQL, mirrors to data/users.json, and returns a JWT access + refresh pair.

### Authentication Required

No

### Required Role

—

### Headers

| Header | Required |
|--------|----------|
| `Content-Type: application/json` | yes (JSON bodies) |

### Path Parameters

_None._

### Query Parameters

_None._

### Request Body Schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `first_name` | string | yes | minLength=1; maxLength=80 |
| `last_name` | string | yes | minLength=1; maxLength=80 |
| `email` | string (email) | yes | — |
| `password` | string | yes | minLength=8; maxLength=128 |
| `confirm_password` | string | yes | minLength=8; maxLength=128 |
| `phone_number` | string | null | no | — |

### Example Request

```http
POST /api/v1/auth/register HTTP/1.1
Host: {BASE_URL}
Content-Type: application/json

{
  "password": "string",
  "last_name": "string",
  "confirm_password": "string",
  "email": "user@example.com",
  "first_name": "string",
  "phone_number": null
}
```

### Validation Rules

- Required body fields: `confirm_password`, `email`, `first_name`, `last_name`, `password`
- `first_name`: minLength=1, maxLength=80
- `last_name`: minLength=1, maxLength=80
- `password`: minLength=8, maxLength=128
- `confirm_password`: minLength=8, maxLength=128

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
| `201` | Registered — returns token pair and user profile |
| `409` | Email or phone already registered |
| `422` | Validation error |
| `429` | Rate limited |

Also see [Global error responses](#global-error-responses). Common for this route:

- `401` — missing/invalid Bearer token (protected routes)
- `403` — authenticated but wrong role/permission
- `422` — validation failure (body/query/path)
- `429` — rate limited

---
