from decimal import Decimal

from app.calculation.engine import (
    _effective_currency_rate,
    _get_bank_commission_percent,
    calculate,
)
from app.calculation.models import CalculationRequest
from app.core import settings as core_settings


def _make_commissions_conf(section: dict | None) -> dict:
    if section is None:
        return {}
    return {"bank_commission": section}


def test_get_bank_commission_percent_missing_section_returns_zero():
    assert _get_bank_commission_percent({}) == 0.0


def test_get_bank_commission_percent_disabled_returns_zero():
    conf = _make_commissions_conf({"enabled": False, "percent": 5})
    assert _get_bank_commission_percent(conf) == 0.0


def test_get_bank_commission_percent_uses_default_when_percent_missing():
    conf = _make_commissions_conf({"meta": {"default_percent": 1.5}})
    assert _get_bank_commission_percent(conf) == 1.5


def test_get_bank_commission_percent_falls_back_to_zero_on_bad_default():
    conf = _make_commissions_conf({"meta": {"default_percent": "bad"}})
    assert _get_bank_commission_percent(conf) == 0.0


def test_get_bank_commission_percent_uses_explicit_percent():
    conf = _make_commissions_conf({"enabled": True, "percent": 2.5})
    assert _get_bank_commission_percent(conf) == 2.5


def test_effective_currency_rate_zero_percent_equals_base_rate():
    rates_conf = {"currencies": {"USD_RUB": "90.0"}}
    base = _effective_currency_rate(rates_conf, "USD", 0.0)
    assert base == Decimal("90.0")


def test_effective_currency_rate_positive_percent_increases_rate():
    rates_conf = {"currencies": {"USD_RUB": "100.0"}}
    effective = _effective_currency_rate(rates_conf, "USD", 2.0)
    # 100 * (1 + 2/100) = 102, with quantize4
    assert effective == Decimal("102.0000")


def test_effective_currency_rate_handles_lowercase_currency_code():
    rates_conf = {"currencies": {"USD_RUB": "80.0"}}
    effective = _effective_currency_rate(rates_conf, "usd", 1.0)
    assert effective == Decimal("80.8000")


def test_total_rub_is_monotonic_with_respect_to_bank_commission(monkeypatch):
    """total_rub should not decrease when bank_commission.percent grows.

    We run the same CalculationRequest with three different commissions configs:
    - no bank_commission section (implicit 0%)
    - bank_commission enabled with percent=0
    - bank_commission enabled with percent>0
    and assert total_rub(0%) == total_rub(enabled=false) and
    total_rub(percent>0) >= total_rub(0%).
    """

    # Prepare a simple, deterministic request (values chosen to stay within tables)
    req = CalculationRequest(
        country="japan",
        year=2020,
        purchase_price=1_500_000,
        currency="JPY",
        engine_cc=1500,
        engine_power_hp=110,
        freight_type=None,
        sanctions_unknown=False,
    )

    base_configs = core_settings.get_configs()

    def _run_with_commissions(commissions_section: dict | None) -> Decimal:
        # Create a shallow copy of the commissions dict to avoid mutating
        commissions_copy = dict(base_configs.commissions)
        if commissions_section is None:
            commissions_copy.pop("bank_commission", None)
        else:
            commissions_copy["bank_commission"] = commissions_section

        # Patch get_configs to return the same configs object but with overridden commissions
        def _fake_get_configs():  # type: ignore[override]
            base_configs.commissions = commissions_copy
            return base_configs

        monkeypatch.setattr(core_settings, "get_configs", _fake_get_configs)
        result = calculate(req)
        return Decimal(str(result.breakdown.total_rub))

    total_no_section = _run_with_commissions(None)
    total_zero = _run_with_commissions({"enabled": True, "percent": 0})
    total_positive = _run_with_commissions({"enabled": True, "percent": 1.0})

    # Invariants: no_section == zero, positive >= zero
    assert total_no_section == total_zero
    assert total_positive >= total_zero
