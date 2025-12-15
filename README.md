# Car Import Cost Calculator

Telegram Bot + FastAPI backend + WebApp for calculating the total import cost of cars from Japan, Korea, UAE, and China.

## Features
- Full calculation engine per current tariff tables:
  - Duties: <3 years (percent with min €/cc), 3–5 years and >5 years (€/cc bands)
  - Country expenses and freight per country (Yen/USD, etc.)
  - Utilization fee, customs services, company commission
  - ERA-GLONASS excluded from totals (deprecated)
- Currency handling:
  - Static rates in config + optional live rates via CBR
  - Response meta contains rates_used with all applied rates; logs include purchase_rate_rub
  - Clients (WebApp и Telegram‑бот) показывают использованный валютный курс
    из meta.detailed_rates_used (например, `USD/RUB = 78.95 + 1%`), так что
    итоговая сумма на экране уже учитывает настроенную банковскую надбавку.
- WebApp (served from the API at /web/) for quick calculations
- Telegram Bot (aiogram v3) with /start and WebApp launch
- REST API endpoints:
  - GET /api/health
  - GET /api/rates — numeric tariff data for frontend
  - GET /api/meta — metadata (countries, freight types, constraints)
  - POST /api/calculate — performs calculation and returns breakdown + meta
  - POST /api/rates/refresh — forces live CBR refresh (if enabled)

## Tech Stack
- Python 3.13, FastAPI, Uvicorn
- Pydantic v2, pydantic-settings
- aiogram 3
- httpx, tenacity
- PyYAML
- structlog
- Ruff, mypy, pytest

## Project Structure
```
app/
  main.py              # FastAPI app
  struct_logger.py
  api/routes.py
  calculation/
    engine.py          # main engine (duty, fees, currency)
    models.py          # request/response schemas
    tariff_tables.py   # helpers for duties
    rounding.py
  bot/
    main.py            # bot runner
    handlers/
    keyboards.py
  core/
    settings.py
  services/
    cbr.py             # CBR live rates service (optional)
  webapp/
    index.html, assets, manifest.json, sw.js
config/
  fees.yml, commissions.yml, rates.yml, duties.yml
nginx/
  Dockerfile, entrypoint.sh, conf.d/*.template
Dockerfile, docker-compose.yml
tests/ (unit + functional)
docs/ (formulas, RPG methodology, webapp refactoring plan)
```

## 📚 Documentation
- **WebApp Refactoring Plan**: See `docs/README_WEBAPP_REFACTORING.md` for the modular architecture refactoring plan (10 stages, 22-35h)
- **RPG Methodology**: See `docs/rpg_intro.txt` for the Repository Planning Graph approach used in this project
- **Project Graph**: See `docs/rpg.yaml` for the complete dependency graph and architecture overview
```

## Quick Start (local, Poetry)
1) Install deps
```bash
poetry install
```
2) Create env file (see below)
```bash
cp .env.example .env
```
3) Run API
```bash
poetry run car-calculator-api
```
4) Open WebApp
- http://localhost:8000/web/

5) (Optional) Run Bot
```bash
poetry run car-calculator-bot
```

## API
- GET /api/health → status and rates info
- GET /api/rates → currencies, duties bands, commissions, customs services, Japan tiers
- GET /api/meta → reference metadata for frontend
- POST /api/calculate → calculation result with breakdown and meta
  - meta includes: duty mode and details, passing/non‑passing, rates_used (e.g. {"JPY_RUB":0.6,"EUR_RUB":100})

## Environment Variables (.env)
```ini
# Network
API_HOST=0.0.0.0
API_PORT=8000
PUBLIC_BASE_URL=http://localhost:8000
LOG_LEVEL=info
# Live CBR (optional in prod only)
ENABLE_LIVE_CBR=false
CBR_CACHE_TTL_SECONDS=1800
CBR_URL=https://www.cbr.ru/scripts/XML_daily.asp
# Access & limits
RATE_LIMIT_PER_MINUTE=60
AVAILABLE_COUNTRIES=
# Telegram bot (optional)
BOT_TOKEN=
# ENV switch: ENVIRONMENT=prod|dev (affects .env vs .env.dev)
ENVIRONMENT=dev
```

---

## Run with Docker (HTTP → HTTPS)
WebApp in Telegram requires HTTPS. The repo includes a reverse proxy (Nginx) and Certbot automation for Let’s Encrypt.

Prerequisites
- A domain pointing to your server (A/AAAA DNS record)
- TCP ports 80 and 443 open

1) Set domain and prepare volumes
```bash
echo "DOMAIN=your.domain.com" > .env
mkdir -p data/certbot/www data/certbot/conf
```

2) Build and start API + Nginx (HTTP first)
```bash
docker compose build
docker compose up -d api nginx
```
- Check: http://your.domain.com/ping → {"status":"ok"}

3) Obtain the initial certificate (webroot challenge)
```bash
docker compose run --rm certbot certonly \
  --webroot -w /var/www/certbot \
  -d "$DOMAIN" \
  --email you@example.com --agree-tos --no-eff-email
```
- Certs are saved to ./data/certbot/conf/live/$DOMAIN/

4) Switch Nginx to HTTPS
```bash
docker compose restart nginx
```
- Now browse: https://your.domain.com/web/
- The certbot service will auto‑renew twice daily and reuse the same volumes

5) Full stack
```bash
docker compose up -d
# logs
docker compose logs -f api nginx certbot
# stop
docker compose down
```

Tips
- If you’re behind a CDN (e.g., Cloudflare), set DNS Only during issuance or use a DNS challenge method
- To enable live CBR in production, set ENABLE_LIVE_CBR=true (don’t enable in tests)
- PUBLIC_BASE_URL should be https://your.domain.com in production (compose sets it to https://${DOMAIN})

---

## Run Telegram Bot with Docker
The bot runs as a separate service (long‑polling). Set BOT_TOKEN in your environment.

1) Set env
```bash
echo "BOT_TOKEN=123456:ABC-DEF..." >> .env
# DOMAIN should already be set for PUBLIC_BASE_URL used in menus
```

2) Start only the bot (API must be reachable)
```bash
docker compose up -d bot
```

3) Start full stack (API, bot, Nginx, Certbot)
```bash
docker compose up -d
```

4) Logs & lifecycle
```bash
docker compose logs -f bot
# stop bot only
docker compose stop bot
# restart bot only
docker compose restart bot
```

Notes
- The bot uses long polling and does not require public HTTPS itself
- For WebApp links in chat, PUBLIC_BASE_URL should be an HTTPS URL (Nginx + Certbot)
- Keep ENABLE_LIVE_CBR=false for the bot; live rates are used by the API

---

## Development & QA
Run tests
```bash
poetry run pytest
```
Lint & format
```bash
poetry run ruff check .
poetry run ruff format .
```
Type check
```bash
poetry run mypy app
```

## License
Proprietary / Internal use.
