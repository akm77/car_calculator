# Car Import Cost Calculator

Telegram Bot + FastAPI backend + WebApp for calculating the total import cost of cars from Japan, Korea, UAE, and China.

## Features

- **🎛️ Config Management System**: Complete Telegram-based configuration management (NEW in v2.1.0)
  - **Download configs**: `/get_fees`, `/get_commissions`, `/get_rates`, `/get_duties`
  - **Upload with validation**: `/set_fees`, `/set_commissions`, `/set_rates`, `/set_duties`
  - **Hot reload (zero downtime)**: `/reload_configs` - apply changes without restart
  - **Monitoring**: `/config_status`, `/config_diff` - version tracking and sync check
  - **Access control**: Admin-only via `ADMIN_USER_IDS` whitelist
  - **4-level validation**: filename, size (≤1MB), YAML syntax, structure
  - **Automatic backups**: Timestamped backups before each update
  - **Config versioning**: Hash + timestamp for each load
  - **Audit logging**: All admin actions + unauthorized attempts
  - **Error recovery**: Graceful degradation, old configs retained on failure
  - 📖 **[Admin Guide](docs/CONFIG_ADMIN_GUIDE.md)** | 📖 **[Incident Playbook](docs/CONFIG_INCIDENT_PLAYBOOK.md)**
  
- Full calculation engine per current tariff tables:
  - Duties: <3 years (percent with min €/cc), 3–5 years and >5 years (€/cc bands)
  - Country expenses and freight per country (Yen/USD, etc.)
  - Utilization fee, customs services, company commission
  - ERA-GLONASS excluded from totals (deprecated)
- Commission model:
  - Fixed company commission in USD (1000 USD for most countries, 0 USD for UAE, configurable in `config/commissions.yml`)
  - Optional **bank_commission** as a percentage surcharge to FX rates (configured in `config/commissions.yml::bank_commission`); it affects only currency-based components and is reflected in `meta.detailed_rates_used.display` (e.g. `USD/RUB = 78.95 + 1%`).
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
- **Config Management**:
  - 📖 **[Admin Guide](docs/CONFIG_ADMIN_GUIDE.md)** - Complete user guide for config management
  - 📖 **[Incident Playbook](docs/CONFIG_INCIDENT_PLAYBOOK.md)** - Troubleshooting and recovery procedures
  - 📖 **[Technical Overview](docs/CONFIG_MANAGEMENT.md)** - Architecture and workflows
- **WebApp Refactoring Plan**: See `docs/README_WEBAPP_REFACTORING.md` for the modular architecture refactoring plan (10 stages, 22-35h)
- **RPG Methodology**: See `docs/rpg_intro.txt` for the Repository Planning Graph approach used in this project
- **Project Graph**: See `docs/rpg.yaml` for the complete dependency graph and architecture overview

## 🎛️ Configuration Management (Quick Start for Admins)

Manage configuration files through Telegram bot commands - **no SSH access or server restart required!**

### Setup Admin Access

1. **Get your user ID:**
   ```
   Telegram: /whoami
   Bot: 👤 Your user ID: 123456789
   ```

2. **Add to admin list:**
   ```bash
   # Edit .env file
   ADMIN_USER_IDS=123456789,987654321
   
   # Restart bot
   docker-compose restart bot
   ```

### Managing Configs

```
# List available configs
/list_configs

# Download a config
/get_fees            # Country fees and freight
/get_commissions     # Company and bank commissions
/get_rates           # Exchange rates and utilization
/get_duties          # Duty calculation tables

# Upload new config (with validation)
/set_fees            # Then send the edited file
/set_commissions
/set_rates
/set_duties

# Apply changes (hot reload - zero downtime!)
/reload_configs

# Monitor status
/config_status       # Check current version and hash
/config_diff         # Check if memory and disk are in sync
```

### Typical Workflow

```
1. /get_fees         → Download current config
2. Edit locally      → Make your changes
3. Validate YAML     → Use online validator
4. /set_fees         → Upload new version
5. [Send file]       → Bot validates and saves
6. /reload_configs   → Apply changes (instant!)
7. /config_status    → Verify new version
```

### Features

- ✅ **Hot reload** - zero downtime, no restart needed
- ✅ **Automatic backups** - timestamped backups before each update
- ✅ **YAML validation** - 4-level validation (filename, size, syntax, structure)
- ✅ **Access control** - admin-only, whitelist-based
- ✅ **Audit logging** - all actions logged with user info
- ✅ **Config versioning** - hash + timestamp tracking
- ✅ **Error recovery** - old configs retained on failure

