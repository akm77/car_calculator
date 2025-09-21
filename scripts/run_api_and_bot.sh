#!/usr/bin/env bash
# A simple supervisor script to run API and/or Telegram bot without Poetry.
# Usage:
#   scripts/run_api_and_bot.sh [api|bot|both]    # default: both
# Requirements:
#   - Python 3 available on PATH
#   - Dependencies installed (pip install -r requirements.txt)
#   - Optional: .venv/ will be auto-activated if present
#   - .env loaded automatically if present (exports variables)

set -euo pipefail

# --- Resolve project root ---
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
PROJECT_ROOT="${SCRIPT_DIR%/scripts}"
cd "$PROJECT_ROOT"

# --- Activate venv if exists ---
if [[ -d ".venv" && -f ".venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

PYTHON_BIN="${PYTHON_BIN:-python3}"

# --- Load .env if present ---
if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

# --- Defaults ---
API_HOST="${API_HOST:-0.0.0.0}"
API_PORT="${API_PORT:-8000}"
LOG_LEVEL="${LOG_LEVEL:-info}"
PUBLIC_BASE_URL="${PUBLIC_BASE_URL:-http://localhost:${API_PORT}}"
MODE="${1:-both}"

# --- Helpers ---
red()   { printf "\033[31m%s\033[0m\n" "$*"; }
green() { printf "\033[32m%s\033[0m\n" "$*"; }
yellow(){ printf "\033[33m%s\033[0m\n" "$*"; }

ensure_dep() {
  local mod="$1"
  if ! "$PYTHON_BIN" - <<PY 2>/dev/null
import ${mod}
PY
  then
    red "Missing Python module: ${mod}. Install deps first (pip install -r requirements.txt)."
    exit 1
  fi
}

start_api() {
  ensure_dep uvicorn
  green "Starting API on ${API_HOST}:${API_PORT} (log-level=${LOG_LEVEL})..."
  "$PYTHON_BIN" -m uvicorn app.main:app \
    --host "$API_HOST" \
    --port "$API_PORT" \
    --log-level "$LOG_LEVEL" &
  API_PID=$!
  echo "$API_PID" > .api.pid
  green "API PID: ${API_PID}"
}

start_bot() {
  if [[ -z "${BOT_TOKEN:-}" ]]; then
    yellow "BOT_TOKEN is not set. Bot will likely fail to start. Export BOT_TOKEN or add it to .env."
  fi
  green "Starting Telegram bot (long polling)..."
  "$PYTHON_BIN" -c 'from app.bot.main import run_bot; run_bot()' &
  BOT_PID=$!
  echo "$BOT_PID" > .bot.pid
  green "Bot PID: ${BOT_PID}"
}

stop_all() {
  yellow "Shutting down..."
  if [[ -n "${API_PID:-}" ]] && kill -0 "$API_PID" 2>/dev/null; then
    kill "$API_PID" 2>/dev/null || true
  fi
  if [[ -n "${BOT_PID:-}" ]] && kill -0 "$BOT_PID" 2>/dev/null; then
    kill "$BOT_PID" 2>/dev/null || true
  fi
}

trap stop_all SIGINT SIGTERM

API_PID=""
BOT_PID=""

case "$MODE" in
  api)
    start_api
    ;;
  bot)
    start_bot
    ;;
  both|*)
    start_api
    # small delay so API starts listening before bot logs
    sleep 0.5
    start_bot
    ;;
esac

# Wait for any child to exit, then stop the other
if [[ -n "${API_PID}" || -n "${BOT_PID}" ]]; then
  set +e
  if [[ -n "${API_PID}" && -n "${BOT_PID}" ]]; then
    wait -n "$API_PID" "$BOT_PID"
  elif [[ -n "${API_PID}" ]]; then
    wait "$API_PID"
  else
    wait "$BOT_PID"
  fi
  EXIT_CODE=$?
  stop_all
  wait 2>/dev/null || true
  exit "$EXIT_CODE"
fi
