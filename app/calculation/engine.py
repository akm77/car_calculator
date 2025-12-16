from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal, getcontext
from typing import Any

from app.core.messages import (
    ERR_MISSING_CURRENCY_RATE,
    WARN_JAPAN_TIER_CURRENCY,
    WARN_NO_DUTY_RATE,
)
from app.core.settings import get_configs
from app.struct_logger import logger

from ..services.cbr import get_effective_rates
from .models import (
    CalculationMeta,
    CalculationRequest,
    CalculationResult,
    CostBreakdown,
    RateUsage,
    WarningItem,
)
from .rounding import quantize4, round_rub, to_decimal
from .tariff_tables import (
    find_duty_rate,
    find_lt3_value_bracket,
    format_volume_band,
    get_age_category,
    get_passing_category,
)


# Set high precision to avoid intermediate rounding issues
getcontext().prec = 28


class CalculationError(Exception):
    """Domain error for calculation pipeline."""

    @classmethod
    def missing_currency_rate(cls, key: str) -> CalculationError:  # removed quotes per Ruff
        return cls(ERR_MISSING_CURRENCY_RATE.format(key=key))


def _currency_rate(rates_conf: dict[str, Any], code: str) -> Decimal:
    key = f"{code.upper()}_RUB"
    try:
        return to_decimal(rates_conf["currencies"][key])
    except Exception as e:  # pragma: no cover - defensive
        raise CalculationError.missing_currency_rate(key) from e


def _get_bank_commission_percent(commissions_conf: dict[str, Any]) -> float:
    """Extract effective bank commission percent from commissions config.

    Behaviour (per sprint1 spec):
    - If `bank_commission` section is missing -> 0.0
    - If `enabled` is explicitly False -> 0.0
    - If `percent` is missing -> use `meta.default_percent` or 0.0
    - Otherwise return `percent` as float.
    """

    bank_conf = commissions_conf.get("bank_commission")
    if not isinstance(bank_conf, dict):
        return 0.0

    if bank_conf.get("enabled") is False:
        return 0.0

    percent = bank_conf.get("percent")
    if percent is None:
        meta = bank_conf.get("meta") or {}
        default_percent = meta.get("default_percent", 0.0)
        try:
            return float(default_percent)
        except (TypeError, ValueError):
            return 0.0

    try:
        return float(percent)
    except (TypeError, ValueError):  # pragma: no cover - defensive
        return 0.0


def _effective_currency_rate(
    rates_conf: dict[str, Any],
    code: str,
    bank_commission_percent: float,
) -> Decimal:
    """Return effective VALUTA/RUB rate with bank commission applied.

    effective_rate = base_rate * (1 + bank_commission_percent / 100).
    """

    base = _currency_rate(rates_conf, code)
    if not bank_commission_percent:
        return base
    factor = Decimal("1") + (to_decimal(bank_commission_percent) / Decimal("100"))
    return quantize4(base * factor)


def _convert(
    amount: Decimal,
    currency: str,
    rates_conf: dict[str, Any],
    bank_commission_percent: float | None = None,
) -> Decimal:
    """Convert from VALUTA to RUB using effective rate and bank commission.

    Backwards compatible: if bank_commission_percent is None, use base rate only.
    """

    if bank_commission_percent is None:
        rate = _currency_rate(rates_conf, currency)
    else:
        rate = _effective_currency_rate(rates_conf, currency, bank_commission_percent)
    return quantize4(amount * rate)


# New: convert RUB -> target currency using configured rates (RUB per unit)
# Safe utility for internal use (e.g., normalize Japan tiers input)


def _convert_from_rub(amount_rub: Decimal, currency: str, rates_conf: dict[str, Any]) -> Decimal:
    rate = _currency_rate(rates_conf, currency)
    if rate == 0:
        return Decimal("0")
    return quantize4(amount_rub / rate)


def _japan_country_expenses(fees: dict[str, Any], purchase_price: Decimal) -> Decimal:
    tiers = fees.get("tiers", [])
    for tier in tiers:
        max_price = tier.get("max_price")
        max_price_dec = to_decimal(max_price) if max_price is not None else None
        if max_price_dec is None or purchase_price <= max_price_dec:
            return to_decimal(tier.get("expenses", 0))
    return Decimal("0")


