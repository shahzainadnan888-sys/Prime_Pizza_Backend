# Prime Pizza Backend — Foundation Architecture

This document describes the Phase-1 backend foundation only.
Business domains (auth, catalog, orders, etc.) are intentionally deferred.

## Layers

1. **API** (`app/api`) — HTTP adapters, versioned routers, health probes
2. **Dependencies** (`app/dependencies`) — FastAPI DI providers
3. **Services** (`app/services`) — application use-case layer (prepared)
4. **Repositories** (`app/repositories`) — persistence adapters (prepared)
5. **Models / Schemas** — ORM + Pydantic contracts
6. **Integrations** — Redis, Twilio, Cloudinary, Resend clients
7. **Core / Config** — settings, logging, exceptions, lifespan

## Startup flow

`main.py` → `uvicorn app.main:app` → `create_app()` → lifespan
(`init_db`, `init_redis`, third-party clients) → request pipeline → shutdown.

## Response contract

All endpoints return the shared envelope in `app/schemas/response.py`.
