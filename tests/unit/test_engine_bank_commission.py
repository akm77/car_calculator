from __future__ import annotations

from decimal import Decimal

import pytest

from app.calculation.engine import (
    _commission,
    _convert,
    _convert_from_rub,
    _effective_currency_rate,
    _get_bank_commission_percent,
    calculate,
)
from app.calculation.models import CalculationRequest
from app.core.settings import ConfigRegistry


# ---- Simple fixtures for pure helpers ---------------------------------------------------------


@pytest.fixture
def rates_conf_basic() -> dict:
    return {"currencies": {"USD_RUB": 90.0, "EUR_RUB": 100.0, "JPY_RUB": 0.5}}


@pytest.fixture
def commissions_conf_base() -> dict:
    return {
        "default_commission_usd": 1000,
        "by_country": {
            "uae": {"commission_usd": 0},
            "georgia": {"commission_usd": 750},
            "legacy": [{"amount": 50000}],
        },
    }


# ---- _get_bank_commission_percent -------------------------------------------------------------


class TestGetBankCommissionPercent:
    def test_no_section_returns_zero(self, commissions_conf_base: dict) -> None:
        assert _get_bank_commission_percent(commissions_conf_base) == 0.0

    def test_disabled_returns_zero(self, commissions_conf_base: dict) -> None:
        commissions_conf_base["bank_commission"] = {"enabled": False, "percent": 5.0}
        assert _get_bank_commission_percent(commissions_conf_base) == 0.0

    def test_percent_used_when_enabled(self, commissions_conf_base: dict) -> None:
        commissions_conf_base["bank_commission"] = {"enabled": True, "percent": 7.5}
        assert _get_bank_commission_percent(commissions_conf_base) == pytest.approx(7.5)

    def test_default_percent_used_when_percent_missing(self, commissions_conf_base: dict) -> None:
        commissions_conf_base["bank_commission"] = {
            "enabled": True,
            "meta": {"default_percent": 3.0},
        }
        assert _get_bank_commission_percent(commissions_conf_base) == pytest.approx(3.0)

    def test_invalid_percent_falls_back_to_zero(self, commissions_conf_base: dict) -> None:
        commissions_conf_base["bank_commission"] = {
            "enabled": True,
            "percent": "not-a-number",
            "meta": {"default_percent": "also-bad"},
        }
        assert _get_bank_commission_percent(commissions_conf_base) == 0.0


# ---- _effective_currency_rate -----------------------------------------------------------------


class TestEffectiveCurrencyRate:
    def test_zero_percent_uses_base_rate(self, rates_conf_basic: dict) -> None:
        rate = _effective_currency_rate(rates_conf_basic, "USD", 0.0)
        assert rate == Decimal("90") or rate == Decimal("90.0000")

    def test_positive_percent_increases_rate(self, rates_conf_basic: dict) -> None:
        rate = _effective_currency_rate(rates_conf_basic, "USD", 5.0)
        # 90 * 1.05 = 94.5
        assert rate == Decimal("94.5") or rate == Decimal("94.5000")

    def test_fractional_percent_precision(self, rates_conf_basic: dict) -> None:
        rate = _effective_currency_rate(rates_conf_basic, "USD", 2.5)
        # 90 * 1.025 = 92.25
        assert rate == Decimal("92.25") or rate == Decimal("92.2500")

    def test_different_currency(self, rates_conf_basic: dict) -> None:
        rate = _effective_currency_rate(rates_conf_basic, "EUR", 10.0)
        # 100 * 1.10 = 110
        assert rate == Decimal("110") or rate == Decimal("110.0000")


# ---- _convert and _convert_from_rub -----------------------------------------------------------


class TestConvertHelpers:
    def test_convert_without_commission_param_uses_base_rate(self, rates_conf_basic: dict) -> None:
        amount = Decimal("100")
        converted = _convert(amount, "USD", rates_conf_basic, bank_commission_percent=None)
        # 100 * 90 = 9000
        assert converted == Decimal("9000") or converted == Decimal("9000.0000")

    def test_convert_with_zero_percent_same_as_base(self, rates_conf_basic: dict) -> None:
        amount = Decimal("100")
        converted = _convert(amount, "USD", rates_conf_basic, bank_commission_percent=0.0)
        assert converted == Decimal("9000") or converted == Decimal("9000.0000")

    def test_convert_with_positive_percent(self, rates_conf_basic: dict) -> None:
        amount = Decimal("100")
        converted = _convert(amount, "USD", rates_conf_basic, bank_commission_percent=5.0)
        # 100 * 94.5 = 9450
        assert converted == Decimal("9450") or converted == Decimal("9450.0000")

    def test_convert_other_currency_with_percent(self, rates_conf_basic: dict) -> None:
        amount = Decimal("200")
        converted = _convert(amount, "EUR", rates_conf_basic, bank_commission_percent=10.0)
        # 200 * (100 * 1.1) = 22000
        assert converted == Decimal("22000") or converted == Decimal("22000.0000")

    def test_convert_from_rub_basic(self, rates_conf_basic: dict) -> None:
        amount_rub = Decimal("5000")
        # JPY_RUB = 0.5 -> 5000 / 0.5 = 10000
        converted = _convert_from_rub(amount_rub, "JPY", rates_conf_basic)
        assert converted == Decimal("10000") or converted == Decimal("10000.0000")

    def test_convert_from_rub_zero_rate_returns_zero(self) -> None:
        rates_conf = {"currencies": {"JPY_RUB": 0.0}}
        converted = _convert_from_rub(Decimal("1000"), "JPY", rates_conf)
        assert converted == Decimal("0") or converted == Decimal("0.0000")


