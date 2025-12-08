"""
Обработчики команд Telegram бота.

Changelog:
- 2025-12-08: Добавлена поддержка engine_power_hp в cmd_calc и on_webapp_data
- 2025-12-08: Создан helper _format_result для единообразного форматирования
"""

from __future__ import annotations

from decimal import Decimal
import json
from typing import TYPE_CHECKING

from aiogram import Dispatcher, F, Router
from aiogram.filters import Command
from pydantic import ValidationError

from app.bot.keyboards import main_menu
from app.calculation.engine import calculate
from app.calculation.models import CalculationRequest, CalculationResult
from app.core.messages import WARN_WEBAPP_HTTP_URL
from app.core.settings import get_settings
from app.struct_logger import logger


if TYPE_CHECKING:  # pragma: no cover
    from aiogram.types import Message

router = Router()


def _format_result(result: CalculationResult, req: CalculationRequest) -> str:
    """
    Форматирование результата расчёта для Telegram.

    Args:
        result: Результат расчёта из engine.calculate()
        req: Исходный запрос (для отображения входных параметров)

    Returns:
        str: HTML-форматированное сообщение для Telegram
    """
    breakdown = result.breakdown
    meta = result.meta

    # Заголовок
    country_emoji = {"japan": "🇯🇵", "korea": "🇰🇷", "uae": "🇦🇪", "china": "🇨🇳", "georgia": "🇬🇪"}.get(
        req.country, "🌍"
    )
    country_label = {"japan": "Япония",
                     "korea": "Корея",
                     "uae": "ОАЭ",
                     "china": "Китай",
                     "georgia": "Грузия"}.get(
        req.country, "Неизвестно"
    )

    msg = "<b>💰 Расчёт стоимости растаможки</b>\n\n"

    # Входные параметры
    msg += f"{country_emoji} <b>Страна:</b> {country_label}\n"
    msg += f"📅 <b>Год:</b> {req.year} ({meta.age_category})\n"
    msg += f"⚙️ <b>Объём:</b> {req.engine_cc} см³\n"

    # NEW: Мощность
    if meta.engine_power_hp and meta.engine_power_kw:
        msg += f"🔋 <b>Мощность:</b> {meta.engine_power_hp} л.с. "
        msg += f"<i>({meta.engine_power_kw:.2f} кВт)</i>\n"

    msg += f"💵 <b>Цена:</b> {req.purchase_price:,.0f} {req.currency}\n"
    msg += "\n"

    # Детализация стоимости
    msg += "<b>📊 Детализация:</b>\n"
    msg += f"• Таможенная пошлина: {breakdown.duties_rub:,.0f} ₽\n"
    msg += f"• Утилизационный сбор: {breakdown.utilization_fee_rub:,.0f} ₽\n"

    # NEW: Коэффициент утильсбора (если есть)
    if meta.utilization_coefficient is not None:
        msg += f"  <i>(базовая ставка 20,000 ₽ × коэфф. {meta.utilization_coefficient})</i>\n"

    msg += f"• Таможенное оформление: {breakdown.customs_services_rub:,.0f} ₽\n"
    msg += f"• Фрахт: {breakdown.freight_rub:,.0f} ₽\n"
    msg += f"• Расходы в стране: {breakdown.country_expenses_rub:,.0f} ₽\n"
    msg += f"• Комиссия компании: {breakdown.company_commission_rub:,.0f} ₽\n"
    msg += f"• ЭРА-ГЛОНАСС: {breakdown.era_glonass_rub:,.0f} ₽\n"
    msg += "\n"

    # Итого
    msg += f"<b>💎 ИТОГО: {breakdown.total_rub:,.0f} ₽</b>\n"

    # Предупреждения
    if meta.warnings:
        msg += "\n⚠️ <b>Предупреждения:</b>\n"
        for warning in meta.warnings:
            msg += f"• {warning.message}\n"

    return msg


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    settings = get_settings()
    text = "Здравствуйте! Это калькулятор стоимости ввоза авто.\n"
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
    """
    Пример расчёта стоимости (демонстрация).

    NEW in v2.0: добавлено поле engine_power_hp.
    """
    try:
        # Пример: Япония, 2021 год, 1496 cc, 110 л.с., 2.5M JPY
        req = CalculationRequest(
            country="japan",
            year=2021,
            engine_cc=1496,
            engine_power_hp=110,  # NEW: обязательное поле
            purchase_price=Decimal("2500000"),
            currency="JPY",
            vehicle_type="M1",
        )

        # Расчёт
        result = calculate(req)

        # Форматирование результата
        response = _format_result(result, req)

        await message.answer(response, parse_mode="HTML")

    except Exception as e:
        logger.error("calc_command_error", error=str(e), exc_info=True)
        await message.answer("❌ Ошибка при расчёте. Попробуйте позже.")


@router.message(F.web_app_data)
async def on_webapp_data(message: Message) -> None:
    """
    Обработка данных из Telegram WebApp.

    NEW in v2.0: парсинг engine_power_hp из WebApp payload.
    """
    raw = message.web_app_data.data  # type: ignore[attr-defined]
    logger.info("webapp_data_received_raw", raw=raw)

    try:
        # Парсинг JSON
        data = json.loads(raw)
        logger.info("webapp_data_received", data_keys=list(data.keys()))

        # NEW: Проверка обязательного поля engine_power_hp
        if "engine_power_hp" not in data:
            await message.answer(
                "❌ <b>Ошибка:</b> Не указана мощность двигателя.\n"
                "Пожалуйста, заполните все поля формы.",
                parse_mode="HTML",
            )
            return

        # Формирование запроса
        req = CalculationRequest(
            country=data.get("country"),
            year=int(data.get("year")),
            engine_cc=int(data.get("engine_cc")),
            engine_power_hp=int(data.get("engine_power_hp")),  # NEW: добавлено поле
            purchase_price=Decimal(str(data.get("purchase_price"))),
            currency=data.get("currency"),
            vehicle_type=data.get("vehicle_type", "M1"),
            freight_type=data.get("freight_type", "container"),
            sanctions_unknown=data.get("sanctions_unknown", False),
        )

        # Расчёт
        result = calculate(req)

        # Форматирование
        response = _format_result(result, req)

        await message.answer(response, parse_mode="HTML")

    except ValidationError as ve:
        logger.warning("webapp_validation_error", errors=ve.errors())
        error_msgs = "\n".join([f"• {e['msg']}" for e in ve.errors()])
        await message.answer(f"❌ <b>Ошибка валидации:</b>\n{error_msgs}", parse_mode="HTML")
    except Exception as e:
        logger.error("webapp_data_error", error=str(e), exc_info=True)
        await message.answer("❌ Ошибка при обработке данных. Попробуйте ещё раз.")


def register(dp: Dispatcher) -> None:
    dp.include_router(router)