def _other_country_expenses(fees: dict[str, Any]) -> Decimal:
    base = fees.get("base_expenses", {})
    total = Decimal("0")
    for v in base.values():
        total += to_decimal(v)
    return total


def _select_freight(fees: dict[str, Any], freight_type: str | None) -> tuple[Decimal, str, str]:
    freight_conf = fees.get("freight", {})
    if not freight_conf:
        return Decimal("0"), "none", "RUB"
    if freight_type and freight_type in freight_conf:
        f = freight_conf[freight_type]
        return to_decimal(f.get("amount", 0.0)), freight_type, f.get("currency", "USD")
    k, v = next(iter(freight_conf.items()))
    return to_decimal(v.get("amount", 0.0)), k, v.get("currency", "USD")


def _compute_duty(
    engine_cc: int,
    age_category: str,
    duties_conf: dict[str, Any],
    rates_conf: dict[str, Any],
    warnings: list[WarningItem],
    purchase_price_rub: Decimal,
) -> tuple[Decimal, str | None, dict[str, Any]]:
    eur_rub = _currency_rate(rates_conf, "EUR")
    details: dict[str, Any] = {}
    if age_category == "lt3":
        customs_value_eur = quantize4(purchase_price_rub / eur_rub)
        details["customs_value_eur"] = float(customs_value_eur)
        bracket = find_lt3_value_bracket(duties_conf, float(customs_value_eur))
        if not bracket:
            warnings.append(WarningItem(code="NO_DUTY", message=WARN_NO_DUTY_RATE))
            return Decimal("0"), None, details
        percent = to_decimal(bracket.get("percent", 0))
        min_rate = to_decimal(bracket.get("min_rate_eur_per_cc", 0))
        details["duty_percent"] = float(percent)
        details["duty_min_rate_eur_per_cc"] = float(min_rate)
        max_val = bracket.get("max_customs_value_eur")
        if max_val is not None:
            details["duty_value_bracket_max_eur"] = float(max_val)
        duty_eur_percent = quantize4(customs_value_eur * percent)
        duty_eur_min = quantize4(min_rate * to_decimal(engine_cc))
        if duty_eur_percent >= duty_eur_min:
            mode = "percent"
            duty_eur = duty_eur_percent
        else:
            mode = "min"
            duty_eur = duty_eur_min
        return quantize4(duty_eur * eur_rub), mode, details
    # 3_5 / gt5
    rate_eur_per_cc = find_duty_rate(duties_conf, age_category, engine_cc)
    if rate_eur_per_cc is None:
        warnings.append(WarningItem(code="NO_DUTY", message=WARN_NO_DUTY_RATE))
        return Decimal("0"), None, details
    details["duty_rate_eur_per_cc"] = float(rate_eur_per_cc)
    duty_rub = quantize4(to_decimal(engine_cc) * to_decimal(rate_eur_per_cc) * eur_rub)
    return duty_rub, "per_cc", details


