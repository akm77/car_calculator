from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.core.messages import (
    ERR_MISSING_CURRENCY_RATE,
    WARN_JAPAN_TIER_CURRENCY,
    WARN_NO_DUTY_RATE,
)
from app.core.settings import get_configs

from .models import CalculationMeta, CalculationRequest, CalculationResult, CostBreakdown
from .tariff_tables import (
    find_duty_rate,
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
) -> float:
    rate_eur_per_cc = find_duty_rate(duties_conf, age_category, engine_cc)
    if rate_eur_per_cc is None:
        warnings.append(WARN_NO_DUTY_RATE)
        return 0.0
    eur_rub = _currency_rate(rates_conf, "EUR")
    return engine_cc * rate_eur_per_cc * eur_rub


def _utilization_fee(age_category: str, rates_conf: dict[str, Any]) -> float:
    util = rates_conf.get("utilization", {})
    base_private = float(util.get("base_private", 20000))
    if age_category == "lt3":
        coef = float(util.get("coef_lt3", 0.17))
    elif age_category == "3_5":
        coef = float(util.get("coef_3_5", 0.26))
    else:
        coef = float(util.get("coef_gt5", util.get("coef_3_5", 0.26)))
    return base_private * coef


def _commission(amount_rub: float, commissions_conf: dict[str, Any]) -> float:
    thresholds = commissions_conf.get("thresholds", [])
    for th in thresholds:
        max_price = th.get("max_price")
        if max_price is None or amount_rub <= max_price:
            return float(th.get("amount", 0.0))
    return 0.0


def calculate(req: CalculationRequest) -> CalculationResult:
    configs = get_configs()
    rates_conf = configs.rates
    fees_conf = configs.fees.get(req.country, {})
    commissions_conf = configs.commissions
    duties_conf = configs.duties

    today = datetime.now(timezone.utc).date()
    age_years = today.year - req.year
    age_category = get_age_category(age_years)
    passing_category = get_passing_category(age_category)

    warnings: list[str] = []
    duties_rub = _compute_duty(req.engine_cc, age_category, duties_conf, rates_conf, warnings)
    volume_band = format_volume_band(duties_conf, age_category, req.engine_cc)

    purchase_price_rub = _convert(req.purchase_price, req.currency, rates_conf)

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

    # Customs services / SVH / etc.
    customs_services_map = rates_conf.get("customs_services", {})
    customs_services_rub = float(customs_services_map.get(req.country, 0))

    era_glonass_rub = float(rates_conf.get("era_glonass_rub", 35000))
    utilization_fee_rub = _utilization_fee(age_category, rates_conf)
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
