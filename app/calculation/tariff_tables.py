from __future__ import annotations

from typing import Any


# Helper functions to extract duty rates from loaded YAML config (duties.yml)


def get_age_category(age_years: int) -> str:
    if age_years < 3:
        return "lt3"
    if 3 <= age_years <= 5:
        return "3_5"
    return "gt5"


def get_passing_category(age_category: str) -> str:
    # Business meaning: 3-5 years are "проходные"
    return "passing" if age_category == "3_5" else "non_passing"


def find_duty_rate(
    duties_conf: dict[str, Any],
    age_category: str,
    engine_cc: int,
) -> float | None:
    if age_category not in duties_conf.get("age_categories", {}):
        return None
    bands = duties_conf["age_categories"][age_category].get("bands", [])
    for band in bands:
        max_cc = band.get("max_cc")
        if max_cc is None or engine_cc <= max_cc:
            return band.get("rate_eur_per_cc")  # type: ignore[no-any-return]
    return None


def format_volume_band(duties_conf: dict[str, Any], age_category: str, engine_cc: int) -> str:
    bands = duties_conf.get("age_categories", {}).get(age_category, {}).get("bands", [])
    for band in bands:
        max_cc = band.get("max_cc")
        rate = band.get("rate_eur_per_cc")
        if max_cc is None or engine_cc <= max_cc:
            upper = f"<= {max_cc}" if max_cc is not None else "> last"
            return f"{upper} @ {rate} €/cc"
    return "n/a"
