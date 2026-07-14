# Production Hardening

This document captures the production-hardening phase for the Prime Pizza FastAPI backend.

## Security improvements

- Redis-backed HTTP rate limiting with per-route policies (auth, OTP, orders, checkout, search, admin, upload, email, health).
- Auth/upload/email/orders policies **fail closed** when Redis is unavailable; other policies fail open for availability.
- IP allowlist bypass is **off by default**; requires both `RATE_LIMIT_OWNER_BYPASS` and non-empty `RATE_LIMIT_BYPASS_IPS`.
- Client IP resolution ignores spoofable `X-Forwarded-For` unless `TRUST_X_FORWARDED_FOR=true` **and** the peer is in `TRUSTED_PROXY_IPS`.
- OTP abuse controls: phone + IP + global send budgets (atomic Redis INCR+EXPIRE).
- Refresh-token rotation uses atomic `GETDEL` consume to block concurrent reuse races.
- JWT signing/verification pinned to **HS256** (env allowlist).
- OpenAPI/Swagger/ReDoc disabled in production (`docs_enabled`).
- Security headers: CSP, HSTS (production / `ENABLE_HSTS`), COOP, CORP, Permissions-Policy.
- `MAX_REQUEST_BODY_BYTES` enforced via middleware (413); uploads stream-capped before full buffer.
- Filename sanitization + magic-byte image validation; Content-Type required for uploads.
- Admin customer update cannot change `role` (mass-assignment closed).
- Maintenance mode enforced from system settings (admin/auth/health remain reachable).
- Production settings validators reject debug mode, placeholder secrets, HTTP frontend URLs, default hosts, non-TLS Redis, empty bypass/proxy configs when those flags are on.
- Exception `details` sanitized in production; stack traces never returned to clients.
- Security event logging with Bearer/JWT/password/OTP redaction.

## Performance optimizations

- Configurable DB pool (`DB_POOL_SIZE`, overflow, recycle, timeout).
- Redis client `max_connections`.
- Dashboard order-status counts collapsed into one GROUP BY query.
- Commerce config (delivery/tax/maintenance) cached in Redis with write-through invalidation.
- Catalog/dashboard/order/cart caches with targeted invalidation.
- Composite DB indexes for orders, notifications, and product catalog hot paths.
- GZip + response timing + in-process metrics.

## Redis optimization strategy

| Namespace | Purpose | Invalidation |
|-----------|---------|--------------|
| `catalog:*` | Categories, featured, popular, deals, product detail, search | Write wipe via `delete_prefix` |
| `cart:*` | Customer cart summary | Per-user delete on mutation |
| `orders:*` | Tracking + checkout lock + idempotency | Targeted deletes + dashboard wipe |
| `dashboard:*` | Stats/analytics/charts | Invalidate on order + admin mutations |
| `settings:commerce` | Delivery/tax/maintenance runtime config | Invalidate on settings upsert |
| `settings:maintenance` | Fast maintenance flag | Set/cleared on `maintenance.mode` writes |
| `auth:*` | OTP sessions, rate counters, refresh/blacklist | TTL + atomic consume |
| `rl:*` | HTTP rate-limit windows | Minute/hour/burst buckets |

## Database optimization strategy

- Soft-delete partial indexes for uniqueness.
- Composites: `(user_id, created_at)`, `(status, created_at)` on orders; notification/catalog composites.
- Eager `selectinload` for cart/order/product detail graphs.
- Env-driven pool sizing for Neon/worker sizing.

## Monitoring architecture

- Process-local `app.monitoring.metrics` counters/timers.
- Public `GET /health/services` exposes **minimal** metrics (`uptime_seconds`, `http_requests_total`) — not full timer dumps.
- `X-Process-Time` + structured access logs with `duration_ms`.
- Ready for a Prometheus scrape adapter later.

## Logging improvements

- Request ID bound into Loguru context.
- Structured JSON sink for production/staging.
- Security sink with 90-day retention; app logs 30 days compressed.
- Redaction: Authorization/password/OTP/API keys, Bearer tokens, bare JWTs.
- File sinks disable backtrace/diagnose outside debug.

## Middleware improvements

Order: TrustedHost → CORS → GZip → SecurityHeaders → RequestID →
RequestLogging → ResponseTime → **BodyLimit** → **Maintenance** →
Auth bootstrap → Authz context → RateLimit → route.

## Rate limiting strategy

| Policy | Defaults (min / hour / burst) | Redis outage |
|--------|-------------------------------|--------------|
| auth | 20 / 120 / 10 | Fail closed |
| orders | 15 / 100 / 8 | Fail closed |
| checkout | 30 / 300 / 12 | Fail open (default list excludes) unless configured |
| search | 60 / 1000 / 25 | Fail open |
| admin | 90 / 2000 / 30 | Fail open |
| upload | 20 / 200 / 8 | Fail closed |
| email | 10 / 60 / 5 | Fail closed |
| health | 180 / 5000 / 60 | Fail open |
| default | 120 / 3000 / 40 | Fail open |

OTP retains stricter phone/IP/global counters. Disabled when `APP_ENV=test`.

## Health check system

| Endpoint | Role |
|----------|------|
| `GET /` | Identity (docs paths omitted when disabled) |
| `GET /health` | Liveness |
| `GET /health/database` | Postgres `SELECT 1` |
| `GET /health/redis` | Redis `PING` |
| `GET /health/services` | Aggregate DB + Redis + Twilio/Cloudinary/Resend config + minimal metrics |

## New environment variables

- `TRUST_X_FORWARDED_FOR` (default `false`)
- `TRUSTED_PROXY_IPS`
- `RATE_LIMIT_OWNER_BYPASS` (default `false`)
- `RATE_LIMIT_FAIL_CLOSED_POLICIES`
- `RATE_LIMIT_CHECKOUT_*`

## Migration

Apply: `alembic upgrade head` (revision `a1b2c3d4e5f6_production_hardening_composite_indexes`).
