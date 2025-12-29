"""
Telegram Bot для расчёта таможенных платежей.

Features:
- Публичные команды: /start, /help
- Административные команды (требуют ADMIN_USER_IDS):
  - Config management: /get_*, /set_*, /reload_configs
  - Status: /config_status, /config_diff, /whoami, /list_configs
"""

from __future__ import annotations

import asyncio
import re

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramNotFound
from aiogram.types import BotCommand

from app.bot.handlers import config as config_handler
from app.bot.handlers.start import register as register_start
from app.bot.middlewares import AdminOnlyMiddleware
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


def _build_dispatcher(admin_ids: set[int]) -> Dispatcher:
    """
    Create and configure Dispatcher with handlers and middleware.

    Args:
        admin_ids: Set of Telegram user IDs with administrator privileges

    Returns:
        Configured Dispatcher
    """
    dp = Dispatcher()

    # ========================================================================
    # PUBLIC HANDLERS (доступны всем пользователям)
    # ========================================================================
    register_start(dp)

    # ========================================================================
    # ADMIN HANDLERS (требуют AdminOnlyMiddleware)
    # ========================================================================
    # Применить AdminOnlyMiddleware к config router
    config_router = config_handler.router
    config_router.message.middleware(AdminOnlyMiddleware(admin_ids))

    dp.include_router(config_router)

    logger.info(
        "dispatcher_configured",
        public_routers=1,
        admin_routers=1,
        admin_count=len(admin_ids),
    )

    return dp


async def _set_commands(bot: Bot) -> None:
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Начать"),
        ]
    )


async def main_async() -> None:
    """Главная асинхронная функция для запуска бота."""
    # Initialize logging based on settings
    settings = get_settings()
    setup_logging(settings.log_level)

    # Проверка конфигурации
    if not settings.bot_token:
        logger.error("bot_token_missing")
        raise MissingBotTokenError(ERR_MISSING_BOT_TOKEN)

    if not settings.admin_ids:
        logger.warning(
            "no_admins_configured",
            message="ADMIN_USER_IDS is empty - config management will be unavailable"
        )

    bot: Bot | None = None
    started = False
    try:
        bot = _build_bot()
        dp = _build_dispatcher(settings.admin_ids)
        try:
            await _set_commands(bot)
        except TelegramNotFound as error:
            raise InvalidBotTokenError(ERR_BAD_BOT_TOKEN) from error

        # Удалить webhook (если был установлен)
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("webhook_deleted")

        logger.info(
            INFO_BOT_STARTED,
            admin_count=len(settings.admin_ids),
            parse_mode="HTML",
        )
        started = True

        # Запустить long polling
        logger.info("polling_started")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

    except Exception as e:
        logger.error(
            "bot_crashed",
            error=str(e),
            error_type=type(e).__name__,
        )
        raise

    finally:
        if started:
            logger.info(INFO_BOT_STOPPED)
        if bot is not None:
            await bot.session.close()


def run_bot() -> None:
    """Entry point для запуска бота."""
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        logger.info("bot_interrupted_by_user")
    except Exception as e:
        logger.error(
            "bot_startup_failed",
            error=str(e),
            error_type=type(e).__name__,
        )
        raise

if __name__ == "__main__":
    run_bot()