# ---- _commission ------------------------------------------------------------------------------


class TestCompanyCommission:
    def test_default_commission_no_bank(self, commissions_conf_base: dict, rates_conf_basic: dict) -> None:
        # 1000 USD * 90 = 90000 RUB
        result = _commission(
            amount_rub=Decimal("0"),
            commissions_conf=commissions_conf_base,
            country="japan",
            rates_conf=rates_conf_basic,
            bank_commission_percent=None,
        )
        assert result > Decimal("80000")
        assert result < Decimal("100000")

    def test_default_commission_with_bank(self, commissions_conf_base: dict, rates_conf_basic: dict) -> None:
        # 1000 USD, 5% bank commission: effective_rate = 94.5 -> ~94500 RUB
        result = _commission(
            amount_rub=Decimal("0"),
            commissions_conf=commissions_conf_base,
            country="japan",
            rates_conf=rates_conf_basic,
            bank_commission_percent=5.0,
        )
        assert result > Decimal("90000")
        assert result < Decimal("100000")
        assert result > _commission(
            amount_rub=Decimal("0"),
            commissions_conf=commissions_conf_base,
            country="japan",
            rates_conf=rates_conf_basic,
            bank_commission_percent=None,
        )

    def test_uae_commission_zero_even_with_bank(self, commissions_conf_base: dict, rates_conf_basic: dict) -> None:
        result = _commission(
            amount_rub=Decimal("0"),
            commissions_conf=commissions_conf_base,
            country="uae",
            rates_conf=rates_conf_basic,
            bank_commission_percent=10.0,
        )
        assert result == Decimal("0")

    def test_country_override_commission_usd_respects_bank(self, commissions_conf_base: dict, rates_conf_basic: dict) -> None:
        # Georgia: 750 USD, 10% bank commission, USD_RUB=90 -> 750 * 99 = 74250
        result = _commission(
            amount_rub=Decimal("0"),
            commissions_conf=commissions_conf_base,
            country="georgia",
            rates_conf=rates_conf_basic,
            bank_commission_percent=10.0,
        )
        assert result > Decimal("65000")
        assert result < Decimal("80000")

    def test_legacy_rub_list_ignores_bank_commission(self, commissions_conf_base: dict) -> None:
        result_with_bank = _commission(
            amount_rub=Decimal("0"),
            commissions_conf=commissions_conf_base,
            country="legacy",
            rates_conf=None,
            bank_commission_percent=10.0,
        )
        result_without_bank = _commission(
            amount_rub=Decimal("0"),
            commissions_conf=commissions_conf_base,
            country="legacy",
            rates_conf=None,
            bank_commission_percent=None,
        )
        assert result_with_bank == result_without_bank == Decimal("50000")


# ---- calculate() scenarios with and without bank commission -----------------------------------


