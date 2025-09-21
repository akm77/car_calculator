#!/usr/bin/env bash
# Supervisor entrypoint for container to run API and/or Telegram bot.
# Controls:
#   RUN_MODE=api|bot|both  (default: both)
# Required env for bot: BOT_TOKEN
set -euo pipefail

API_HOST="${API_HOST:-0.0.0.0}"
API_PORT="${API_PORT:-8000}"
LOG_LEVEL="${LOG_LEVEL:-info}"
RUN_MODE="${RUN_MODE:-both}"

API_PID=""
BOT_PID=""

start_api() {
  echo "[entrypoint] Starting API on ${API_HOST}:${API_PORT}..."
  uvicorn app.main:app --host "$API_HOST" --port "$API_PORT" --log-level "$LOG_LEVEL" &
  API_PID=$!
  echo "[entrypoint] API PID: $API_PID"
}

start_bot() {
  if [[ -z "${BOT_TOKEN:-}" ]]; then
    echo "[entrypoint] WARNING: BOT_TOKEN is not set; bot may fail to start" >&2
  fi
  echo "[entrypoint] Starting Telegram bot (long polling)..."
  python -c 'from app.bot.main import run_bot; run_bot()' &
  BOT_PID=$!
  echo "[entrypoint] Bot PID: $BOT_PID"
}

stop_all() {
  echo "[entrypoint] Stopping..."
  if [[ -n "${API_PID}" ]] && kill -0 "$API_PID" 2>/dev/null; then
    kill "$API_PID" 2>/dev/null || true
  fi
  if [[ -n "${BOT_PID}" ]] && kill -0 "$BOT_PID" 2>/dev/null; then
    kill "$BOT_PID" 2>/dev/null || true
  fi
}

trap stop_all SIGINT SIGTERM

case "$RUN_MODE" in
  api)
    start_api
    ;;
  bot)
    start_bot
    ;;
  both|*)
    start_api
    # tiny delay to ensure API binds before bot logs
    sleep 0.3
    start_bot
    ;;
esac

# Wait for any to exit, then stop the rest
set +e
if [[ -n "$API_PID" && -n "$BOT_PID" ]]; then
  wait -n "$API_PID" "$BOT_PID"
elif [[ -n "$API_PID" ]]; then
  wait "$API_PID"
else
  wait "$BOT_PID"
fi
EXIT_CODE=$?
stop_all
wait 2>/dev/null || true
exit "$EXIT_CODE"

