from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter

from app.calculation.engine import calculate
from app.calculation.models import CalculationRequest, CalculationResult
from app.calculation.tariff_tables import get_passing_category
from app.core.settings import get_configs
from app.services.cbr import get_effective_rates


router = APIRouter(prefix="/api")


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/calculate", response_model=CalculationResult)
async def calculate_endpoint(payload: CalculationRequest) -> CalculationResult:
    return calculate(payload)


@router.get("/rates")
async def get_rates() -> dict[str, object]:
    """Return current currency rates, commissions thresholds, utilization coefficients,
    duties table and other numeric tariff data for the frontend.
    Structure is intentionally verbose but stable for WebApp consumption.
    """
    cfg = get_configs()
    rates_conf = cfg.rates
    duties_conf = cfg.duties
    commissions_conf = cfg.commissions
    fees_conf = cfg.fees

    # Extract Japan tiers explicitly (they are price-based expense tiers in purchase currency)
    japan_fees = fees_conf.get("japan", {})
    japan_currency = japan_fees.get("country_currency", "JPY")
    japan_tiers = [
        {"max_price": t.get("max_price"), "expenses": t.get("expenses"), "currency": japan_currency}
        for t in japan_fees.get("tiers", [])
    ]

    effective_rates = get_effective_rates(rates_conf)
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "currencies": effective_rates.get("currencies", {}),
        "live_source": effective_rates.get("live_source"),
        "commissions": commissions_conf.get("thresholds", []),
        "utilization": rates_conf.get("utilization", {}),
        "duties": duties_conf.get("age_categories", {}),  # pass-through bands
        "customs_services": rates_conf.get("customs_services", {}),
        "era_glonass_rub": rates_conf.get("era_glonass_rub"),
        "japan_expense_tiers": japan_tiers,
    }


@router.get("/meta")
async def get_meta() -> dict[str, object]:
    """Return reference metadata (countries, freight types, constraints, age categories)."""
    cfg = get_configs()
    fees_conf = cfg.fees
    rates_conf = cfg.rates

    current_year = datetime.now(UTC).year

    # Collect countries meta
    country_labels: dict[str, tuple[str, str]] = {
        "japan": ("Япония", "🇯🇵"),
        "korea": ("Корея", "🇰🇷"),
        "uae": ("ОАЭ", "🇦🇪"),
        "china": ("Китай", "🇨🇳"),
    }

    countries: list[dict[str, object]] = []
    for code, data in fees_conf.items():
        label, emoji = country_labels.get(code, (code.title(), ""))
        freight_types = list((data.get("freight") or {}).keys())
        if not freight_types:
            # Provide at least one placeholder if absent
            freight_types = []
        entry = {
            "code": code,
            "label": label,
            "emoji": emoji,
            "purchase_currency": data.get("country_currency"),
            "freight_types": freight_types,
            "has_price_tiers": bool(data.get("tiers")),
        }
        countries.append(entry)

    # Age categories mapping reused on frontend (pass / non-pass logic)
    age_categories = [
        {"code": "lt3", "label": "< 3 лет", "passing": get_passing_category("lt3") == "passing"},
        {"code": "3_5", "label": "3-5 лет", "passing": get_passing_category("3_5") == "passing"},
        {"code": "gt5", "label": "> 5 лет", "passing": get_passing_category("gt5") == "passing"},
    ]

    currencies_supported = sorted({c.split("_RUB")[0] for c in rates_conf.get("currencies", {})})

    freight_type_labels = {
        "standard": "Стандартный",
        "open": "Открытый",
        "container": "Контейнер",
    }

    constraints = {
        "min_year": 1990,
        "max_year": current_year,
        "max_engine_cc": 10000,
    }

    notes = [
        "3-5 лет = проходные. <3 и >5 = непроходные (для текущей логики пошлин).",
        "Для двигателей >2999 см³ утиль сбор может требовать уточнения.",
        "Если санкционный статус неизвестен — обращайтесь в поддержку.",
    ]

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "countries": countries,
        "age_categories": age_categories,
        "freight_type_labels": freight_type_labels,
        "currencies_supported": currencies_supported,
        "constraints": constraints,
        "notes": notes,
    }
