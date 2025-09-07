from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from fastapi.testclient import TestClient


def test_rates_endpoint(client: TestClient) -> None:
    r = client.get("/api/rates")
    assert r.status_code == 200
    data = r.json()
    for key in [
        "generated_at",
        "currencies",
        "commissions",
        "utilization",
        "duties",
        "customs_services",
        "era_glonass_rub",
    ]:
        assert key in data
    assert "USD_RUB" in data["currencies"]
    assert isinstance(data["commissions"], list)


def test_meta_endpoint(client: TestClient) -> None:
    r = client.get("/api/meta")
    assert r.status_code == 200
    data = r.json()
    for key in [
        "generated_at",
        "countries",
        "age_categories",
        "freight_type_labels",
        "currencies_supported",
        "constraints",
    ]:
        assert key in data
    country_codes = {c["code"] for c in data["countries"]}
    assert {"japan", "korea", "uae", "china"}.issubset(country_codes)


def test_calculate_japan_basic(client: TestClient) -> None:
    current_year = datetime.now(UTC).year
    # Ensure age falls into 3-5 years category for duty bands stability
    year = current_year - 4 if current_year - 4 >= 1990 else 2021
    payload = {
        "country": "japan",
        "year": year,
        "engine_cc": 1500,
        "purchase_price": 2_000_000,  # JPY
        "currency": "JPY",
        "freight_type": "standard",
    }
    r = client.post("/api/calculate", json=payload)
    assert r.status_code == 200, r.text
    data = r.json()
    breakdown = data["breakdown"]
    # Deterministic expectations derived from static config
    # purchase_price_rub = 2_000_000 * 0.60 = 1_200_000
    assert abs(breakdown["purchase_price_rub"] - 1_200_000) < 1
    # duty: 1500cc * 1.7 * 100 (EUR_RUB) = 255_000
    assert abs(breakdown["duties_rub"] - 255_000) < 1
    # utilization fee base 20_000 * 0.26 = 5_200
    assert abs(breakdown["utilization_fee_rub"] - 5_200) < 0.5
    # customs services japan = 70_000
    assert abs(breakdown["customs_services_rub"] - 70_000) < 0.1
    # era glonass = 35_000
    assert abs(breakdown["era_glonass_rub"] - 35_000) < 0.1
    # freight 350 USD * 90 = 31_500
    assert abs(breakdown["freight_rub"] - 31_500) < 1
    # country expenses tier 150_000 JPY * 0.60 = 90_000
    assert abs(breakdown["country_expenses_rub"] - 90_000) < 1
    # commission threshold (<=1.5M) = 40_000
    assert abs(breakdown["company_commission_rub"] - 40_000) < 0.1
    # total sum check
    expected_total = 1_200_000 + 255_000 + 5_200 + 70_000 + 35_000 + 31_500 + 90_000 + 40_000
    assert abs(breakdown["total_rub"] - expected_total) < 2
