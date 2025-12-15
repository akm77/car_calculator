from decimal import Decimal

from app.calculation.engine import calculate
from app.calculation.models import CalculationRequest


def test_detailed_rates_used_and_meta_rates_used_display_no_commission():
    """When bank_commission is effectively 0, display string has no '+ X%'.

    This relies on default commissions config where bank_commission is disabled
    or percent is zero.
    """
    req = CalculationRequest(
        country="japan",
        year=2022,
        engine_cc=1500,
        engine_power_hp=110,
        purchase_price=Decimal("1000000"),
        currency="JPY",
        freight_type="standard",
    )

    result = calculate(req)
    meta = result.meta

    # detailed_rates_used should contain entries for JPY and EUR at least
    assert "JPY" in meta.detailed_rates_used
    jpy_rate = meta.detailed_rates_used["JPY"]

    assert jpy_rate.base_rate > 0
    assert jpy_rate.effective_rate > 0
    # With zero commission, base and effective should be equal numerically
    assert jpy_rate.bank_commission_percent == 0.0
    assert jpy_rate.effective_rate == jpy_rate.base_rate

    # Display string format: "JPY/RUB = <base>" (no + X%)
    assert jpy_rate.display.startswith("JPY/RUB = ")
    assert "+" not in jpy_rate.display

    # Legacy meta.rates_used should still have numeric base rate under key JPY_RUB
    assert "JPY_RUB" in meta.rates_used
    assert isinstance(meta.rates_used["JPY_RUB"], float)


def test_detailed_rates_used_display_with_positive_commission(monkeypatch):
    """When bank_commission.percent > 0, display must contain '+ X%'."""
    from app.core.settings import get_configs as real_get_configs
    import app.calculation.engine as engine_module

    base_configs = real_get_configs()

    # Force bank_commission.enabled=True, percent=3.0 in effective configs
    def _fake_get_configs():  # type: ignore[override]
        cfg = base_configs
        commissions = dict(cfg.commissions)
        commissions["bank_commission"] = {"enabled": True, "percent": 3.0}
        cfg.commissions = commissions
        return cfg

    # Patch the symbol used inside calculate()
    monkeypatch.setattr(engine_module, "get_configs", _fake_get_configs)

    req = CalculationRequest(
        country="korea",
        year=2022,
        engine_cc=1600,
        engine_power_hp=120,
        purchase_price=Decimal("20000"),
        currency="USD",
        freight_type="standard",
    )

    result = calculate(req)
    meta = result.meta

    # For this request we must at least use USD and EUR
    assert "USD" in meta.detailed_rates_used
    usd_rate = meta.detailed_rates_used["USD"]

    assert usd_rate.base_rate > 0
    # effective_rate может уже быть равен base_rate, если effective_rates
    # ранее включили надбавку; для нас важно, что комиссия зафиксирована
    assert usd_rate.bank_commission_percent == 3.0

    # Display string формат: "USD/RUB = <base> + 3%"
    assert usd_rate.display.startswith("USD/RUB = ")
    assert "+ 3%" in usd_rate.display

    # Legacy numeric rate is still present for backward compatibility
    assert "USD_RUB" in meta.rates_used
    assert isinstance(meta.rates_used["USD_RUB"], float)
