# Health

Back to [`api.md`](../../api.md) · [`index`](README.md)

## `GET /`

**Summary:** API root

**Auth:** Public

Service identity endpoint.

**Success responses:** `200`

---

## `GET /health`

**Summary:** Liveness probe

**Auth:** Public

Process liveness — does not check external dependencies.

**Success responses:** `200`

---

## `GET /health/database`

**Summary:** Database readiness

**Auth:** Public

Verify PostgreSQL connectivity.

**Success responses:** `200`

---

## `GET /health/redis`

**Summary:** Redis readiness

**Auth:** Public

Verify Redis connectivity.

**Success responses:** `200`

---

## `GET /health/services`

**Summary:** Dependency and configuration readiness

**Auth:** Public

Aggregate readiness for database, Redis, and configured third-party services.

Twilio / Cloudinary / Resend checks verify configuration presence (not live
outbound calls) to avoid costing API credits on every probe.

**Success responses:** `200`

---

## `GET /api/v1/`

**Summary:** API root

**Auth:** Public

Service identity endpoint.

**Success responses:** `200`

---

## `GET /api/v1/health`

**Summary:** Liveness probe

**Auth:** Public

Process liveness — does not check external dependencies.

**Success responses:** `200`

---

## `GET /api/v1/health/database`

**Summary:** Database readiness

**Auth:** Public

Verify PostgreSQL connectivity.

**Success responses:** `200`

---

## `GET /api/v1/health/redis`

**Summary:** Redis readiness

**Auth:** Public

Verify Redis connectivity.

**Success responses:** `200`

---

## `GET /api/v1/health/services`

**Summary:** Dependency and configuration readiness

**Auth:** Public

Aggregate readiness for database, Redis, and configured third-party services.

Twilio / Cloudinary / Resend checks verify configuration presence (not live
outbound calls) to avoid costing API credits on every probe.

**Success responses:** `200`

---
