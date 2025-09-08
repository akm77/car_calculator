from __future__ import annotations

from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal, getcontext
from typing import Any

from app.core.messages import (
    ERR_MISSING_CURRENCY_RATE,
    WARN_JAPAN_TIER_CURRENCY,
    WARN_NO_DUTY_RATE,
)
from app.core.settings import get_configs
from app.struct_logger import logger

from ..services.cbr import get_effective_rates
from .models import CalculationMeta, CalculationRequest, CalculationResult, CostBreakdown
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


def _to_decimal(val: Any) -> Decimal:
    return val if isinstance(val, Decimal) else Decimal(str(val))


def _currency_rate(rates_conf: dict[str, Any], code: str) -> Decimal:
    key = f"{code.upper()}_RUB"
    try:
        return _to_decimal(rates_conf["currencies"][key])
    except Exception as e:  # pragma: no cover - defensive
        raise CalculationError.missing_currency_rate(key) from e


def _convert(amount: Decimal, currency: str, rates_conf: dict[str, Any]) -> Decimal:
    return (amount * _currency_rate(rates_conf, currency)).quantize(Decimal("0.0001"))


def _japan_country_expenses(fees: dict[str, Any], purchase_price: Decimal) -> Decimal:
    tiers = fees.get("tiers", [])
    for tier in tiers:
        max_price = tier.get("max_price")
        max_price_dec = _to_decimal(max_price) if max_price is not None else None
        if max_price_dec is None or purchase_price <= max_price_dec:
            return _to_decimal(tier.get("expenses", 0))
    return Decimal("0")


def _other_country_expenses(fees: dict[str, Any]) -> Decimal:
    base = fees.get("base_expenses", {})
    total = Decimal("0")
    for v in base.values():
        total += _to_decimal(v)
    return total


def _select_freight(fees: dict[str, Any], freight_type: str | None) -> tuple[Decimal, str, str]:
    freight_conf = fees.get("freight", {})
    if not freight_conf:
        return Decimal("0"), "none", "RUB"
    if freight_type and freight_type in freight_conf:
        f = freight_conf[freight_type]
        return _to_decimal(f.get("amount", 0.0)), freight_type, f.get("currency", "USD")
    k, v = next(iter(freight_conf.items()))
    return _to_decimal(v.get("amount", 0.0)), k, v.get("currency", "USD")


def _compute_duty(
    engine_cc: int,
    age_category: str,
    duties_conf: dict[str, Any],
    rates_conf: dict[str, Any],
    warnings: list[str],
    purchase_price_rub: Decimal,
) -> tuple[Decimal, str | None]:
    eur_rub = _currency_rate(rates_conf, "EUR")
    if age_category == "lt3":
        customs_value_eur = (purchase_price_rub / eur_rub).quantize(Decimal("0.0001"))
        bracket = find_lt3_value_bracket(duties_conf, float(customs_value_eur))
        if not bracket:
            warnings.append(WARN_NO_DUTY_RATE)
            return Decimal("0"), None
        percent = _to_decimal(bracket.get("percent", 0))
        min_rate = _to_decimal(bracket.get("min_rate_eur_per_cc", 0))
        duty_eur_percent = (customs_value_eur * percent).quantize(Decimal("0.0001"))
        duty_eur_min = (min_rate * _to_decimal(engine_cc)).quantize(Decimal("0.0001"))
        if duty_eur_percent >= duty_eur_min:
            mode = "percent"
            duty_eur = duty_eur_percent
        else:
            mode = "min"
            duty_eur = duty_eur_min
        return (duty_eur * eur_rub).quantize(Decimal("0.0001")), mode
    # 3_5 / gt5
    rate_eur_per_cc = find_duty_rate(duties_conf, age_category, engine_cc)
    if rate_eur_per_cc is None:
        warnings.append(WARN_NO_DUTY_RATE)
        return Decimal("0"), None
    duty_rub = (_to_decimal(engine_cc) * _to_decimal(rate_eur_per_cc) * eur_rub).quantize(
        Decimal("0.0001")
    )
    return duty_rub, "per_cc"


