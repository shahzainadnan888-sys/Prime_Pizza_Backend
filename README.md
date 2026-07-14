# Prime Pizza API Backend

Production-grade FastAPI backend for the **Prime Pizza** restaurant platform — authentication, catalog, cart, checkout, orders, owner dashboard, email notifications, Redis caching, and enterprise hardening.

---

## Features

- Phone OTP authentication via **local Redis OTP** (pluggable provider architecture)
- JWT access + rotating refresh tokens (Redis-backed blacklist / consume-once)
- Role-based access control (customer / owner)
- Catalog, deals, search, Cloudinary image uploads
- Cart, wishlist, coupons, checkout validation
- Order placement, tracking, owner status/payment management
- Owner dashboard, analytics, charts, customers, audit logs
- Resend transactional email (new-order + owner test)
- Redis caching, rate limiting, maintenance mode
- Structured logging, health probes, security headers
- Docker / Compose ready; Neon PostgreSQL + managed Redis for production

---

## Architecture

```
Client (Web / Mobile)
        │
        ▼
 FastAPI (uvicorn) ── Middleware (security, rate limit, request ID, …)
        │
        ├── Services ── Repositories ── PostgreSQL (Neon)
        │                     │
        │                     └── Redis (cache, OTP, rate limits, sessions)
        ├── Local OTP (Redis) / future SMS providers
        ├── Cloudinary
        └── Resend
```

Layering: **Router → Dependencies → Service → Repository → Model**.  
See `docs/architecture.md` and `docs/production-hardening.md`.

---

## Tech stack

| Layer | Technology |
|-------|------------|
| API | FastAPI, Pydantic v2, Uvicorn |
| DB | PostgreSQL (Neon), SQLAlchemy 2.0 async, Alembic |
| Cache | Redis (Upstash or local) |
| Auth | Local Redis OTP, python-jose JWT, bcrypt |
| Media | Cloudinary |
| Email | Resend |
| Logging | Loguru (JSON + rotation) |
| Packaging | `uv` / hatchling, Python 3.13+ |

---

## Installation

```bash
# Clone
cd prime_pizza3.0_backend

# Create venv & install (recommended: uv)
uv sync --extra dev

# Or pip
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux
pip install -e ".[dev]"
```

---

## Environment variables

```bash
cp .env.example .env
# Edit secrets — never commit .env
python scripts/validate_env.py
```

### Required

| Variable | Purpose |
|----------|---------|
| `SECRET_KEY` | JWT signing (≥32 chars; ≥48 in production) |
| `OWNER_PHONE_NUMBER` | E.164 owner phone (maps to owner role) |
| `OWNER_EMAIL` | Owner notification recipient |
| `DATABASE_URL` | Neon / Postgres URL |
| `REDIS_URL` | Redis URL (`rediss://` in production) |
| `OTP_EXPIRE_SECONDS` | OTP TTL (alias `OTP_EXPIRY_SECONDS`) |
| `OTP_MAX_ATTEMPTS` | Max verify attempts per challenge |
| `CLOUDINARY_CLOUD_NAME` / `API_KEY` / `API_SECRET` | Image CDN |
| `APP_ENV` | `development` \| `staging` \| `production` \| `test` |
| `FRONTEND_URL` | CORS origin (HTTPS in production) |

### Strongly recommended

`RESEND_API_KEY`, `RESEND_FROM_EMAIL`, `ALLOWED_HOSTS`, `DEBUG=false` (production).

Full list: `.env.example`.

---

## Running locally

```bash
# Apply migrations (Neon or local Postgres)
alembic upgrade head

# Start API
uv run python main.py
# or
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs` (disabled when `APP_ENV=production`)
- ReDoc: `http://localhost:8000/redoc`
- Frontend contract: [`api.md`](./api.md)

---

## Database migrations

```bash
alembic upgrade head
alembic revision --autogenerate -m "describe change"
alembic downgrade -1
```

Production: run migrations as a **release job** before/during deploy (see `DEPLOYMENT.md`).

---

## Docker

```bash
# API + Redis (uses DATABASE_URL from .env — typically Neon)
docker compose up --build

# Optional local Postgres + Adminer + migrate
docker compose --profile local-db --profile tools --profile migrate up --build
```

Image traits: multi-stage build, non-root user `appuser`, healthcheck on `/health`, no secrets in layers.

---

## Redis

Used for: OTP sessions & limits, JWT refresh/blacklist, HTTP rate limits, catalog/cart/order/dashboard caches, commerce/maintenance flags, checkout locks.

Production: Upstash (`rediss://`) or equivalent managed Redis.

---

## Cloudinary / Resend

| Provider | Used for |
|----------|----------|
| Cloudinary | Avatars & product images (`resource_type=image`) |
| Resend | Owner new-order email + admin test email |
| Local OTP | Phone login codes via Redis (no SMS vendor) |

Configure via env; readiness reflected on `GET /health/services`.

---

## Testing

```bash
uv run pytest
uv run pytest -q --cov=app
uv run ruff check app tests
```

---

## Deployment

See **[DEPLOYMENT.md](./DEPLOYMENT.md)** for Render, Railway, DigitalOcean, AWS EC2, Docker, and VPS.

Backup / DR: **[docs/BACKUP.md](./docs/BACKUP.md)**  
Production readiness: **[docs/PRODUCTION_READINESS.md](./docs/PRODUCTION_READINESS.md)**

---

## Folder structure

```
app/
  api/v1/endpoints/   # HTTP routes
  authorization/      # RBAC + ownership
  config/             # Settings
  core/               # Logging, exceptions, lifespan
  database/           # Engine, session, mixins
  dependencies/       # FastAPI DI
  emails/             # Templates + sanitizers
  integrations/       # Redis, Cloudinary, Resend
  middleware/         # Security, rate limit, … 
  models/             # SQLAlchemy models
  monitoring/         # In-process metrics
  repositories/       # Data access
  schemas/            # Pydantic I/O
  security/           # JWT helpers
  services/           # Business logic
  utils/
alembic/              # Migrations
tests/
scripts/              # validate_env, generate_api_md
docs/
Dockerfile
docker-compose.yml
api.md                # Frontend API contract
```

---

## Troubleshooting

| Symptom | Check |
|---------|--------|
| App won't start | `python scripts/validate_env.py`; `SECRET_KEY` length; prod validators |
| Redis timeout | URL TLS (`rediss://`); firewall; Upstash region |
| DB errors | `ssl=require` / Neon pooler; run `alembic upgrade head` |
| CORS failures | `FRONTEND_URL` exact match; `ALLOWED_HOSTS` |
| 429 responses | Rate limits / OTP budgets; wait `Retry-After` |
| Docs missing | Not exposed when `APP_ENV=production` |
| OTP failures | Check Redis; read Development OTP banner in server terminal |

---

## License

Proprietary — Prime Pizza Engineering.
