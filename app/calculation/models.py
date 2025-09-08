from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.core.messages import ERR_YEAR_FUTURE, ERR_YEAR_TOO_OLD


Country = Literal["japan", "korea", "uae", "china"]
FreightType = Literal["open", "container", "standard"]


class CalculationRequest(BaseModel):
    country: Country
    year: int
    engine_cc: int = Field(gt=0)
    purchase_price: Decimal = Field(gt=0)
    currency: str = Field(description="ISO currency code of purchase price, e.g. JPY USD CNY AED")
    freight_type: FreightType | None = None
    sanctions_unknown: bool = False

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


class CalculationMeta(BaseModel):
    age_years: int
    age_category: str
    volume_band: str
    passing_category: str
    duty_formula_mode: str | None = None
    eur_rate_used: str | None = None
    warnings: list[WarningItem] = Field(default_factory=list)


class CalculationResult(BaseModel):
    request: CalculationRequest
    meta: CalculationMeta
    breakdown: CostBreakdown


# Explicit rebuild to avoid Pydantic lazy resolution issues under some import orders
CalculationRequest.model_rebuild()
CostBreakdown.model_rebuild()
WarningItem.model_rebuild()
CalculationMeta.model_rebuild()
CalculationResult.model_rebuild()