def _utilization_fee(age_category: str, engine_cc: int, rates_conf: dict[str, Any]) -> Decimal:
    util = rates_conf.get("utilization", {})
    table = util.get("personal_m1", [])
    key = "lt3" if age_category == "lt3" else "ge3"
    for seg in table:
        max_cc = seg.get("max_cc")
        if max_cc is None or engine_cc <= max_cc:
            return _to_decimal(seg.get(key, 0))
    return Decimal("0")


def _commission(amount_rub: Decimal, commissions_conf: dict[str, Any]) -> Decimal:
    thresholds = commissions_conf.get("thresholds", [])
    for th in thresholds:
        max_price = th.get("max_price")
        max_price_dec = _to_decimal(max_price) if max_price is not None else None
        if max_price_dec is None or amount_rub <= max_price_dec:
            return _to_decimal(th.get("amount", 0.0))
    return Decimal("0")


def _round_rub(val: Decimal) -> int:
    return int(val.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def calculate(req: CalculationRequest) -> CalculationResult:
    configs = get_configs()

    rates_conf = get_effective_rates(configs.rates)
    fees_conf = configs.fees.get(req.country, {})
    commissions_conf = configs.commissions
    duties_conf = configs.duties

    today = datetime.now(UTC).date()
    age_years = today.year - req.year
    age_category = get_age_category(age_years)
    passing_category = get_passing_category(age_category)

    purchase_price_rub = _convert(_to_decimal(req.purchase_price), req.currency, rates_conf)

    warnings: list[str] = []

    duties_rub_dec, duty_mode = _compute_duty(
        req.engine_cc,
        age_category,
        duties_conf,
        rates_conf,
        warnings,
        purchase_price_rub,
    )
    volume_band = format_volume_band(duties_conf, age_category, req.engine_cc)

    if req.country == "japan":
        if req.currency.upper() != "JPY":
            warnings.append(WARN_JAPAN_TIER_CURRENCY)
        expenses_val = _japan_country_expenses(fees_conf, _to_decimal(req.purchase_price))
    else:
        expenses_val = _other_country_expenses(fees_conf)
    expenses_currency = fees_conf.get("country_currency", req.currency)
    country_expenses_rub_dec = _convert(expenses_val, expenses_currency, rates_conf)

    freight_amount, _freight_type_used, freight_currency = _select_freight(
        fees_conf, req.freight_type
    )
    freight_rub_dec = _convert(freight_amount, freight_currency, rates_conf)

    customs_services_map = rates_conf.get("customs_services", {})
    customs_services_rub_dec = _to_decimal(customs_services_map.get(req.country, 0))

    era_glonass_rub_dec = _to_decimal(rates_conf.get("era_glonass_rub", 35000))
    utilization_fee_rub_dec = _utilization_fee(age_category, req.engine_cc, rates_conf)
    commission_rub_dec = _commission(purchase_price_rub, commissions_conf)

    total_rub_dec = (
        purchase_price_rub
        + duties_rub_dec
        + utilization_fee_rub_dec
        + customs_services_rub_dec
        + era_glonass_rub_dec
        + freight_rub_dec
        + country_expenses_rub_dec
        + commission_rub_dec
    )

    breakdown = CostBreakdown(
        purchase_price_rub=_round_rub(purchase_price_rub),
        duties_rub=_round_rub(duties_rub_dec),
        utilization_fee_rub=_round_rub(utilization_fee_rub_dec),
        customs_services_rub=_round_rub(customs_services_rub_dec),
        era_glonass_rub=_round_rub(era_glonass_rub_dec),
        freight_rub=_round_rub(freight_rub_dec),
        country_expenses_rub=_round_rub(country_expenses_rub_dec),
        company_commission_rub=_round_rub(commission_rub_dec),
        total_rub=_round_rub(total_rub_dec),
    )

    eur_rate = _currency_rate(rates_conf, "EUR")
    eur_source = rates_conf.get("live_source", "static")

    meta = CalculationMeta(
        age_years=age_years,
        age_category=age_category,
        volume_band=volume_band,
        passing_category=passing_category,
        warnings=warnings,
        duty_formula_mode=duty_mode,
        eur_rate_used=f"{eur_rate}:{eur_source}",
    )

    logger.info(
        "calculation_done",
        country=req.country,
        age_category=age_category,
        duty_mode=duty_mode,
        eur_rate=str(eur_rate),
        eur_source=eur_source,
        total=breakdown.total_rub,
    )

    return CalculationResult(request=req, meta=meta, breakdown=breakdown)
