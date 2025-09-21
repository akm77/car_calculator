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


def _convert(amount: Decimal, currency: str, rates_conf: dict[str, Any]) -> Decimal:
    return quantize4(amount * _currency_rate(rates_conf, currency))

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


def _utilization_fee(age_category: str, engine_cc: int, rates_conf: dict[str, Any]) -> Decimal:
    util = rates_conf.get("utilization", {})
    table = util.get("personal_m1", [])

    # Определяем правильный ключ в зависимости от возрастной категории
    if age_category == "lt3":
        key = "lt3"
    elif age_category == "3_5":
        key = "ge3"  # для 3-5 лет используем ставку ge3
    else:  # gt5
        key = "gt5"  # для >5 лет используем ставку gt5 если есть, иначе ge3

    for seg in table:
        max_cc = seg.get("max_cc")
        if max_cc is None or engine_cc <= max_cc:
            # Сначала пробуем найти специфичный ключ, потом fallback на ge3
            rate = seg.get(key) or seg.get("ge3", 0)
            return to_decimal(rate)
    return Decimal("0")


def _commission(amount_rub: Decimal, commissions_conf: dict[str, Any]) -> Decimal:
    thresholds = commissions_conf.get("thresholds", [])
    for th in thresholds:
        max_price = th.get("max_price")
        max_price_dec = to_decimal(max_price) if max_price is not None else None
        if max_price_dec is None or amount_rub <= max_price_dec:
            return to_decimal(th.get("amount", 0.0))
    return Decimal("0")


def calculate(req: CalculationRequest) -> CalculationResult:
    configs = get_configs()

    rates_conf = get_effective_rates(configs.rates)
    fees_conf = configs.fees.get(req.country, {})
    commissions_conf = configs.commissions
    duties_conf = configs.duties

    # Track which currency rates were used in this calculation
    used_currency_codes: set[str] = set()

    today = datetime.now(UTC).date()
    age_years = today.year - req.year
    age_category = get_age_category(age_years)
    passing_category = get_passing_category(age_category)

    # Purchase price conversion
    used_currency_codes.add(req.currency.upper())
    purchase_price_rub = _convert(to_decimal(req.purchase_price), req.currency, rates_conf)

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
        # Use RUB->JPY conversion based on effective rates
        try:
            purchase_price_jpy = _convert_from_rub(purchase_price_rub, "JPY", rates_conf)
            used_currency_codes.add("JPY")
        except CalculationError:
            purchase_price_jpy = to_decimal(req.purchase_price)  # fallback to raw value
        if req.currency.upper() != "JPY":
            # Keep soft warning for UX, but compute tiers correctly
            warnings.append(
                WarningItem(code="JAPAN_CURRENCY", message=WARN_JAPAN_TIER_CURRENCY)
            )
        expenses_val = _japan_country_expenses(fees_conf, purchase_price_jpy)
        expenses_currency = fees_conf.get("country_currency", "JPY")
    else:
        expenses_val = _other_country_expenses(fees_conf)
        expenses_currency = fees_conf.get("country_currency", req.currency)

    used_currency_codes.add(expenses_currency.upper())
    country_expenses_rub_dec = _convert(expenses_val, expenses_currency, rates_conf)

    freight_amount, _freight_type_used, freight_currency = _select_freight(
        fees_conf, req.freight_type
    )
    used_currency_codes.add(freight_currency.upper())
    freight_rub_dec = _convert(freight_amount, freight_currency, rates_conf)

    customs_services_map = rates_conf.get("customs_services", {})
    customs_services_rub_dec = to_decimal(customs_services_map.get(req.country, 0))

    # ERA-GLONASS excluded from calculation (deprecated) — keep 0 in breakdown
    # (no variable assignment to avoid linter warning)

    # Utilization fee — only for M1. For other vehicle types, set 0 and warn to contact support.
    if getattr(req, "vehicle_type", "M1") != "M1":
        utilization_fee_rub_dec = Decimal("0")
        warnings.append(
            WarningItem(
                code="NON_M1",
                message=(
                    "Расчет утильсбора выполнен для легковых (M1). Для выбранного типа ТС "  # noqa: RUF001
                    "обратитесь в поддержку для уточнения ставки."
                ),
            )
        )
    else:
        utilization_fee_rub_dec = _utilization_fee(age_category, req.engine_cc, rates_conf)

    # Commission based ONLY on purchase price in RUB (business rule)
    commission_rub_dec = _commission(purchase_price_rub, commissions_conf)

    total_rub_dec = (
        purchase_price_rub
        + duties_rub_dec
        + utilization_fee_rub_dec
        + customs_services_rub_dec
        + freight_rub_dec
        + country_expenses_rub_dec
        + commission_rub_dec
    )

    breakdown = CostBreakdown(
        purchase_price_rub=round_rub(purchase_price_rub),
        duties_rub=round_rub(duties_rub_dec),
        utilization_fee_rub=round_rub(utilization_fee_rub_dec),
        customs_services_rub=round_rub(customs_services_rub_dec),
        era_glonass_rub=0,
        freight_rub=round_rub(freight_rub_dec),
        country_expenses_rub=round_rub(country_expenses_rub_dec),
        company_commission_rub=round_rub(commission_rub_dec),
        total_rub=round_rub(total_rub_dec),
    )

    eur_rate = _currency_rate(rates_conf, "EUR")
    eur_source = rates_conf.get("live_source", "static")

    # Collect actual rates used
    rates_used: dict[str, float] = {}
    currencies_table = rates_conf.get("currencies", {})
    for code in sorted({c.upper() for c in used_currency_codes}):
        key = f"{code}_RUB"
        if key in currencies_table:
            try:
                rates_used[key] = float(currencies_table[key])
            except Exception:
                continue

    # Extract purchase currency rate (if available)
    purchase_rate_key = f"{req.currency.upper()}_RUB"
    purchase_rate_val = rates_used.get(purchase_rate_key)

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
        vehicle_type=getattr(req, "vehicle_type", None),
        rates_used=rates_used,
    )

    logger.info(
        "calculation_done",
        country=req.country,
        age_category=age_category,
        duty_mode=duty_mode,
        eur_rate=str(eur_rate),
        eur_source=eur_source,
        purchase_currency=req.currency.upper(),
        purchase_rate_key=purchase_rate_key,
        purchase_rate_rub=purchase_rate_val,
        rates_used=rates_used,
        total=breakdown.total_rub,
    )

    return CalculationResult(request=req, meta=meta, breakdown=breakdown)
