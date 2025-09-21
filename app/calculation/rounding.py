from __future__ import annotations

from collections.abc import Iterable, Mapping  # noqa: TC003
from decimal import ROUND_HALF_UP, Decimal, getcontext


# Centralized monetary rounding utilities
# Precision for internal Decimal context (high enough to avoid cascading rounding errors)
getcontext().prec = 28

RUBLE_QUANT = Decimal("1")  # integer rubles
FOUR_DEC_PLACES = Decimal("0.0001")
TWO_DEC_PLACES = Decimal("0.01")


def to_decimal(val: object) -> Decimal:
    if isinstance(val, Decimal):
        return val
    return Decimal(str(val))


def quantize4(val: Decimal | float | int) -> Decimal:
    return to_decimal(val).quantize(FOUR_DEC_PLACES)


def round_rub(val: Decimal | float | int) -> int:
    """Round monetary value to integer RUB using HALF_UP.
    Returns built-in int for JSON friendliness.
    """
    return int(to_decimal(val).quantize(RUBLE_QUANT, rounding=ROUND_HALF_UP))


def round_rub_map(data: Mapping[str, Decimal]) -> dict[str, int]:
    return {k: round_rub(v) for k, v in data.items()}


def sum_decimals(values: Iterable[Decimal]) -> Decimal:
    total = Decimal("0")
    for v in values:
        total += v
    return total