def _utilization_fee_v2(
    age_category: str, engine_cc: int, engine_power_hp: int, rates_conf: dict[str, Any]
) -> tuple[Decimal, float]:
    """
    Новая система утильсбора (2025): 2D-таблица по объёму и мощности.

    Args:
        age_category: 'lt3', '3_5', или 'gt5'
        engine_cc: Объём двигателя в см³
        engine_power_hp: Мощность в л.с.
        rates_conf: Конфигурация с utilization_m1_personal

    Returns:
        (fee_rub, coefficient): Сумма сбора и использованный коэффициент
    """
    util = rates_conf.get("utilization_m1_personal", {})
    base_rate = to_decimal(util.get("base_rate_rub", 20000))

    # 1. Конвертация л.с. → кВт
    HP_TO_KW = 0.7355
    engine_power_kw = engine_power_hp * HP_TO_KW

    # 2. Поиск диапазона объёма
    volume_bands = util.get("volume_bands", [])
    volume_band = None
    for band in volume_bands:
        vol_range = band.get("volume_range", [])
        if len(vol_range) >= 2 and vol_range[0] <= engine_cc <= vol_range[1]:
            volume_band = band
            break

    if not volume_band:
        logger.warning(f"Volume band not found for {engine_cc} cc, returning 0")
        return Decimal("0"), 0.0

    # 3. Поиск диапазона мощности
    power_brackets = volume_band.get("power_brackets", [])
    coefficient = None
    for bracket in power_brackets:
        max_kw = bracket.get("power_kw_max")
        # Если max_kw is None — это последний диапазон (без верхней границы)
        if max_kw is None or engine_power_kw <= max_kw:
            # Выбираем коэффициент по возрасту: lt3 или gt3
            coef_key = "coefficient_lt3" if age_category == "lt3" else "coefficient_gt3"
            coefficient = bracket.get(coef_key, 0)
            break

    if coefficient is None:
        logger.warning(
            f"Power bracket not found for {engine_power_kw:.2f} kW "
            f"({engine_power_hp} hp) in volume band {engine_cc} cc, returning 0"
        )
        return Decimal("0"), 0.0

    # 4. Расчёт: base_rate × coefficient
    coefficient_dec = to_decimal(coefficient)
    fee = quantize4(base_rate * coefficient_dec)

    return fee, float(coefficient)


def _commission(
    amount_rub: Decimal,
    commissions_conf: dict[str, Any],
    country: str | None,
    rates_conf: dict[str, Any] | None = None,
    bank_commission_percent: float | None = None,
) -> Decimal:
    """Return commission in RUB (NEW 2025: fixed 1000 USD or country override).

    Selection order:
    1) if by_country[country] exists -> use commission_usd from there
    2) else use default_commission_usd (converted to RUB)

    Банковская комиссия применяется как надбавка к валютному курсу при
    конвертации комиссии компании (1000 USD → RUB), если задан
    bank_commission_percent.
    """
    # Check for country-specific override (e.g., UAE = 0)
    if country:
        by_country = commissions_conf.get("by_country") or {}
        country_config = by_country.get(country)
        if country_config is not None:
            # New structure: commission_usd key directly in country config
            if isinstance(country_config, dict) and "commission_usd" in country_config:
                commission_usd = to_decimal(country_config["commission_usd"])
                if rates_conf:
                    # Apply bank commission via effective rate
                    return _convert(
                        commission_usd,
                        "USD",
                        rates_conf,
                        bank_commission_percent,
                    )
                return Decimal("0")
            # Legacy structure: list with amount
            elif isinstance(country_config, list) and country_config:
                return to_decimal(country_config[0].get("amount", 0))

    # Default: 1000 USD converted to RUB
    default_usd = commissions_conf.get("default_commission_usd", 1000)
    if rates_conf:
        commission_usd = to_decimal(default_usd)
        return _convert(
            commission_usd,
            "USD",
            rates_conf,
            bank_commission_percent,
        )

    # Fallback if no rates (shouldn't happen in practice)
    return Decimal("0")


