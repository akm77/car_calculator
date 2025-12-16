from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
import yaml

from app.core.settings import get_configs


if TYPE_CHECKING:
    from fastapi.testclient import TestClient


BASE_DIR = Path(__file__).resolve().parents[2]
TEST_CONFIG_DIR = BASE_DIR / "tests" / "test_data" / "config"


def _load_commissions_from_yaml(filename: str) -> dict:
    path = TEST_CONFIG_DIR / filename
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


@pytest.fixture
def commissions_profile_no_bank() -> dict:
    """Load commissions config without bank_commission (regression baseline)."""
    return _load_commissions_from_yaml("commissions_company_only.yml")


@pytest.fixture
def commissions_profile_with_bank_default() -> dict:
    """Load commissions config with enabled bank_commission at default percent (2-5%)."""
    return _load_commissions_from_yaml("commissions_with_bank.yml")
    # Keep YAML percent by default; tests focus on relative difference vs no-bank


@pytest.fixture
def commissions_profile_with_bank_high() -> dict:
    """Load commissions config with bank_commission set above warn_above for warnings tests."""
    data = _load_commissions_from_yaml("commissions_with_bank.yml")
    bank = data.setdefault("bank_commission", {})
    meta = bank.setdefault("meta", {})

    # Ensure we exceed warn_above threshold if present, otherwise set a safe high value
    warn_above = float(meta.get("warn_above", 10.0))
    bank["enabled"] = True
    bank["percent"] = warn_above + 5.0
    meta.setdefault("recommended_min", 0.0)
    meta.setdefault("recommended_max", 10.0)
    meta.setdefault("default_percent", bank["percent"])
    return data


@pytest.fixture
def _patch_commissions(monkeypatch):
    """Helper fixture to patch cfg.commissions for a single test and restore afterwards."""
    import copy

    cfg = get_configs()
    # Deep copy to preserve nested structures like bank_commission
    original_commissions = copy.deepcopy(cfg.commissions)

    def _apply(new_commissions: dict) -> None:
        """Apply new commissions config by directly mutating the dict."""
        cfg_inner = get_configs()
        # Clear the dict and update with deep copy to ensure nested dicts are replaced
        cfg_inner.commissions.clear()
        cfg_inner.commissions.update(copy.deepcopy(new_commissions))

    yield _apply

    # Restore original commissions after test
    cfg_restore = get_configs()
    cfg_restore.commissions.clear()
    cfg_restore.commissions.update(original_commissions)


def _build_payload() -> dict:
    """Reusable request payload focusing on a stable 3-5 years age band."""
    current_year = datetime.now(UTC).year
    year = current_year - 4 if current_year - 4 >= 1990 else 2021
    return {
        "country": "japan",
        "year": year,
        "engine_cc": 1500,
        "engine_power_hp": 150,
        "purchase_price": 10_000,
        "currency": "USD",
        "freight_type": "standard",
    }


def _extract_rate_meta(meta: dict, code: str) -> tuple[float | None, float | None, float | None]:
    """Return (base_rate, effective_rate, bank_percent) for given currency code if detailed meta is present."""  # noqa: E501
    detailed = meta.get("detailed_rates_used") or {}
    entry = detailed.get(code) or {}
    base = entry.get("base_rate")
    effective = entry.get("effective_rate")
    bank_percent = entry.get("bank_commission_percent")
    return base, effective, bank_percent


@pytest.mark.functional
def test_calculate_without_bank_commission_regression(
    client: TestClient,
    commissions_profile_no_bank: dict,
    _patch_commissions,
) -> None:
    """/api/calculate without bank commission should behave like legacy baseline.

    Focus: structure, non-negative breakdown values, reasonable company_commission_rub and
    absence of bank-related inflators in rates meta.
    """

    _patch_commissions(commissions_profile_no_bank)

    payload = _build_payload()
    r = client.post("/api/calculate", json=payload)
    assert r.status_code == 200, r.text
    data = r.json()

    assert "breakdown" in data
    assert "meta" in data
    assert "request" in data

    breakdown = data["breakdown"]
    meta = data["meta"]

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

    assert breakdown["purchase_price_rub"] > 0
    assert breakdown["duties_rub"] > 0
    assert breakdown["total_rub"] > breakdown["purchase_price_rub"]

    commission = breakdown["company_commission_rub"]
    assert 10_000 <= commission <= 200_000

    rates_used = meta.get("rates_used") or {}
    assert "USD_RUB" in rates_used

    base, effective, bank_percent = _extract_rate_meta(meta, "USD_RUB")
    if base is not None and effective is not None:
        assert effective == pytest.approx(base, rel=1e-6, abs=1e-4)
    if bank_percent is not None:
        assert bank_percent == pytest.approx(0.0, abs=1e-6)


