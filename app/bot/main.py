from __future__ import annotations

import asyncio
import re

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramNotFound
from aiogram.types import BotCommand

from app.bot.handlers.start import register as register_start
from app.core.messages import (
    ERR_BAD_BOT_TOKEN,
    ERR_INVALID_BOT_TOKEN,
    ERR_MISSING_BOT_TOKEN,
    INFO_BOT_STARTED,
    INFO_BOT_STOPPED,
)
from app.core.settings import get_settings
from app.struct_logger import logger, setup_logging


TOKEN_PATTERN = re.compile(r"^\d{5,20}:[A-Za-z0-9_-]{20,}$")


class MissingBotTokenError(RuntimeError):
    """Raised when BOT_TOKEN is not provided in settings."""


class InvalidBotTokenError(RuntimeError):
    """Raised when BOT_TOKEN does not match expected pattern."""


def _build_bot() -> Bot:
    settings = get_settings()
    token = settings.bot_token
    if not token:
        raise MissingBotTokenError(ERR_MISSING_BOT_TOKEN)
    if not TOKEN_PATTERN.match(token):
        raise InvalidBotTokenError(ERR_INVALID_BOT_TOKEN)
    return Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


def _build_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    register_start(dp)
    return dp


async def _set_commands(bot: Bot) -> None:
    await bot.set_my_commands([
        BotCommand(command="start", description="Начать"),
        BotCommand(command="calc", description="Быстрый расчёт"),
    ])


async def main_async() -> None:
    # Initialize logging based on settings
    settings = get_settings()
    setup_logging(settings.log_level)

    bot: Bot | None = None
    started = False
    try:
        bot = _build_bot()
        dp = _build_dispatcher()
        try:
            await _set_commands(bot)
        except TelegramNotFound as error:
            raise InvalidBotTokenError(ERR_BAD_BOT_TOKEN) from error
        logger.info(INFO_BOT_STARTED)
        started = True
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        if started:
            logger.info(INFO_BOT_STOPPED)
        if bot is not None:
            await bot.session.close()


def run_bot() -> None:
    asyncio.run(main_async())

if __name__ == "__main__":
    run_bot()
