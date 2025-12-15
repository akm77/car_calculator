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


def test_get_meta_engine_power_constraints(client: TestClient) -> None:
    """
    Проверка наличия constraints для engine_power_hp в /api/meta.
    SPRINT 5: Добавлены engine_power_hp_min/max и conversion_factors.
    """
    response = client.get("/api/meta")
    assert response.status_code == 200

    data = response.json()

    # Проверка constraints
    assert "constraints" in data
    constraints = data["constraints"]

    # NEW: Проверка engine_power_hp
    assert "engine_power_hp_min" in constraints
    assert "engine_power_hp_max" in constraints
    assert constraints["engine_power_hp_min"] == 1
    assert constraints["engine_power_hp_max"] == 1500

    # NEW: Проверка conversion_factors
    assert "conversion_factors" in data
    factors = data["conversion_factors"]
    assert "hp_to_kw" in factors
    assert "kw_to_hp" in factors
    assert factors["hp_to_kw"] == 0.7355
    assert factors["kw_to_hp"] == 1.35962


def test_get_meta_backward_compatibility(client: TestClient) -> None:
    """
    Убедиться, что старые поля не удалены (backward compatibility).
    SPRINT 5: Гарантия стабильности API для старых клиентов.
    """
    response = client.get("/api/meta")
    data = response.json()

    # Старые обязательные поля должны присутствовать
    assert "countries" in data
    assert "constraints" in data
    assert "currencies_supported" in data

    # Проверка старых constraints
    constraints = data["constraints"]
    assert "min_year" in constraints
    assert "max_year" in constraints
    assert "max_engine_cc" in constraints
    assert constraints["max_engine_cc"] == 10000

    # Проверка других метаданных
    assert "age_categories" in data
    assert "freight_type_labels" in data
    assert len(data["age_categories"]) == 3  # lt3, 3_5, gt5


def test_meta_notes_include_commission_info(client: TestClient) -> None:
    """Meta notes should contain information about commission policy (regression)."""
    response = client.get("/api/meta")
    assert response.status_code == 200
    data = response.json()

    notes = data.get("notes") or []
    # At least one note should mention commission explicitly (Russian or English spelling).
    joined = " ".join(str(n) for n in notes).lower()
    assert "комисс" in joined or "commission" in joined


def test_calculate_japan_basic(client: TestClient) -> None:
    """
    Basic calculation test for Japan with engine_power_hp field.
    Updated for SPRINT 5: engine_power_hp now required.
    """
    current_year = datetime.now(UTC).year
    # Ensure age falls into 3-5 years category for duty bands stability
    year = current_year - 4 if current_year - 4 >= 1990 else 2021
    payload = {
        "country": "japan",
        "year": year,
        "engine_cc": 1500,
        "engine_power_hp": 150,  # NEW: Required field since utilization_2025.yml
        "purchase_price": 2_000_000,  # JPY
        "currency": "JPY",
        "freight_type": "standard",
    }
    r = client.post("/api/calculate", json=payload)
    assert r.status_code == 200, r.text
    data = r.json()

    # Validate structure
    assert "breakdown" in data
    assert "meta" in data
    assert "request" in data

    breakdown = data["breakdown"]
    meta = data["meta"]

    # Check all breakdown fields are present and positive
    required_fields = [
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
    for field in required_fields:
        assert field in breakdown
        assert breakdown[field] >= 0

    # Basic sanity checks (values > 0 for most fields)
    assert breakdown["purchase_price_rub"] > 0
    assert breakdown["duties_rub"] > 0
    assert breakdown["total_rub"] > breakdown["purchase_price_rub"]

    # Check meta includes engine_power info (new in 2025 spec)
    assert "engine_power_hp" in meta
    assert meta["engine_power_hp"] == 150
    assert "engine_power_kw" in meta
    assert meta["engine_power_kw"] > 0  # Should be ~110 kW (150 * 0.7355)
