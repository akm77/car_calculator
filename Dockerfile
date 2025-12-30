# syntax=docker/dockerfile:1.6

# =============================================================================
# Builder Stage: Export Poetry dependencies to requirements.txt
# =============================================================================
FROM python:3.13-slim AS builder

# Build arguments with defaults
ARG POETRY_VERSION=1.8.3

# Python environment optimization
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install minimal system dependencies for build stage
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
ENV POETRY_HOME=/opt/poetry \
    POETRY_VERSION=${POETRY_VERSION}
RUN pip install --no-cache-dir "poetry==${POETRY_VERSION}"

WORKDIR /app

# Copy only manifest files for better layer caching
COPY pyproject.toml poetry.lock ./

# Export runtime requirements (without dev deps, without hashes for better compatibility)
RUN poetry export -f requirements.txt --output /tmp/requirements.txt --without-hashes --without dev

# =============================================================================
# Runtime Stage: Final production image
# =============================================================================
FROM python:3.13-slim AS runtime

# Build arguments for runtime configuration (can be overridden at build time)
ARG API_HOST=0.0.0.0
ARG API_PORT=8000
ARG LOG_LEVEL=info
ARG ENABLE_LIVE_CBR=false
ARG CBR_CACHE_TTL_SECONDS=1800
ARG RATE_LIMIT_PER_MINUTE=60

# Python environment optimization
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install minimal OS dependencies (curl for healthcheck, tini for signal handling)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    tini \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY --from=builder /tmp/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt

# Copy application code
COPY app ./app
# COPY config ./config
COPY tests /tests
COPY README.md ./README.md

# Copy and make supervisor script executable
COPY scripts/run.sh /app/run.sh
RUN chmod +x /app/run.sh

# =============================================================================
# Environment Variables with Defaults
# =============================================================================

# Network Configuration
ENV API_HOST=${API_HOST} \
    API_PORT=${API_PORT}

# Logging
ENV LOG_LEVEL=${LOG_LEVEL}

# External Services
ENV ENABLE_LIVE_CBR=${ENABLE_LIVE_CBR} \
    CBR_CACHE_TTL_SECONDS=${CBR_CACHE_TTL_SECONDS} \
    CBR_URL=https://www.cbr.ru/scripts/XML_daily.asp

# Rate Limiting
ENV RATE_LIMIT_PER_MINUTE=${RATE_LIMIT_PER_MINUTE}

# Application URL (will be overridden by docker-compose or runtime)
ENV PUBLIC_BASE_URL=http://localhost:${API_PORT}

# Runtime mode (both, api, bot) - set via docker-compose command
ENV RUN_MODE=both

# Environment type (dev, prod) - affects .env file selection
ENV ENVIRONMENT=prod

# Telegram Bot Configuration (must be set at runtime)
# BOT_TOKEN - Telegram bot token from @BotFather (REQUIRED for bot mode)
ENV BOT_TOKEN=${BOT_TOKEN}
# ADMIN_USER_IDS - Comma-separated list of admin Telegram user IDs (OPTIONAL but recommended)
# Example: ADMIN_USER_IDS=123456789,987654321
ENV ADMIN_USER_IDS=${ADMIN_USER_IDS}
# Optional Configuration
# AVAILABLE_COUNTRIES - Comma-separated list of allowed countries (optional filter)
# Example: AVAILABLE_COUNTRIES=japan,korea,uae,china,georgia
ENV AVAILABLE_COUNTRIES=${AVAILABLE_COUNTRIES}

# =============================================================================
# Container Configuration
# =============================================================================

# Expose API port
EXPOSE ${API_PORT}

# Health check using /ping endpoint
HEALTHCHECK --interval=30s --timeout=5s --retries=3 --start-period=40s \
    CMD curl -fsS http://127.0.0.1:${API_PORT}/ping || exit 1

# Create directories for volumes (config and logs)
#RUN mkdir -p /app/logs
#RUN mkdir -p /app/config

# Use tini as PID 1 for proper signal handling and run supervisor script
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/app/run.sh"]

# =============================================================================
# Labels for documentation and metadata
# =============================================================================
LABEL maintainer="Car Calculator Project" \
      description="FastAPI + Telegram Bot for car import cost calculation" \
      version="2.1.0" \
      org.opencontainers.image.source="https://github.com/your-org/car-calculator" \
      org.opencontainers.image.documentation="https://github.com/your-org/car-calculator/blob/main/README.md"

