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


class TestRatesEndpoint:
    """Comprehensive tests for GET /api/rates."""

    def test_rates_structure(self, client: TestClient) -> None:
        """Проверка полной структуры ответа /api/rates."""
        response = client.get("/api/rates")
        assert response.status_code == 200

        data = response.json()

        # Required top-level fields
        required_fields = [
            "generated_at",
            "currencies",
            "commissions",
            "utilization",
            "duties",
            "customs_services",
            "era_glonass_rub",
            "japan_expense_tiers",
            "countries_active",
            "live_source",
        ]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"

    def test_rates_currencies_complete(self, client: TestClient) -> None:
        """Проверка наличия всех 5 валют."""
        response = client.get("/api/rates")
        assert response.status_code == 200

        currencies = response.json()["currencies"]

        required_currencies = ["USD_RUB", "EUR_RUB", "JPY_RUB", "CNY_RUB", "AED_RUB"]
        for curr in required_currencies:
            assert curr in currencies
            assert isinstance(currencies[curr], (int, float))
            assert currencies[curr] > 0

    def test_rates_commissions_structure(self, client: TestClient) -> None:
        """Проверка структуры комиссий."""
        response = client.get("/api/rates")
        assert response.status_code == 200

        data = response.json()

        # commissions can be list or dict
        if "commissions" in data:
            commissions = data["commissions"]
            assert isinstance(commissions, (list, dict))

    def test_rates_uae_zero_commission(self, client: TestClient) -> None:
        """ОАЭ: commission_usd = 0."""
        response = client.get("/api/rates")
        assert response.status_code == 200

        data = response.json()

        # Check commissions_by_country if present
        if "commissions_by_country" in data:
            commissions = data["commissions_by_country"]
            if "uae" in commissions:
                assert commissions["uae"]["commission_usd"] == 0

    def test_rates_customs_services_all_countries(self, client: TestClient) -> None:
        """customs_services содержит записи для всех стран."""
        response = client.get("/api/rates")
        assert response.status_code == 200

        customs_services = response.json()["customs_services"]

        expected_countries = ["japan", "korea", "uae", "china", "georgia"]
        for country in expected_countries:
            assert country in customs_services
            assert isinstance(customs_services[country], (int, float))
            assert customs_services[country] > 0

    def test_rates_era_glonass(self, client: TestClient) -> None:
        """era_glonass_rub = 45000 (базовая ставка)."""
        response = client.get("/api/rates")
        assert response.status_code == 200

        era_glonass = response.json()["era_glonass_rub"]
        assert era_glonass == 45000

    def test_rates_utilization_structure(self, client: TestClient) -> None:
        """Проверка структуры utilization."""
        response = client.get("/api/rates")
        assert response.status_code == 200

        utilization = response.json()["utilization"]

        # utilization should be present (may be empty dict or have data)
        assert isinstance(utilization, dict)

    def test_rates_duties_age_categories(self, client: TestClient) -> None:
        """Проверка наличия всех возрастных категорий в duties."""
        response = client.get("/api/rates")
        assert response.status_code == 200

        duties = response.json()["duties"]

        assert "lt3" in duties
        assert "3_5" in duties
        assert "gt5" in duties

    def test_rates_japan_expense_tiers(self, client: TestClient) -> None:
        """Проверка структуры japan_expense_tiers."""
        response = client.get("/api/rates")
        assert response.status_code == 200

        tiers = response.json()["japan_expense_tiers"]

        assert isinstance(tiers, list)
        if len(tiers) > 0:
            tier = tiers[0]
            assert "max_price" in tier
            assert "expenses" in tier
            assert "currency" in tier

    def test_rates_countries_active(self, client: TestClient) -> None:
        """Проверка списка активных стран."""
        response = client.get("/api/rates")
        assert response.status_code == 200

        countries = response.json()["countries_active"]

        assert isinstance(countries, list)
        expected_countries = {"japan", "korea", "uae", "china", "georgia"}
        assert expected_countries.issubset(set(countries))

    def test_rates_live_source(self, client: TestClient) -> None:
        """Проверка поля live_source."""
        response = client.get("/api/rates")
        assert response.status_code == 200

        live_source = response.json()["live_source"]
        assert live_source in ("static", "cbr", None)