def calculate(req: CalculationRequest) -> CalculationResult:
    configs = get_configs()

    rates_conf = get_effective_rates(configs.rates)
    fees_conf = configs.fees.get(req.country, {})
    commissions_conf = configs.commissions
    duties_conf = configs.duties

    # Bank commission percent from config (global for now)
    bank_commission_percent = _get_bank_commission_percent(commissions_conf)

    # Track which currency rates were used in this calculation
    used_currency_codes: set[str] = set()

    today = datetime.now(UTC).date()
    age_years = today.year - req.year
    age_category = get_age_category(age_years)
    passing_category = get_passing_category(age_category)

    # Purchase price conversion
    used_currency_codes.add(req.currency.upper())
    # IMPORTANT: bank commission SHOULD NOT affect customs value / duties.
    # We therefore always use base currency rate here (bank_commission_percent=None).
    purchase_price_rub = _convert(
        to_decimal(req.purchase_price),
        req.currency,
        rates_conf,
        bank_commission_percent=None,
    )

    warnings: list[WarningItem] = []

    # Sanctions status unknown warning (does not affect numeric calculation)
    if req.sanctions_unknown:
        warnings.append(
            WarningItem(
                code="SANCTIONS_UNKNOWN",
                message=(
                    "Статус санкционности автомобиля не подтвержден. Фрахт может отличаться; "
                    "для уточнения обратитесь в поддержку."
                ),
            )
        )

    duties_rub_dec, duty_mode, duty_details = _compute_duty(
        req.engine_cc,
        age_category,
        duties_conf,
        rates_conf,
        warnings,
        purchase_price_rub,
    )
    # Duty always uses EUR
    used_currency_codes.add("EUR")

    volume_band = format_volume_band(duties_conf, age_category, req.engine_cc)

    # Country expenses
    if req.country == "japan":
        # Normalize tier selection to purchase price expressed in JPY regardless of input currency
        # Use RUB->JPY conversion based on base rates (no bank commission impact on tiers)
        try:
            purchase_price_jpy = _convert_from_rub(purchase_price_rub, "JPY", rates_conf)
            used_currency_codes.add("JPY")
        except CalculationError:
            purchase_price_jpy = to_decimal(req.purchase_price)  # fallback to raw value
        if req.currency.upper() != "JPY":
            # Keep soft warning for UX, but compute tiers correctly
            warnings.append(WarningItem(code="JAPAN_CURRENCY", message=WARN_JAPAN_TIER_CURRENCY))
        expenses_val = _japan_country_expenses(fees_conf, purchase_price_jpy)
        expenses_currency = fees_conf.get("country_currency", "JPY")
    else:
        expenses_val = _other_country_expenses(fees_conf)
        expenses_currency = fees_conf.get("country_currency", req.currency)

    used_currency_codes.add(expenses_currency.upper())
    # Country expenses also should not be affected by bank commission when comparing
    # against existing regression expectations.
    country_expenses_rub_dec = _convert(
        expenses_val,
        expenses_currency,
        rates_conf,
        bank_commission_percent=None,
    )

    freight_amount, _freight_type_used, freight_currency = _select_freight(
        fees_conf, req.freight_type
    )
    used_currency_codes.add(freight_currency.upper())
    # Freight is also converted without extra bank commission in current regression.
    freight_rub_dec = _convert(
        freight_amount,
        freight_currency,
        rates_conf,
        bank_commission_percent=None,
    )

    customs_services_map = rates_conf.get("customs_services", {})
    customs_services_rub_dec = to_decimal(customs_services_map.get(req.country, 0))

    # ERA-GLONASS: NEW 2025 - configurable value (default 45000 RUB)
    era_glonass_rub_dec = to_decimal(rates_conf.get("era_glonass_rub", 45000))

    # Utilization fee — only for M1. For other vehicle types, set 0 and warn to contact support.
    utilization_coefficient = None
    if getattr(req, "vehicle_type", "M1") != "M1":
        utilization_fee_rub_dec = Decimal("0")
        warnings.append(
            WarningItem(
                code="NON_M1",
                message=(
                    "Расчёт утилизационного сбора выполнен для легковых (M1). Для выбранного типа ТС "  # noqa: RUF001
                    "обратитесь в поддержку для уточнения ставки."
                ),
            )
        )
    else:
        # NEW: Call v2 function with engine_power_hp
        utilization_fee_rub_dec, utilization_coefficient = _utilization_fee_v2(
            age_category, req.engine_cc, req.engine_power_hp, rates_conf
        )

    # Commission: NEW 2025 - fixed 1000 USD (or 0 for UAE)
    # Here bank commission percent is applied to conversion of commission itself,
    # which matches business expectation that bank fee is paid on company commission.
    commission_rub_dec = _commission(
        purchase_price_rub,
        commissions_conf,
        req.country,
        rates_conf,
        bank_commission_percent,
    )
    if commission_rub_dec > 0:
        used_currency_codes.add("USD")  # Commission uses USD

    total_rub_dec = (
        purchase_price_rub
        + duties_rub_dec
        + utilization_fee_rub_dec
        + customs_services_rub_dec
        + freight_rub_dec
        + country_expenses_rub_dec
        + era_glonass_rub_dec
        + commission_rub_dec
    )

    breakdown = CostBreakdown(
        purchase_price_rub=round_rub(purchase_price_rub),
        duties_rub=round_rub(duties_rub_dec),
        utilization_fee_rub=round_rub(utilization_fee_rub_dec),
        customs_services_rub=round_rub(customs_services_rub_dec),
        era_glonass_rub=round_rub(era_glonass_rub_dec),
        freight_rub=round_rub(freight_rub_dec),
        country_expenses_rub=round_rub(country_expenses_rub_dec),
        company_commission_rub=round_rub(commission_rub_dec),
        total_rub=round_rub(total_rub_dec),
    )

    eur_rate = _currency_rate(rates_conf, "EUR")
    eur_source = rates_conf.get("live_source", "static")

    # Collect actual base rates used (legacy view)
    rates_used: dict[str, float] = {}
    currencies_table = rates_conf.get("currencies", {})
    for code in sorted({c.upper() for c in used_currency_codes}):
        key = f"{code}_RUB"
        if key in currencies_table:
            try:
                rates_used[key] = float(currencies_table[key])
            except Exception:  # pragma: no cover - defensive
                continue

    # New: detailed rates with bank commission applied
    detailed_rates_used: dict[str, RateUsage] = {}
    for code in sorted({c.upper() for c in used_currency_codes}):
        key = f"{code}_RUB"
        if key not in currencies_table:
            continue
        try:
            base_rate = float(currencies_table[key])
        except Exception:  # pragma: no cover - defensive
            continue
        # effective_rate всегда зависит от сконфигурированного процента комиссии
        effective_rate_dec = _effective_currency_rate(rates_conf, code, bank_commission_percent)
        effective_rate = float(effective_rate_dec)
        percent = float(bank_commission_percent or 0.0)
        # Форматируем человекочитаемую строку: округляем base до 2 знаков, процент до целого
        base_str = f"{base_rate:.2f}".rstrip("0").rstrip(".")
        if percent:
            percent_str = f"{percent:.0f}".rstrip(".0")
            display = f"{code}/RUB = {base_str} + {percent_str}%"
        else:
            display = f"{code}/RUB = {base_str}"
        detailed_rates_used[code] = RateUsage(
            base_rate=base_rate,
            effective_rate=effective_rate,
            bank_commission_percent=percent,
            display=display,
        )

    # Extract purchase currency rate (if available)
    purchase_rate_key = f"{req.currency.upper()}_RUB"
    purchase_rate_val = rates_used.get(purchase_rate_key)

    # Calculate engine_power_kw for display
    HP_TO_KW = 0.7355
    engine_power_kw = round(req.engine_power_hp * HP_TO_KW, 2)

    meta = CalculationMeta(
        age_years=age_years,
        age_category=age_category,
        volume_band=volume_band,
        passing_category=passing_category,
        warnings=warnings,
        duty_formula_mode=duty_mode,
        eur_rate_used=f"{eur_rate}:{eur_source}",
        customs_value_eur=duty_details.get("customs_value_eur"),
        duty_percent=duty_details.get("duty_percent"),
        duty_min_rate_eur_per_cc=duty_details.get("duty_min_rate_eur_per_cc"),
        duty_rate_eur_per_cc=duty_details.get("duty_rate_eur_per_cc"),
        duty_value_bracket_max_eur=duty_details.get("duty_value_bracket_max_eur"),
        vehicle_type=req.vehicle_type,
        engine_power_hp=req.engine_power_hp,
        engine_power_kw=engine_power_kw,
        utilization_coefficient=utilization_coefficient,
        rates_used=rates_used,
        detailed_rates_used=detailed_rates_used,
    )

    # For backward compatibility, keep purchase_rate_val implicitly available via
    # meta.rates_used[purchase_rate_key] if present; we don't introduce
    # dedicated fields to avoid changing API surface.

    return CalculationResult(request=req, meta=meta, breakdown=breakdown)
