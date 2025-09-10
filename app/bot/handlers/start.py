from __future__ import annotations

import json
from typing import TYPE_CHECKING

from aiogram import Dispatcher, F, Router
from aiogram.filters import Command

from app.bot.keyboards import main_menu
from app.calculation.engine import calculate
from app.calculation.models import CalculationRequest
from app.core.messages import WARN_WEBAPP_HTTP_URL
from app.core.settings import get_settings
from app.struct_logger import logger


if TYPE_CHECKING:  # pragma: no cover
    from aiogram.types import Message

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    settings = get_settings()
    text = (
        "Здравствуйте! Это калькулятор стоимости ввоза авто.\n"
    )
    if settings.webapp_url.lower().startswith("https://"):
        await message.answer(
            text + "\nНажмите кнопку ниже для запуска WebApp.",  # noqa: RUF001
            reply_markup=main_menu(settings.webapp_url),
        )
    else:
        logger.warning(WARN_WEBAPP_HTTP_URL, url=settings.webapp_url)
        await message.answer(text + "\n(Времено без WebApp кнопки: нужен HTTPS)")


@router.message(Command("calc"))
async def cmd_calc(message: Message) -> None:
    req = CalculationRequest(
        country="japan",
        year=2021,
        engine_cc=1496,
        purchase_price=1200000,
        currency="JPY",
        freight_type="standard",
    )
    result = calculate(req)
    total = result.breakdown.total_rub
    await message.answer(
        f"Пример расчета (Япония 2021 1.5L):\nИтого: {total:,.0f} RUB",  # noqa: RUF001
        disable_web_page_preview=True,
    )


@router.message(F.web_app_data)
async def on_webapp_data(message: Message) -> None:
    raw = message.web_app_data.data  # type: ignore[attr-defined]
    logger.info("webapp_data_received_raw", raw=raw)
    try:
        data = json.loads(raw)
        logger.info("webapp_data_parsed", keys=list(data.keys()))
    except Exception:
        logger.exception("webapp_data_parse_error")
        await message.answer("Получены данные WebApp (не JSON)")
        return

    action = data.get("action")

    # Process webapp data (any action)
    logger.info("webapp_data_processing", data=data)

    # Extract basic info
    total = data.get("total") or data.get("total_rub", 0)
    country = data.get("country", "")
    year = data.get("year", "")
    engine_cc = data.get("engine_cc", "")
    currency = data.get("currency", "")

    # Get country name in Russian
    country_names = {
        "japan": "Японии",
        "korea": "Кореи",
        "uae": "ОАЭ",
        "china": "Китая",
    }
    country_name = country_names.get(country, country)

    # Format the message
    if total and country_name:
        message_text = f"🚗 Расчет растаможки автомобиля из {country_name}\n\n"

        if year:
            message_text += f"📅 Год выпуска: {year}\n"
        if engine_cc:
            message_text += f"🔧 Объем двигателя: {engine_cc} см³\n"
        if currency and data.get("purchase_price"):
            purchase_price = data.get("purchase_price")
            try:
                # Convert to float for formatting, handle both string and numeric values
                purchase_price_num = float(purchase_price)
                message_text += f"💰 Цена покупки: {purchase_price_num:,.0f} {currency}\n"
            except (ValueError, TypeError):
                # Fallback if conversion fails
                message_text += f"💰 Цена покупки: {purchase_price} {currency}\n"

        message_text += f"\n💵 **Итоговая стоимость: {total:,.0f} ₽**"

        # Add detailed breakdown if available
        detail = data.get("detail", "")
        if detail and len(detail) > 0:
            # Telegram has message length limit, so we'll send summary + link to detailed breakdown
            message_text += f"\n\n📊 Подробная детализация:\n{detail}"

    else:
        # Fallback to summary or text
        message_text = data.get("summary") or data.get("text") or "Результат расчета получен"

    # Send the message
    try:
        await message.answer(message_text, parse_mode="Markdown")
        logger.info("webapp_data_sent", total=total, country=country, action=action)
    except Exception as e:
        # If markdown fails, try without formatting
        logger.warning("webapp_data_markdown_failed", error=str(e))
        try:
            # Remove markdown formatting and send plain text
            plain_text = message_text.replace("**", "").replace("*", "")
            await message.answer(plain_text)
            logger.info("webapp_data_sent_plain", total=total, country=country, action=action)
        except Exception as e2:
            logger.error("webapp_data_failed", error=str(e2))
            await message.answer("Результат расчета получен, но произошла ошибка при форматировании.")


def register(dp: Dispatcher) -> None:
    dp.include_router(router)