class TestMetaEndpoint:
    """Comprehensive tests for GET /api/meta."""

    def test_meta_structure_complete(self, client: TestClient) -> None:
        """Проверка полной структуры ответа /api/meta."""
        response = client.get("/api/meta")
        assert response.status_code == 200

        data = response.json()

        required_fields = [
            "generated_at",
            "countries",
            "age_categories",
            "freight_type_labels",
            "currencies_supported",
            "constraints",
            "conversion_factors",
        ]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"

    def test_meta_countries_complete(self, client: TestClient) -> None:
        """countries содержит все 5 стран."""
        response = client.get("/api/meta")
        assert response.status_code == 200

        countries = response.json()["countries"]

        assert isinstance(countries, list)
        country_codes = {c["code"] for c in countries}
        expected = {"japan", "korea", "uae", "china", "georgia"}
        assert expected == country_codes

    def test_meta_countries_have_labels_and_emoji(self, client: TestClient) -> None:
        """Каждая страна имеет code, label, emoji."""
        response = client.get("/api/meta")
        assert response.status_code == 200

        countries = response.json()["countries"]

        for country in countries:
            assert "code" in country
            assert "label" in country
            assert "emoji" in country
            assert isinstance(country["code"], str)
            assert isinstance(country["label"], str)
            assert len(country["emoji"]) > 0

    def test_meta_age_categories_complete(self, client: TestClient) -> None:
        """age_categories содержит 3 категории."""
        response = client.get("/api/meta")
        assert response.status_code == 200

        age_categories = response.json()["age_categories"]

        assert isinstance(age_categories, list)
        assert len(age_categories) == 3

        codes = {cat["code"] for cat in age_categories}
        assert codes == {"lt3", "3_5", "gt5"}

    def test_meta_age_categories_have_labels(self, client: TestClient) -> None:
        """Каждая age_category имеет code и label."""
        response = client.get("/api/meta")
        assert response.status_code == 200

        age_categories = response.json()["age_categories"]

        for cat in age_categories:
            assert "code" in cat
            assert "label" in cat
            assert isinstance(cat["code"], str)
            assert isinstance(cat["label"], str)

    def test_meta_currencies_supported(self, client: TestClient) -> None:
        """currencies_supported содержит основные валюты."""
        response = client.get("/api/meta")
        assert response.status_code == 200

        currencies = response.json()["currencies_supported"]

        assert isinstance(currencies, list)
        # At least core currencies (excluding RUB which is the target currency)
        expected = {"USD", "EUR", "JPY", "CNY", "AED"}
        assert expected.issubset(set(currencies))

    def test_meta_constraints_year(self, client: TestClient) -> None:
        """constraints.year_max = текущий год (динамически)."""
        response = client.get("/api/meta")
        assert response.status_code == 200

        constraints = response.json()["constraints"]

        assert "min_year" in constraints
        assert "max_year" in constraints
        assert constraints["min_year"] == 1990
        assert constraints["max_year"] == datetime.now(UTC).year

    def test_meta_constraints_engine_power(self, client: TestClient) -> None:
        """constraints содержит engine_power_hp_min/max."""
        response = client.get("/api/meta")
        assert response.status_code == 200

        constraints = response.json()["constraints"]

        assert "engine_power_hp_min" in constraints
        assert "engine_power_hp_max" in constraints
        assert constraints["engine_power_hp_min"] == 1
        assert constraints["engine_power_hp_max"] == 1500

    def test_meta_conversion_factors(self, client: TestClient) -> None:
        """conversion_factors.hp_to_kw = 0.7355."""
        response = client.get("/api/meta")
        assert response.status_code == 200

        factors = response.json()["conversion_factors"]

        assert "hp_to_kw" in factors
        assert "kw_to_hp" in factors
        assert factors["hp_to_kw"] == 0.7355
        assert abs(factors["kw_to_hp"] - 1.35962) < 0.00001

    def test_meta_freight_type_labels(self, client: TestClient) -> None:
        """freight_type_labels содержит стандартные типы."""
        response = client.get("/api/meta")
        assert response.status_code == 200

        labels = response.json()["freight_type_labels"]

        assert isinstance(labels, dict)
        # At least some standard types
        expected_keys = {"standard", "open", "container"}
        assert expected_keys.issubset(set(labels.keys()))


