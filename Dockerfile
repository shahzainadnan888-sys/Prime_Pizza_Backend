# syntax=docker/dockerfile:1.7

# --------------------------------------------------
# Stage 1: dependency builder (layer-cached)
# --------------------------------------------------
FROM python:3.13-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /build

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && curl -LsSf https://astral.sh/uv/install.sh | sh

ENV PATH="/root/.local/bin:${PATH}"

# Install dependencies first (better cache) without the project sources.
COPY pyproject.toml uv.lock README.md ./
RUN mkdir -p app && printf '"""Prime Pizza API package."""\n__version__ = "1.0.0"\n' > app/__init__.py \
    && uv sync --frozen --no-dev --no-editable

# Copy full sources and re-sync to install the project package.
COPY app ./app
COPY main.py ./
RUN uv sync --frozen --no-dev --no-editable

# --------------------------------------------------
# Stage 2: production runtime (non-root)
# --------------------------------------------------
FROM python:3.13-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:${PATH}" \
    APP_HOME=/app \
    HOST=0.0.0.0 \
    PORT=8000

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system --gid 10001 appuser \
    && useradd --system --uid 10001 --gid appuser --home-dir /app --shell /usr/sbin/nologin appuser \
    && mkdir -p /app/logs /app/data \
    && chown -R appuser:appuser /app

COPY --from=builder --chown=appuser:appuser /build/.venv /app/.venv
COPY --chown=appuser:appuser app ./app
COPY --chown=appuser:appuser main.py alembic.ini ./
COPY --chown=appuser:appuser alembic ./alembic
COPY --chown=appuser:appuser scripts ./scripts

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD curl -fsS "http://127.0.0.1:${PORT}/health" || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host ${HOST} --port ${PORT} --proxy-headers --forwarded-allow-ips='*'"]