class TestCalculateWithBankCommission:
    def _make_request(self) -> CalculationRequest:
        return CalculationRequest(
            country="japan",
            year=2024,
            engine_cc=1500,
            engine_power_hp=110,
            purchase_price=Decimal("10000"),
            currency="USD",
        )

    def _patch_configs(self, monkeypatch: pytest.MonkeyPatch, percent: float | None) -> None:
        """Monkeypatch get_configs + get_effective_rates to use fixed configs.

        percent:
            None -> no bank_commission section
            0.0  -> enabled=True, percent=0.0
            >0   -> enabled=True, percent=<value>
        """

        from app.calculation import engine as engine_mod

        def fake_get_effective_rates(base_rates: dict) -> dict:
            # Ignore base_rates; always return fixed values
            return {
                "currencies": {
                    "USD_RUB": 90.0,
                    "EUR_RUB": 100.0,
                    "JPY_RUB": 0.5,
                },
                "live_source": None,
            }

        monkeypatch.setattr(engine_mod, "get_effective_rates", fake_get_effective_rates)

        real_get_configs = engine_mod.get_configs

        def fake_get_configs():
            cfgs = real_get_configs()
            commissions = dict(cfgs.commissions)
            if percent is None:
                commissions.pop("bank_commission", None)
            else:
                commissions["bank_commission"] = {"enabled": True, "percent": percent}
            # Preserve hash and loaded_at to satisfy ConfigRegistry validation
            return ConfigRegistry(
                duties=cfgs.duties,
                fees=cfgs.fees,
                commissions=commissions,
                rates=cfgs.rates,
                hash=cfgs.hash,
                loaded_at=cfgs.loaded_at,
            )

        monkeypatch.setattr(engine_mod, "get_configs", fake_get_configs)

    def test_total_without_bank_commission(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self._patch_configs(monkeypatch, percent=None)
        req = self._make_request()
        result = calculate(req)

        # Must use base USD_RUB rate without commission
        usd_usage = result.meta.detailed_rates_used["USD"]
        assert usd_usage.base_rate == pytest.approx(90.0)
        assert usd_usage.bank_commission_percent == pytest.approx(0.0)
        assert usd_usage.effective_rate == pytest.approx(90.0)

    def test_total_with_small_bank_commission(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # 5% bank commission
        self._patch_configs(monkeypatch, percent=5.0)
        req = self._make_request()
        result = calculate(req)

        usd_usage = result.meta.detailed_rates_used["USD"]
        assert usd_usage.base_rate == pytest.approx(90.0)
        assert usd_usage.bank_commission_percent == pytest.approx(5.0)
        assert usd_usage.effective_rate == pytest.approx(94.5, rel=1e-4)

    def test_total_grows_with_bank_commission(self, monkeypatch: pytest.MonkeyPatch) -> None:
        req = self._make_request()

        # 0% commission
        self._patch_configs(monkeypatch, percent=0.0)
        result0 = calculate(req)

        # 10% commission
        self._patch_configs(monkeypatch, percent=10.0)
        result10 = calculate(req)

        assert result10.breakdown.total_rub > result0.breakdown.total_rub

    def test_boundary_commission_levels(self, monkeypatch: pytest.MonkeyPatch) -> None:
        req = self._make_request()

        # 0%, 10%, 12.5%
        self._patch_configs(monkeypatch, percent=0.0)
        result0 = calculate(req)

        self._patch_configs(monkeypatch, percent=10.0)
        result10 = calculate(req)

        self._patch_configs(monkeypatch, percent=12.5)
        result125 = calculate(req)

        assert result0.breakdown.total_rub < result10.breakdown.total_rub < result125.breakdown.total_rub

    def test_uae_total_increases_but_company_commission_zero(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.calculation import engine as engine_mod

        # Use same fixed rates as above
        def fake_get_effective_rates(base_rates: dict) -> dict:
            return {
                "currencies": {"USD_RUB": 90.0, "EUR_RUB": 100.0, "JPY_RUB": 0.5},
                "live_source": None,
            }

        monkeypatch.setattr(engine_mod, "get_effective_rates", fake_get_effective_rates)
        real_get_configs = engine_mod.get_configs

        def fake_get_configs(percent: float):
            cfgs = real_get_configs()
            commissions = dict(cfgs.commissions)
            commissions["bank_commission"] = {"enabled": True, "percent": percent}
            # Preserve hash and loaded_at similarly to _patch_configs
            return ConfigRegistry(
                duties=cfgs.duties,
                fees=cfgs.fees,
                commissions=commissions,
                rates=cfgs.rates,
                hash=cfgs.hash,
                loaded_at=cfgs.loaded_at,
            )

        req = CalculationRequest(
            country="uae",
            year=2021,
            engine_cc=3000,
            engine_power_hp=250,
            purchase_price=Decimal("25000"),
            currency="USD",
        )

        # 0% bank commission
        monkeypatch.setattr(engine_mod, "get_configs", lambda: fake_get_configs(0.0))
        result0 = calculate(req)

        # 10% bank commission
        monkeypatch.setattr(engine_mod, "get_configs", lambda: fake_get_configs(10.0))
        result10 = calculate(req)

        assert result0.breakdown.company_commission_rub == Decimal("0")
        assert result10.breakdown.company_commission_rub == Decimal("0")
        assert result10.breakdown.total_rub > result0.breakdown.total_rub


class TestEffectiveCurrencyRateEdgeCases:
    def test_very_large_percent(self, rates_conf_basic: dict) -> None:
        """Even при очень большом процента effective_rate считается по той же формуле."""

        rate = _effective_currency_rate(rates_conf_basic, "USD", 250.0)
        # base 90 * (1 + 2.5) = 90 * 3.5 = 315.0
        assert rate == Decimal("315") or rate == Decimal("315.0000")

    def test_negative_percent_behaves_as_discount(self, rates_conf_basic: dict) -> None:
        """Отрицательный процент трактуется как скидка к курсу (зафиксировать поведение)."""

        rate = _effective_currency_rate(rates_conf_basic, "USD", -10.0)
        # base 90 * (1 - 0.1) = 81.0
        assert rate == Decimal("81") or rate == Decimal("81.0000")


class TestConvertUnknownCurrency:
    def test_unknown_currency_raises_calculation_error(self) -> None:
        """При отсутствии курса по валюте _convert должен пробрасывать CalculationError."""

        from app.calculation.engine import CalculationError

        rates_conf = {"currencies": {"USD_RUB": 90.0}}
        with pytest.raises(CalculationError):
            _convert(Decimal("1"), "XYZ", rates_conf, bank_commission_percent=5.0)