class TestCalculateSuccessfulCases:
    """Тесты успешных расчётов для всех стран."""

    def test_calculate_japan_lt3_nonsanctioned(self, client: TestClient) -> None:
        """Япония, lt3, несанкционный → проверить структуру ответа."""
        current_year = datetime.now(UTC).year
        year = current_year - 1  # lt3

        payload = {
            "country": "japan",
            "year": year,
            "engine_cc": 2000,
            "engine_power_hp": 150,
            "purchase_price": 2000000,
            "currency": "JPY",
            "freight_type": "standard",
            "sanctions_unknown": False,
        }

        response = client.post("/api/calculate", json=payload)

        assert response.status_code == 200
        data = response.json()

        # Check structure
        assert "breakdown" in data
        assert "meta" in data
        assert "request" in data

        # Check all breakdown fields present
        breakdown = data["breakdown"]
        required_fields = [
            "purchase_price_rub",
            "country_expenses_rub",
            "freight_rub",
            "customs_services_rub",
            "duties_rub",
            "utilization_fee_rub",
            "era_glonass_rub",
            "company_commission_rub",
            "total_rub",
        ]
        for field in required_fields:
            assert field in breakdown

        # Check meta
        meta = data["meta"]
        assert meta["age_category"] == "lt3"
        assert "rates_used" in meta
        assert "detailed_rates_used" in meta
        assert "engine_power_hp" in meta
        assert "engine_power_kw" in meta

    def test_calculate_korea_3_5(self, client: TestClient) -> None:
        """Корея, 3_5 → проверить breakdown и meta."""
        current_year = datetime.now(UTC).year
        year = current_year - 4  # 3_5

        payload = {
            "country": "korea",
            "year": year,
            "engine_cc": 1800,
            "engine_power_hp": 140,
            "purchase_price": 15000,
            "currency": "USD",
            "freight_type": "standard",
        }

        response = client.post("/api/calculate", json=payload)

        assert response.status_code == 200
        data = response.json()

        assert data["meta"]["age_category"] == "3_5"
        assert data["breakdown"]["total_rub"] > 0

    def test_calculate_uae_gt5_container(self, client: TestClient) -> None:
        """ОАЭ, gt5, container → проверить, что commission_rub = 0."""
        current_year = datetime.now(UTC).year
        year = current_year - 7  # gt5

        if year < 1990:
            year = 1990

        payload = {
            "country": "uae",
            "year": year,
            "engine_cc": 3500,
            "engine_power_hp": 280,
            "purchase_price": 40000,
            "currency": "USD",
            "freight_type": "container",
        }

        response = client.post("/api/calculate", json=payload)

        assert response.status_code == 200
        data = response.json()

        # UAE should have zero company commission
        assert data["breakdown"]["company_commission_rub"] == 0

    def test_calculate_china_lt3_high_price(self, client: TestClient) -> None:
        """Китай, lt3, высокая стоимость."""
        current_year = datetime.now(UTC).year
        year = current_year - 1  # lt3

        payload = {
            "country": "china",
            "year": year,
            "engine_cc": 2500,
            "engine_power_hp": 200,
            "purchase_price": 50000,
            "currency": "USD",
            "freight_type": "standard",
        }

        response = client.post("/api/calculate", json=payload)

        assert response.status_code == 200
        data = response.json()

        assert data["breakdown"]["total_rub"] > 0
        assert data["meta"]["age_category"] == "lt3"

    def test_calculate_georgia_gt5(self, client: TestClient) -> None:
        """Грузия, gt5."""
        current_year = datetime.now(UTC).year
        year = current_year - 8  # gt5

        if year < 1990:
            year = 1995

        payload = {
            "country": "georgia",
            "year": year,
            "engine_cc": 2000,
            "engine_power_hp": 150,
            "purchase_price": 8000,
            "currency": "USD",
            "freight_type": "standard",
        }

        response = client.post("/api/calculate", json=payload)

        assert response.status_code == 200
        data = response.json()

        assert data["breakdown"]["total_rub"] > 0
        assert data["meta"]["age_category"] == "gt5"


