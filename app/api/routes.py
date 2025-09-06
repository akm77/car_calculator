from __future__ import annotations

from fastapi import APIRouter

from app.calculation.engine import calculate
from app.calculation.models import CalculationRequest, CalculationResult


router = APIRouter(prefix="/api")


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/calculate", response_model=CalculationResult)
async def calculate_endpoint(payload: CalculationRequest) -> CalculationResult:
    return calculate(payload)
