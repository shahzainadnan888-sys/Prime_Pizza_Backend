# Backup & Disaster Recovery — Prime Pizza API

## PostgreSQL (Neon)

### Managed backups (recommended)

- Enable Neon **Point-in-Time Recovery (PITR)** / branching in the Neon console
- Keep a secondary branch or snapshot for major releases
- Retention: follow business RPO (recommend ≥ 7 days PITR)

### Logical dump (portable)

```bash
# From a trusted operator workstation (never bake credentials into images)
pg_dump "$DATABASE_URL_SYNC" --format=custom --file="prime_$(date +%Y%m%d_%H%M).dump"

# Restore into a new database / branch
pg_restore --clean --if-exists --dbname="$TARGET_DATABASE_URL" prime_YYYYMMDD_HHMM.dump
```

Use the sync URL form (`postgresql+psycopg://` or Neon console “psql” string).

### Migration strategy

1. Always forward-only in production: `alembic upgrade head`
2. Keep migrations idempotent and reviewed
3. Take a Neon branch/snapshot **before** risky migrations
4. Rollback application first if needed; DB downgrades are last resort (`alembic downgrade`)

---

## Redis

Redis holds **ephemeral** data:

- OTP sessions & rate counters
- JWT refresh tokens / blacklist
- HTTP rate-limit windows
- Catalog / cart / order / dashboard caches
- Maintenance / commerce config cache
- Checkout locks / idempotency keys

**Do not** treat Redis as a system of record. On total Redis loss:

1. Users re-authenticate (OTP)
2. Caches rebuild on next read
3. In-flight checkout locks expire via TTL
4. Rate-limit budgets reset (auth policies fail closed until Redis returns)

Optional: enable AOF/RDB on self-hosted Redis for softer restarts (compose local Redis uses AOF). Managed Redis (Upstash) handles durability per plan.

---

## Cloudinary assets

- Media is the source of truth in Cloudinary (avatars, product images)
- Enable Cloudinary backup / versioning in the Cloudinary console
- Store `public_id` + secure URL in PostgreSQL; DB restore alone does not restore binary assets
- Disaster recovery: restore DB rows + ensure Cloudinary account assets remain; re-upload only if assets were deleted

---

## Application config & secrets

| Asset | Backup |
|-------|--------|
| `.env` / secrets | Password manager / cloud secrets (AWS SM, Doppler, Render/Railway secrets) |
| Alembic revisions | Git |
| `data/users.json` mirror | Derived from DB; not primary — recreate on login if lost |
| Log files | Ship to centralized logging; local `logs/` rotates 30d (app) / 90d (security) |

---

## Disaster recovery runbook

| Scenario | RTO guidance | Actions |
|----------|--------------|---------|
| API crash | Minutes | Restart container / platform service; health checks recover |
| Redis outage | Minutes–hours | Restore Redis; auth/upload/orders rate limits fail closed until back |
| Neon outage | Hours | Fail over Neon branch/region or restore snapshot; re-point `DATABASE_URL` |
| Region loss | Hours–day | Redeploy API near new DB; update DNS; validate `/health/services` |
| Ransomware / wipe | Day | Restore Neon PITR + Cloudinary + redeploy from Git tag |

### Recovery verification

```text
GET /health
GET /health/database
GET /health/redis
GET /health/services
POST /api/v1/auth/send-otp   (test phone)
Browse catalog → cart → place order → owner email
```

---

## RPO / RTO targets (defaults)

| Component | RPO | RTO |
|-----------|-----|-----|
| PostgreSQL | ≤ 5–15 min (Neon PITR) | ≤ 1 hour |
| Redis | Acceptable loss (ephemeral) | ≤ 15 min |
| Cloudinary | Provider SLA | Provider restore |
| App binaries | Git immortal | ≤ 30 min redeploy |
