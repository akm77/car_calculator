from __future__ import annotations


# Error / exception messages
ERR_MISSING_CURRENCY_RATE = "missing currency rate: {key}"
ERR_MISSING_BOT_TOKEN = "BOT_TOKEN not provided"
ERR_BAD_BOT_TOKEN="Telegram API responded Not Found (check BOT_TOKEN)"
ERR_INVALID_BOT_TOKEN = "invalid bot token format"
ERR_YEAR_FUTURE = "year cannot be in the future"
ERR_YEAR_TOO_OLD = "year too old for calculation baseline"

# Warning / info messages (still constants for consistency)
WARN_NO_DUTY_RATE = "No duty rate for age category; duty set to 0"
WARN_JAPAN_TIER_CURRENCY = (
    "Japan tiers expect JPY purchase price; different currency provided"
)
WARN_WEBAPP_HTTP_URL = "webapp url is not https; telegram webapp button skipped"

# Info messages
INFO_BOT_STARTED = "bot polling started"
INFO_BOT_STOPPED = "bot polling stopped"