class TestCalculateInvariants:
    """Тесты инвариантов для POST /api/calculate."""

    def test_total_equals_sum_of_components(self, client: TestClient) -> None:
        """total_rub = сумма всех компонентов."""
        payload = {
            "country": "japan",
            "year": 2020,
            "engine_cc": 2000,
            "engine_power_hp": 150,
            "purchase_price": 2000000,
            "currency": "JPY",
            "freight_type": "standard",
        }

        response = client.post("/api/calculate", json=payload)

        assert response.status_code == 200
        data = response.json()
        breakdown = data["breakdown"]

        calculated_total = (
            breakdown["purchase_price_rub"] +
            breakdown["country_expenses_rub"] +
            breakdown["freight_rub"] +
            breakdown["customs_services_rub"] +
            breakdown["duties_rub"] +
            breakdown["utilization_fee_rub"] +
            breakdown["era_glonass_rub"] +
            breakdown["company_commission_rub"]
        )

        assert breakdown["total_rub"] == calculated_total

    def test_engine_power_conversion_hp_to_kw(self, client: TestClient) -> None:
        """meta.engine_power_kw = meta.engine_power_hp × 0.7355."""
        payload = {
            "country": "japan",
            "year": 2020,
            "engine_cc": 2000,
            "engine_power_hp": 150,
            "purchase_price": 2000000,
            "currency": "JPY",
        }

        response = client.post("/api/calculate", json=payload)

        assert response.status_code == 200
        meta = response.json()["meta"]

        expected_kw = meta["engine_power_hp"] * 0.7355
        assert abs(meta["engine_power_kw"] - expected_kw) < 0.01

    def test_rates_used_contains_required_currencies(self, client: TestClient) -> None:
        """meta.rates_used содержит минимум основные валюты."""
        payload = {
            "country": "japan",
            "year": 2020,
            "engine_cc": 2000,
            "engine_power_hp": 150,
            "purchase_price": 2000000,
            "currency": "JPY",
        }

        response = client.post("/api/calculate", json=payload)

        assert response.status_code == 200
        meta = response.json()["meta"]

        rates_used = meta.get("rates_used", {})
        # Should contain at least USD, EUR, JPY
        assert any(key.startswith("USD") for key in rates_used)
        assert any(key.startswith("EUR") for key in rates_used)

    def test_detailed_rates_used_structure(self, client: TestClient) -> None:
        """meta.detailed_rates_used содержит правильную структуру."""
        payload = {
            "country": "japan",
            "year": 2020,
            "engine_cc": 2000,
            "engine_power_hp": 150,
            "purchase_price": 1000,
            "currency": "USD",
        }

        response = client.post("/api/calculate", json=payload)

        assert response.status_code == 200
        meta = response.json()["meta"]

        detailed = meta.get("detailed_rates_used", {})

        if "USD" in detailed:
            usd_detail = detailed["USD"]
            assert "base_rate" in usd_detail
            assert "effective_rate" in usd_detail
            assert "bank_commission_percent" in usd_detail
            assert "display" in usd_detail

            # effective_rate should be >= base_rate
            assert usd_detail["effective_rate"] >= usd_detail["base_rate"]


class TestHealthEndpoint:
    """Tests for GET /health."""

    def test_health_structure(self, client: TestClient) -> None:
        """Проверка структуры ответа /health."""
        response = client.get("/api/health")
        assert response.status_code == 200

        data = response.json()

        assert "status" in data
        assert data["status"] == "ok"
        assert "config_hash" in data
        assert "cbr_cache" in data

    def test_health_cbr_cache_structure(self, client: TestClient) -> None:
        """Проверка структуры cbr_cache в /health."""
        response = client.get("/api/health")
        assert response.status_code == 200

        cbr_cache = response.json()["cbr_cache"]

        assert "cached" in cbr_cache
        assert isinstance(cbr_cache["cached"], bool)


class TestRatesRefreshEndpoint:
    """Tests for POST /api/rates/refresh."""

    def test_refresh_rates_success(self, client: TestClient) -> None:
        """POST /api/rates/refresh без параметров → 200."""
        response = client.post("/api/rates/refresh")

        # Should return 200 even if cached
        assert response.status_code == 200

        data = response.json()
        assert "refreshed_at" in data or "cache" in data

    def test_refresh_rates_structure(self, client: TestClient) -> None:
        """Проверка структуры ответа /api/rates/refresh."""
        response = client.post("/api/rates/refresh")
        assert response.status_code == 200

        data = response.json()

        # Should have some result fields
        assert any(key in data for key in ["refreshed_at", "fetched_count", "cache", "status"])

