# Authentication

Back to [`api.md`](../../api.md) · [`index`](README.md)

## `POST /api/v1/auth/send-otp`

**Summary:** Send OTP via Twilio Verify

**Auth:** Public

Sends a one-time verification code to an E.164 phone number. Rate limited per phone, per IP, and globally. Public endpoint.

**Body**

- Content-Type: `application/json`
- Schema: `SendOTPRequest`

| Field | Type | Required |
|-------|------|----------|
| `phone_number` | `string` | yes |

**Success responses:** `200`

---

## `POST /api/v1/auth/verify-otp`

**Summary:** Verify OTP and issue tokens

**Auth:** Public

Verifies the OTP, upserts the user (owner phone becomes owner role), mirrors identity to data/users.json, and returns JWT access + refresh tokens.

**Body**

- Content-Type: `application/json`
- Schema: `VerifyOTPRequest`

| Field | Type | Required |
|-------|------|----------|
| `phone_number` | `string` | yes |
| `code` | `string` | yes |

**Success responses:** `200`

---

## `POST /api/v1/auth/refresh`

**Summary:** Refresh access token

**Auth:** Public

**Body**

- Content-Type: `application/json`
- Schema: `RefreshTokenRequest`

| Field | Type | Required |
|-------|------|----------|
| `refresh_token` | `string` | yes |

**Success responses:** `200`

---

## `POST /api/v1/auth/logout`

**Summary:** Logout and revoke tokens

**Auth:** Bearer

**Body**

- Content-Type: `application/json`

**Success responses:** `200`

---

## `GET /api/v1/auth/me`

**Summary:** Current authenticated user

**Auth:** Bearer

**Success responses:** `200`

---