📖 **Full documentation:** [CONFIG_ADMIN_GUIDE.md](docs/CONFIG_ADMIN_GUIDE.md)
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

## Testing

### Running Tests

```bash
# All tests (excluding manual)
pytest tests/ -v --ignore=tests/manual

# Only unit tests
pytest tests/unit/ -v

# Only functional/integration tests
pytest tests/functional/ -v

# With coverage report (HTML)
pytest tests/ --cov=app --cov-report=html --ignore=tests/manual
open htmlcov/index.html

# With coverage report (terminal)
pytest tests/ --cov=app --cov-report=term --ignore=tests/manual

# Specific test file
pytest tests/unit/test_models_validation.py -v

# Stop on first failure
pytest tests/ -x --ignore=tests/manual
```

### Test Structure

- **tests/unit/** — Unit tests (isolated, no external dependencies)
  - `test_models_*.py` — Pydantic models validation (148 tests)
  - `test_rounding.py` — Rounding functions (69 tests)
  - `test_tariff_tables.py` — Duty rates & age categories (117 tests)
  - `test_engine_*.py` — Calculation engine helpers & integration (143 tests)
  - `test_bank_commission.py` — Bank commission logic (9 tests)
  - `test_utilization_v2.py` — Utilization fee 2025 (19 tests)

- **tests/functional/** — Functional/integration tests
  - `test_api.py` — REST API endpoints (40 tests)
  - `test_api_validation.py` — Input validation & HTTP 422 (51 tests)
  - `test_api_bank_commission.py` — Bank commission via API (3 tests)
  - `test_engine.py` — Parametrized tests from cases.yml (46 tests)
  - `test_cbr.py` — CBR service integration (2 tests)

- **tests/test_data/** — Test data
  - `cases.yml` — 46 parametrized test scenarios (all countries, age categories, boundaries)
  - `config/` — Test configurations (rates, duties, commissions, fees)

- **tests/manual/** — Manual tests (not run automatically)
  - Browser-based tests for WebApp components
  - Bot handler tests (require Telegram Bot API)

### Test Coverage

**Current coverage: 91%**

Detailed coverage by module:
- `app/calculation/models.py`: **100%**
- `app/calculation/tariff_tables.py`: **100%**
- `app/api/routes.py`: **99%**
- `app/calculation/rounding.py`: **95%**
- `app/calculation/engine.py`: **94%**
- `app/core/settings.py`: **93%**
- `app/services/cbr.py`: **85%**

**Test statistics**:
- Total: 619 tests (618 passed, 1 skipped)
- Unit tests: 477
- Functional tests: 142

### Documentation

- **Full test report**: `docs/sprints/TEST_FINAL_REPORT.md`
- **Maintenance checklist**: `docs/sprints/TEST_MAINTENANCE_CHECKLIST.md`
- **Coverage by SPECIFICATION.md**: See TEST_FINAL_REPORT.md § 3

### Maintenance

When making changes, follow the checklist in `docs/sprints/TEST_MAINTENANCE_CHECKLIST.md`:
- Changing SPECIFICATION.md → update corresponding tests
- Adding new fields → add validation tests in `test_models_validation.py`
- Changing calculation logic → update `test_engine_helpers.py` and `cases.yml`
- Adding new country → add tests and 3 cases (lt3, 3_5, gt5)

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

## Config Management Commands (Admin only)

The Telegram bot provides admin-only commands for managing configuration files:

### View Available Configs
```bash
/list_configs  # Show all configuration files with status (✅/❌)
```

### Download Configuration Files
```bash
/get_fees          # Download config/fees.yml (тарифы стран и фрахта)
/get_commissions   # Download config/commissions.yml (комиссии)
/get_rates         # Download config/rates.yml (курсы валют и утильсбор)
/get_duties        # Download config/duties.yml (таблицы пошлин)
```

Each downloaded file includes:
- 📄 Filename
- 📝 Description
- 📊 File size
- ✅ Status indicator (file exists/missing)

### Upload Configuration Files (Coming in CONFIG-03)
```bash
/set_fees          # Upload new fees.yml (with validation)
/set_commissions   # Upload new commissions.yml (with validation)
/set_rates         # Upload new rates.yml (with validation)
/set_duties        # Upload new duties.yml (with validation)
/reload_configs    # Reload all configs into memory (hot reload)
```

**Features:**
- 🔒 Admin-only access (controlled by middleware)
- 🔄 Automatic backups with timestamp before upload
- ✅ YAML validation before saving
- 📦 FSM-based upload flow for safety
- ❌ User-friendly error messages

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
