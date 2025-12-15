from decimal import Decimal

from app.calculation.engine import (
    _effective_currency_rate,
    _get_bank_commission_percent,
)


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

