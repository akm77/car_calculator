from __future__ import annotations

import json
from typing import TYPE_CHECKING

from aiogram import Dispatcher, F, Router
from aiogram.filters import Command

from app.bot.keyboards import webapp_keyboard
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
        "Используйте /calc для тестового расчета."  # noqa: RUF001
    )
    if settings.webapp_url.lower().startswith("https://"):
        await message.answer(
            text + "\nНажмите кнопку ниже для запуска WebApp.",  # noqa: RUF001
            reply_markup=webapp_keyboard(settings.webapp_url),
        )
    else:
        logger.warning(WARN_WEBAPP_HTTP_URL, url=settings.webapp_url)
        await message.answer(text + "\n(Времено без WebApp кнопки: нужен HTTPS)")  # noqa: RUF001


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
    try:
        data = json.loads(raw)
    except Exception:
        await message.answer("Получены данные WebApp (не JSON)")
        return
    # Expect structure { summary: str, total_rub: number }
    summary = data.get("summary") or "Результат получен"
    total = data.get("total_rub")
    line = f"{summary}\nИтого: {total:,.0f} RUB" if isinstance(total, (int, float)) else summary  # noqa: RUF001
    await message.answer(line)


def register(dp: Dispatcher) -> None:
    dp.include_router(router)
