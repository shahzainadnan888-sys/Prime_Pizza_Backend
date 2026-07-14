# Deployment Guide — Prime Pizza API

This guide covers deploying the FastAPI backend to common platforms. The database of record in production is **Neon PostgreSQL**. Cache/sessions use **managed Redis** (e.g. Upstash).

---

## Pre-flight (all platforms)

1. Create Neon project → copy connection string → set `DATABASE_URL`
2. Create Upstash (or Redis Cloud) → `REDIS_URL` with TLS (`rediss://`)
3. Configure Twilio Verify, Cloudinary, Resend
4. Generate `SECRET_KEY` (≥48 random bytes for production)
5. Set `APP_ENV=production`, `DEBUG=false`, HTTPS `FRONTEND_URL`, explicit `ALLOWED_HOSTS`
6. Run migrations: `alembic upgrade head`
7. Verify: `GET /health`, `GET /health/database`, `GET /health/redis`, `GET /health/services`

Validate locally:

```bash
python scripts/validate_env.py
```

---

## Build & start commands

| Step | Command |
|------|---------|
| Install | `uv sync --no-dev` or `pip install .` |
| Migrate | `alembic upgrade head` |
| Start | `uvicorn app.main:app --host 0.0.0.0 --port $PORT --proxy-headers` |
| Health | `GET /health` (liveness), `/health/services` (readiness) |

Docker:

```bash
docker build -t prime-pizza-api .
docker run --env-file .env -p 8000:8000 prime-pizza-api
```

Compose (dev):

```bash
docker compose up --build
```

---

## Environment variables (production)

Set at least:

```
APP_ENV=production
DEBUG=false
SECRET_KEY=<48+ chars>
OWNER_PHONE_NUMBER=+92…
OWNER_EMAIL=owner@domain.com
DATABASE_URL=postgresql://…?sslmode=require
REDIS_URL=rediss://…
TWILIO_ACCOUNT_SID=AC…
TWILIO_AUTH_TOKEN=…
TWILIO_VERIFY_SERVICE_SID=VA…   # or TWILIO_SERVICE_ID
CLOUDINARY_CLOUD_NAME=…
CLOUDINARY_API_KEY=…
CLOUDINARY_API_SECRET=…
RESEND_API_KEY=re_…
RESEND_FROM_EMAIL=noreply@yourdomain.com
FRONTEND_URL=https://your-frontend
ALLOWED_HOSTS=["api.yourdomain.com"]
ENABLE_HSTS=true
TRUST_X_FORWARDED_FOR=true
TRUSTED_PROXY_IPS=["<load-balancer>"]
ENABLE_DOCS=false
```

---

## Render

1. New **Web Service** → connect repo
2. Runtime: Docker **or** Native
   - **Docker:** Dockerfile path `./Dockerfile`
   - **Native:** Build `pip install .` / Start `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. Add env vars from the table above
4. Add **one-off** migrate job / release command: `alembic upgrade head`
5. Health check path: `/health`
6. Point custom domain; enable HTTPS

Neon + Upstash remain external services (recommended).

---

## Railway

1. New project → Deploy from GitHub
2. Add variables (paste `.env` carefully; never commit)
3. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Pre-deploy / release: `alembic upgrade head`
5. Optional: use Railway Redis **or** keep Upstash
6. Prefer Neon for Postgres rather than Railway Postgres if already provisioned

---

## DigitalOcean App Platform

1. Create App from GitHub
2. Component type: **Web Service**
3. Dockerfile build **or** Python buildpack
4. HTTP port `8000` (or `$PORT`)
5. Health check `/health`
6. Run migrate as a job component:
   ```
   alembic upgrade head
   ```
7. Attach custom domain + SSL

---

## AWS EC2 / self-hosted VPS

### Server prep

```bash
sudo apt update && sudo apt install -y docker.io docker-compose-v2 nginx certbot
sudo usermod -aG docker $USER
```

### Run container

```bash
git clone <repo> && cd prime_pizza3.0_backend
cp .env.example .env   # fill production values
docker build -t prime-pizza-api .
docker run -d --name prime-api --restart unless-stopped \
  --env-file .env -p 127.0.0.1:8000:8000 prime-pizza-api
```

### Migrate once

```bash
docker run --rm --env-file .env prime-pizza-api alembic upgrade head
```

### Nginx reverse proxy (TLS)

```nginx
server {
  listen 443 ssl http2;
  server_name api.yourdomain.com;
  # ssl_certificate …;

  location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Request-ID $request_id;
  }
}
```

Set `TRUST_X_FORWARDED_FOR=true` and `TRUSTED_PROXY_IPS` to your Nginx/VPC peer IPs.

---

## Docker-only (any cloud)

```bash
docker build -t ghcr.io/you/prime-pizza-api:1.0.0 .
docker push ghcr.io/you/prime-pizza-api:1.0.0
# Pull & run with env injection from secrets manager
```

Use orchestrator health checks against `/health` and readiness against `/health/services` (or `/health/database` + `/health/redis`).

---

## Database setup (Neon)

1. Create Neon project (region near API)
2. Copy pooled connection string
3. App auto-normalizes to `postgresql+asyncpg://` and remaps `sslmode`
4. `alembic upgrade head`
5. Enable PITR / scheduled backups in Neon console

---

## Redis setup

- Upstash: create DB, copy `rediss://` URL
- Or ElastiCache / Redis Cloud with TLS
- Do not expose Redis publicly without ACLs

---

## Cloudinary / Twilio / Resend

| Provider | Steps |
|----------|-------|
| Cloudinary | Create cloud → API key/secret → folder `prime_pizza/` used by uploads |
| Twilio | Verify Service → SID → phone sender geo permissions |
| Resend | Verify domain → API key → set `RESEND_FROM_EMAIL` |

Test email: owner `POST /api/v1/admin/test-email` with Bearer token.

---

## CI/CD preparation

Suggested GitHub Actions jobs (not required to exist yet):

1. **lint** — `ruff check app tests`
2. **test** — `pytest` with `APP_ENV=test`
3. **build** — `docker build`
4. **migrate** — run on release against Neon (use secrets)
5. **deploy** — platform-specific

Keep `SECRET_KEY`, Twilio, Cloudinary, Resend in **secret stores**, never in repo.

---

## Post-deploy checklist

- [ ] `/health` → 200
- [ ] `/health/database` → 200
- [ ] `/health/redis` → 200
- [ ] `/health/services` → 200 or degraded only for optional email
- [ ] Send OTP → verify → place test order → owner email arrives
- [ ] OpenAPI not public (`/docs` 404)
- [ ] Security headers present
- [ ] Rate limit headers on responses