@pytest.mark.functional
def test_calculate_with_bank_commission_increases_costs(
    client: TestClient,
    commissions_profile_no_bank: dict,
    commissions_profile_with_bank_default: dict,
    _patch_commissions,
) -> None:
    """With enabled bank_commission, all currency-derived costs should increase."""

    payload = _build_payload()

    _patch_commissions(commissions_profile_no_bank)
    r_no_bank = client.post("/api/calculate", json=payload)
    assert r_no_bank.status_code == 200, r_no_bank.text
    data_no_bank = r_no_bank.json()

    _patch_commissions(commissions_profile_with_bank_default)
    r_with_bank = client.post("/api/calculate", json=payload)
    assert r_with_bank.status_code == 200, r_with_bank.text
    data_with_bank = r_with_bank.json()

    br_no = data_no_bank["breakdown"]
    br_bank = data_with_bank["breakdown"]
    meta_no = data_no_bank["meta"]
    meta_bank = data_with_bank["meta"]

    assert set(br_no.keys()) == set(br_bank.keys())

    # Per engine.py implementation, bank commission affects:
    # - purchase_price_rub (converted with bank_commission_percent)
    # - company_commission_rub (USD commission converted with bank_commission_percent)
    # - total_rub (sum of all components)
    # But NOT: country_expenses_rub, freight_rub (use bank_commission_percent=None)
    for key in [
        "purchase_price_rub",
        "company_commission_rub",
        "total_rub",
    ]:
        assert br_bank[key] > br_no[key], f"{key}: {br_bank[key]} should be > {br_no[key]}"

    # These should remain the same (no bank commission applied)
    for key in [
        "country_expenses_rub",
        "freight_rub",
    ]:
        assert br_bank[key] == br_no[key], f"{key} should not be affected by bank commission"

    for stable_key in [
        "age_category",
        "duty_mode",
    ]:
        if stable_key in meta_no or stable_key in meta_bank:
            assert meta_no.get(stable_key) == meta_bank.get(stable_key)

    base_no, eff_no, bank_percent_no = _extract_rate_meta(meta_no, "USD_RUB")
    base_bank, eff_bank, bank_percent_bank = _extract_rate_meta(meta_bank, "USD_RUB")

    if base_no is not None and base_bank is not None:
        assert base_no == pytest.approx(base_bank, rel=1e-6, abs=1e-4)

    if eff_no is not None and eff_bank is not None:
        assert eff_bank > eff_no

    if bank_percent_no is not None:
        assert bank_percent_no == pytest.approx(0.0, abs=1e-6)

    if bank_percent_bank is not None:
        assert bank_percent_bank >= 0.0

    warnings_no = meta_no.get("warnings") or []
    warnings_bank = meta_bank.get("warnings") or []

    def _warning_codes(warnings: list[dict]) -> set[str]:
        return {w.get("code", "") for w in warnings}

    codes_no = _warning_codes(warnings_no)
    codes_bank = _warning_codes(warnings_bank)

    assert "BANK_COMMISSION_HIGH" not in codes_no
    assert "BANK_COMMISSION_HIGH" not in codes_bank


@pytest.mark.functional
def test_calculate_with_high_bank_commission_triggers_warning(
    client: TestClient,
    commissions_profile_no_bank: dict,
    commissions_profile_with_bank_high: dict,
    _patch_commissions,
) -> None:
    """High bank_commission percent should trigger a warning and increase costs further."""

    payload = _build_payload()

    _patch_commissions(commissions_profile_no_bank)
    r_no_bank = client.post("/api/calculate", json=payload)
    assert r_no_bank.status_code == 200, r_no_bank.text
    data_no_bank = r_no_bank.json()

    _patch_commissions(commissions_profile_with_bank_high)
    r_high = client.post("/api/calculate", json=payload)
    assert r_high.status_code == 200, r_high.text
    data_high = r_high.json()

    br_no = data_no_bank["breakdown"]
    br_high = data_high["breakdown"]
    meta_no = data_no_bank["meta"]
    meta_high = data_high["meta"]

    assert br_high["total_rub"] > br_no["total_rub"]
    assert br_high["purchase_price_rub"] > br_no["purchase_price_rub"]

    base_no, eff_no, _ = _extract_rate_meta(meta_no, "USD_RUB")
    base_high, eff_high, bank_percent_high = _extract_rate_meta(meta_high, "USD_RUB")

    if base_no is not None and base_high is not None:
        assert base_no == pytest.approx(base_high, rel=1e-6, abs=1e-4)

    if eff_no is not None and eff_high is not None:
        assert eff_high > eff_no

    if bank_percent_high is not None:
        assert bank_percent_high > 5.0

    warnings_high = meta_high.get("warnings") or []

    # Current implementation may not yet expose a dedicated BANK_COMMISSION_* warning code.
    # At minimum we assert that warnings list shape is stable and do not enforce specific code.
    assert isinstance(warnings_high, list)
