# Car Import Cost Calculator

Telegram Bot + FastAPI backend + WebApp for calculating total import cost of cars from multiple source countries (Japan, Korea, UAE, China).

## Features (MVP)
- REST API: /api/health, /api/calculate
- Telegram Bot (aiogram v3) with /start command
- Config-driven fees & rates (YAML)
- Calculation engine skeleton (extensible)

## Tech Stack
- Python 3.13
- FastAPI
- aiogram 3
- Pydantic v2
- Uvicorn
- PyYAML
- structlog
- dotenv

## Project Structure
```
app/
  core/settings.py
  logging.py
  main.py (FastAPI app + run_api)
  api/routes.py
  calculation/
    engine.py
    models.py
    tariff_tables.py
  bot/
    main.py (run_bot)
    handlers/
    keyboards.py
  webapp/
    index.html
config/
  fees.yml
  commissions.yml
  rates.yml
  duties.yml
.env.example
```

## Quick Start
1. Install deps (via poetry or pip):
```
poetry install
```
2. Copy env file:
```
cp .env.example .env
```
3. Run API:
```
poetry run car-calculator-api
```
4. Run Bot (new terminal):
```
poetry run car-calculator-bot
```

## API
- GET /api/health -> {"status":"ok"}
- POST /api/calculate -> calculation result (stub now)

## Environment Variables (.env)
```
BOT_TOKEN=your_telegram_bot_token
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=info
```

## Development & QA
### Run tests
```
poetry run pytest
```
### Lint & format (Ruff)
```
poetry run ruff check .
poetry run ruff format .
```
### Type check (mypy)
```
poetry run mypy app
```
### Pre-commit
Install hooks once:
```
poetry run pre-commit install
```
Run on all files manually:
```
poetry run pre-commit run --all-files
```

## Next Steps
- Implement full calculation formulas
- Add WebApp JS and form
- Add tests
- Currency rate provider abstraction

## License
Proprietary / Internal use.
