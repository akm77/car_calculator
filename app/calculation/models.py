from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal  # noqa: TC003
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.core.messages import ERR_YEAR_FUTURE, ERR_YEAR_TOO_OLD


Country = Literal["japan", "korea", "uae", "china", "georgia"]
FreightType = Literal["open", "container", "standard"]
VehicleType = Literal["M1", "pickup", "bus", "motorhome", "other"]


class CalculationRequest(BaseModel):
    country: Country
    year: int
    engine_cc: int = Field(gt=0, le=10000, description="Объём двигателя в см³")
    engine_power_hp: int = Field(gt=0, le=1500, description="Мощность двигателя в л.с.")
    purchase_price: Decimal = Field(gt=0)
    currency: str = Field(description="ISO currency code of purchase price, e.g. JPY USD CNY AED")
    freight_type: FreightType | None = None
    sanctions_unknown: bool = False
    vehicle_type: VehicleType = Field(default="M1")

    @field_validator("year")
    @classmethod
    def validate_year(cls, v: int) -> int:
        current_year = datetime.now(UTC).year
        if v > current_year:
            raise ValueError(ERR_YEAR_FUTURE)
        if v < 1990:
            raise ValueError(ERR_YEAR_TOO_OLD)
        return v

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, v: str) -> str:
        return v.upper().strip()


class CostBreakdown(BaseModel):
    purchase_price_rub: int
    duties_rub: int
    utilization_fee_rub: int
    customs_services_rub: int
    era_glonass_rub: int
    freight_rub: int
    country_expenses_rub: int
    company_commission_rub: int
    total_rub: int


class WarningItem(BaseModel):
    code: str
    message: str


class RateUsage(BaseModel):
    """Detailed information about currency rate usage in calculation.

    This extends the previous simple mapping `rates_used: dict[str, float]` to a
    richer structure that can hold base and effective rates together with
    applied bank commission percent and a human-readable display string.
    """

    base_rate: float
    effective_rate: float
    bank_commission_percent: float
    display: str


class CalculationMeta(BaseModel):
    age_years: int
    age_category: str
    volume_band: str
    passing_category: str
    duty_formula_mode: str | None = None
    eur_rate_used: str | None = None
    warnings: list[WarningItem] = Field(default_factory=list)
    # New: Detailed duty info for transparency
    customs_value_eur: float | None = None
    duty_percent: float | None = None
    duty_min_rate_eur_per_cc: float | None = None
    duty_rate_eur_per_cc: float | None = None
    duty_value_bracket_max_eur: float | None = None
    vehicle_type: VehicleType | None = None
    # New: Power and utilization fee info (2025 spec)
    engine_power_hp: int | None = None
    engine_power_kw: float | None = None
    utilization_coefficient: float | None = None
    # Old: Map of currency rates used in this calculation, preserved for
    # backward compatibility (keys like "USD_RUB": 90.0).
    rates_used: dict[str, float] = Field(default_factory=dict)
    # New: Detailed rates information per source currency code (e.g. "USD").
    detailed_rates_used: dict[str, RateUsage] = Field(default_factory=dict)


class CalculationResult(BaseModel):
    request: CalculationRequest
    meta: CalculationMeta
    breakdown: CostBreakdown


# Explicit rebuild to avoid Pydantic lazy resolution issues under some import orders
CalculationRequest.model_rebuild()
CostBreakdown.model_rebuild()
WarningItem.model_rebuild()
RateUsage.model_rebuild()
CalculationMeta.model_rebuild()
CalculationResult.model_rebuild()
