from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.core.messages import (
    ERR_MISSING_CURRENCY_RATE,
    WARN_JAPAN_TIER_CURRENCY,
    WARN_NO_DUTY_RATE,
)
from app.core.settings import get_configs

from ..services.cbr import get_effective_rates
from .models import CalculationMeta, CalculationRequest, CalculationResult, CostBreakdown
from .tariff_tables import (
    find_duty_rate,
    find_lt3_value_bracket,
    format_volume_band,
    get_age_category,
    get_passing_category,
)


class CalculationError(Exception):
    """Domain error for calculation pipeline."""

    @classmethod
    def missing_currency_rate(cls, key: str) -> CalculationError:  # removed quotes per Ruff
        return cls(ERR_MISSING_CURRENCY_RATE.format(key=key))


def _currency_rate(rates_conf: dict[str, Any], code: str) -> float:
    key = f"{code.upper()}_RUB"
    try:
        return float(rates_conf["currencies"][key])
    except Exception as e:  # pragma: no cover - defensive
        raise CalculationError.missing_currency_rate(key) from e


def _convert(amount: float, currency: str, rates_conf: dict[str, Any]) -> float:
    return amount * _currency_rate(rates_conf, currency)


def _japan_country_expenses(fees: dict[str, Any], purchase_price: float) -> float:
    tiers = fees.get("tiers", [])
    for tier in tiers:
        max_price = tier.get("max_price")
        if max_price is None or purchase_price <= max_price:
            return float(tier.get("expenses", 0))
    return 0.0


def _other_country_expenses(fees: dict[str, Any]) -> float:
    base = fees.get("base_expenses", {})
    return float(sum(base.values()))


def _select_freight(fees: dict[str, Any], freight_type: str | None) -> tuple[float, str, str]:
    freight_conf = fees.get("freight", {})
    if not freight_conf:
        return 0.0, "none", "RUB"
    if freight_type and freight_type in freight_conf:
        f = freight_conf[freight_type]
        return float(f.get("amount", 0.0)), freight_type, f.get("currency", "USD")
    k, v = next(iter(freight_conf.items()))
    return float(v.get("amount", 0.0)), k, v.get("currency", "USD")


def _compute_duty(
    engine_cc: int,
    age_category: str,
    duties_conf: dict[str, Any],
    rates_conf: dict[str, Any],
    warnings: list[str],
    purchase_price_rub: float,
) -> float:
    eur_rub = _currency_rate(rates_conf, "EUR")
    # lt3 logic: percentage of customs value (EUR) but not less than min per cc
    if age_category == "lt3":
        customs_value_eur = purchase_price_rub / eur_rub
        bracket = find_lt3_value_bracket(duties_conf, customs_value_eur)
        if not bracket:
            warnings.append(WARN_NO_DUTY_RATE)
            return 0.0
        percent = float(bracket.get("percent", 0))
        min_rate = float(bracket.get("min_rate_eur_per_cc", 0))
        duty_eur_percent = customs_value_eur * percent
        duty_eur_min = min_rate * engine_cc
        duty_eur = max(duty_eur_percent, duty_eur_min)
        return duty_eur * eur_rub
    # 3_5 & gt5: band rate per cc
    rate_eur_per_cc = find_duty_rate(duties_conf, age_category, engine_cc)
    if rate_eur_per_cc is None:
        warnings.append(WARN_NO_DUTY_RATE)
        return 0.0
    return engine_cc * rate_eur_per_cc * eur_rub


def _utilization_fee(age_category: str, engine_cc: int, rates_conf: dict[str, Any]) -> float:
    # New table-based logic (personal M1) with absolute RUB values per engine segment.
    util = rates_conf.get("utilization", {})
    table = util.get("personal_m1", [])
    key = "lt3" if age_category == "lt3" else "ge3"
    for seg in table:
        max_cc = seg.get("max_cc")
        if max_cc is None or engine_cc <= max_cc:
            return float(seg.get(key, 0))
    return 0.0


def _commission(amount_rub: float, commissions_conf: dict[str, Any]) -> float:
    thresholds = commissions_conf.get("thresholds", [])
    for th in thresholds:
        max_price = th.get("max_price")
        if max_price is None or amount_rub <= max_price:
            return float(th.get("amount", 0.0))
    return 0.0


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

    # Convert purchase first (needed for lt3 duty logic)
    purchase_price_rub = _convert(req.purchase_price, req.currency, rates_conf)

    warnings: list[str] = []

    duties_rub = _compute_duty(
        req.engine_cc,
        age_category,
        duties_conf,
        rates_conf,
        warnings,
        purchase_price_rub,
    )
    volume_band = format_volume_band(duties_conf, age_category, req.engine_cc)

    if req.country == "japan":
        if req.currency.lower() != "jpy":
            warnings.append(WARN_JAPAN_TIER_CURRENCY)
        expenses_val = _japan_country_expenses(fees_conf, req.purchase_price)
    else:
        expenses_val = _other_country_expenses(fees_conf)
    expenses_currency = fees_conf.get("country_currency", req.currency)
    country_expenses_rub = _convert(expenses_val, expenses_currency, rates_conf)

    freight_amount, _freight_type_used, freight_currency = _select_freight(
        fees_conf, req.freight_type
    )
    freight_rub = _convert(freight_amount, freight_currency, rates_conf)

    customs_services_map = rates_conf.get("customs_services", {})
    customs_services_rub = float(customs_services_map.get(req.country, 0))

    era_glonass_rub = float(rates_conf.get("era_glonass_rub", 35000))
    utilization_fee_rub = _utilization_fee(age_category, req.engine_cc, rates_conf)
    commission_rub = _commission(purchase_price_rub, commissions_conf)

    total_rub = sum(
        [
            purchase_price_rub,
            duties_rub,
            utilization_fee_rub,
            customs_services_rub,
            era_glonass_rub,
            freight_rub,
            country_expenses_rub,
            commission_rub,
        ]
    )

    breakdown = CostBreakdown(
        purchase_price_rub=purchase_price_rub,
        duties_rub=duties_rub,
        utilization_fee_rub=utilization_fee_rub,
        customs_services_rub=customs_services_rub,
        era_glonass_rub=era_glonass_rub,
        freight_rub=freight_rub,
        country_expenses_rub=country_expenses_rub,
        company_commission_rub=commission_rub,
        total_rub=total_rub,
    )

    meta = CalculationMeta(
        age_years=age_years,
        age_category=age_category,
        volume_band=volume_band,
        passing_category=passing_category,
        warnings=warnings,
    )

    return CalculationResult(request=req, meta=meta, breakdown=breakdown)
