# syntax=docker/dockerfile:1.6

# ---------- Builder: export Poetry deps to requirements ----------
FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System deps for build and curl for healthcheck in final stage copy
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VERSION=1.8.3
RUN pip install --no-cache-dir "poetry==${POETRY_VERSION}"

WORKDIR /app

# Only copy manifest files for better layer caching
COPY pyproject.toml poetry.lock ./

# Export runtime requirements (without dev deps)
RUN poetry export -f requirements.txt --output /tmp/requirements.txt --without-hashes

# ---------- Runtime image ----------
FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install minimal OS deps (include tini for signal handling)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    tini \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps
COPY --from=builder /tmp/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy application code
COPY app ./app
COPY config ./config
COPY README.md ./README.md

# Copy supervisor script
COPY scripts/run.sh /app/run.sh
RUN chmod +x /app/run.sh

# Environment
ENV API_HOST=0.0.0.0 \
    API_PORT=8000 \
    ENABLE_LIVE_CBR=false \
    LOG_LEVEL=info \
    PUBLIC_BASE_URL=http://localhost:8000 \
    RUN_MODE=both

EXPOSE 8000

# Healthcheck (uses /ping)
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -fsS http://127.0.0.1:8000/ping || exit 1

# Use tini as PID 1 and run supervisor script
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/app/run.sh"]
