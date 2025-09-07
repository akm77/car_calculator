from __future__ import annotations

from datetime import UTC, datetime
import math
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient
import pytest
import yaml

from app.main import app


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_FILE = BASE_DIR / "tests" / "test_data" / "cases.yml"


def _load_cases() -> list[dict[str, Any]]:
    data = yaml.safe_load(DATA_FILE.read_text(encoding="utf-8")) or {}
    return data.get("cases", [])


CASES = _load_cases()


@pytest.mark.parametrize("case", CASES, ids=[c.get("name", str(i)) for i, c in enumerate(CASES)])
def test_calculation_cases(case: dict[str, Any]):
    client = TestClient(app)
    current_year = datetime.now(UTC).year
    req_payload = dict(case["request"])  # copy
    if "year" not in req_payload:
        age_offset = int(case.get("age_offset", 1))
        req_payload["year"] = current_year - age_offset

    r = client.post("/api/calculate", json=req_payload)
    assert r.status_code == 200, r.text
    data = r.json()

    expected = case["expected"]
    meta = data["meta"]
    breakdown = data["breakdown"]

    assert meta["age_category"] == expected["age_category"]

    # Helper for numeric comparison with tolerance
    def approx(key: str, rel_tol=0.0001, abs_tol=2.0):  # allow minor float drift
        exp = float(expected[key])
        got = float(breakdown[key])
        if not math.isclose(got, exp, rel_tol=rel_tol, abs_tol=abs_tol):
            raise AssertionError(f"Mismatch {key}: expected {exp}, got {got}")

    numeric_keys = [
        "purchase_price_rub",
        "duties_rub",
        "utilization_fee_rub",
        "customs_services_rub",
        "era_glonass_rub",
        "freight_rub",
        "country_expenses_rub",
        "company_commission_rub",
        "total_rub",
    ]
    for k in numeric_keys:
        approx(k)
