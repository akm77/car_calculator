"""Юнит-тесты для CalculationMeta и вспомогательных типов."""

from __future__ import annotations

from pydantic import ValidationError
import pytest

from app.calculation.models import CalculationMeta, RateUsage, WarningItem


class TestWarningItem:
    """Тесты для модели WarningItem."""

    def test_warning_item_valid(self):
        """Создание валидного предупреждения."""
        warning = WarningItem(code="WARN_TEST", message="Test warning message")
        assert warning.code == "WARN_TEST"
        assert warning.message == "Test warning message"

    def test_warning_item_missing_code(self):
        """Отсутствие code — ошибка."""

        with pytest.raises(ValidationError) as exc_info:
            WarningItem(message="Test message")  # type: ignore
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("code",) for e in errors)

    def test_warning_item_missing_message(self):
        """Отсутствие message — ошибка."""

        with pytest.raises(ValidationError) as exc_info:
            WarningItem(code="WARN_TEST")  # type: ignore
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("message",) for e in errors)


class TestRateUsage:
    """Тесты для модели RateUsage."""

    def test_rate_usage_valid(self):
        """Создание валидной информации об использовании курса."""
        rate_usage = RateUsage(
            base_rate=90.0,
            effective_rate=91.8,
            bank_commission_percent=2.0,
            display="USD/RUB = 90.0 + 2.0%",
        )
        assert rate_usage.base_rate == 90.0
        assert rate_usage.effective_rate == 91.8
        assert rate_usage.bank_commission_percent == 2.0
        assert rate_usage.display == "USD/RUB = 90.0 + 2.0%"

    def test_rate_usage_no_commission(self):
        """Курс без банковской комиссии."""
        rate_usage = RateUsage(
            base_rate=90.0,
            effective_rate=90.0,
            bank_commission_percent=0.0,
            display="USD/RUB = 90.0",
        )
        assert rate_usage.base_rate == rate_usage.effective_rate
        assert rate_usage.bank_commission_percent == 0.0

    def test_rate_usage_high_commission(self):
        """Курс с высокой комиссией."""
        rate_usage = RateUsage(
            base_rate=100.0,
            effective_rate=105.0,
            bank_commission_percent=5.0,
            display="EUR/RUB = 100.0 + 5.0%",
        )
        assert rate_usage.effective_rate == 105.0
        assert rate_usage.bank_commission_percent == 5.0

    @pytest.mark.parametrize(
        "base,percent,expected_effective",
        [
            (90.0, 2.0, 91.8),
            (100.0, 3.0, 103.0),
            (85.5, 1.5, 86.7825),
            (120.0, 0.0, 120.0),
        ],
    )
    def test_rate_usage_commission_calculation(self, base, percent, expected_effective):
        """Проверка соответствия эффективного курса базовому + комиссия."""
        rate_usage = RateUsage(
            base_rate=base,
            effective_rate=expected_effective,
            bank_commission_percent=percent,
            display=f"TEST/RUB = {base} + {percent}%",
        )
        # Проверяем, что effective_rate близок к base_rate * (1 + percent/100)
        calculated = base * (1 + percent / 100)
        assert abs(rate_usage.effective_rate - calculated) < 0.01


class TestCalculationMeta:
    """Тесты для модели CalculationMeta."""

    def test_calculation_meta_minimal(self):
        """Минимальная валидная мета-информация."""
        meta = CalculationMeta(
            age_years=3,
            age_category="3_5",
            volume_band="2000-2500",
            passing_category="standard",
        )
        assert meta.age_years == 3
        assert meta.age_category == "3_5"
        assert meta.volume_band == "2000-2500"
        assert meta.passing_category == "standard"
        assert meta.warnings == []

    def test_calculation_meta_with_warnings(self):
        """Мета с предупреждениями."""
        warnings = [
            WarningItem(code="WARN_1", message="Warning 1"),
            WarningItem(code="WARN_2", message="Warning 2"),
        ]
        meta = CalculationMeta(
            age_years=5,
            age_category="gt5",
            volume_band="1500-2000",
            passing_category="standard",
            warnings=warnings,
        )
        assert len(meta.warnings) == 2
        assert meta.warnings[0].code == "WARN_1"
        assert meta.warnings[1].code == "WARN_2"

    def test_calculation_meta_age_category_lt3(self):
        """Категория возраста < 3 лет."""
        meta = CalculationMeta(
            age_years=2,
            age_category="lt3",
            volume_band="2000-2500",
            passing_category="standard",
        )
        assert meta.age_category == "lt3"

    def test_calculation_meta_age_category_3_5(self):
        """Категория возраста 3-5 лет."""
        meta = CalculationMeta(
            age_years=4,
            age_category="3_5",
            volume_band="2000-2500",
            passing_category="standard",
        )
        assert meta.age_category == "3_5"

    def test_calculation_meta_age_category_gt5(self):
        """Категория возраста > 5 лет."""
        meta = CalculationMeta(
            age_years=10,
            age_category="gt5",
            volume_band="2000-2500",
            passing_category="standard",
        )
        assert meta.age_category == "gt5"

    def test_calculation_meta_engine_power_conversion(self):
        """Конвертация мощности из л.с. в кВт."""
        # 100 л.с. = 73.55 кВт
        meta = CalculationMeta(
            age_years=3,
            age_category="3_5",
            volume_band="2000-2500",
            passing_category="standard",
            engine_power_hp=100,
            engine_power_kw=73.55,
        )
        assert meta.engine_power_hp == 100
        assert meta.engine_power_kw == 73.55

    @pytest.mark.parametrize(
        "hp,expected_kw",
        [
            (100, 73.55),
            (150, 110.325),
            (200, 147.1),
            (250, 183.875),
            (300, 220.65),
        ],
    )
    def test_calculation_meta_hp_to_kw_conversion(self, hp, expected_kw):
        """Проверка формулы конвертации: kW = hp × 0.7355."""
        meta = CalculationMeta(
            age_years=3,
            age_category="3_5",
            volume_band="2000-2500",
            passing_category="standard",
            engine_power_hp=hp,
            engine_power_kw=expected_kw,
        )
        # Проверяем, что engine_power_kw близко к hp * 0.7355
        calculated_kw = hp * 0.7355
        assert abs(meta.engine_power_kw - calculated_kw) < 0.01

    def test_calculation_meta_rates_used_structure(self):
        """Проверка структуры rates_used."""
        rates = {
            "USD_RUB": 90.0,
            "EUR_RUB": 100.0,
            "JPY_RUB": 0.8,
            "CNY_RUB": 12.5,
            "AED_RUB": 24.5,
        }
        meta = CalculationMeta(
            age_years=3,
            age_category="3_5",
            volume_band="2000-2500",
            passing_category="standard",
            rates_used=rates,
        )
        assert meta.rates_used == rates
        assert all(isinstance(v, (int, float)) for v in meta.rates_used.values())
        assert all(v > 0 for v in meta.rates_used.values())

    def test_calculation_meta_detailed_rates_used(self):
        """Проверка структуры detailed_rates_used."""
        detailed_rates = {
            "USD": RateUsage(
                base_rate=90.0,
                effective_rate=91.8,
                bank_commission_percent=2.0,
                display="USD/RUB = 90.0 + 2.0%",
            ),
            "EUR": RateUsage(
                base_rate=100.0,
                effective_rate=100.0,
                bank_commission_percent=0.0,
                display="EUR/RUB = 100.0",
            ),
        }
        meta = CalculationMeta(
            age_years=3,
            age_category="3_5",
            volume_band="2000-2500",
            passing_category="standard",
            detailed_rates_used=detailed_rates,
        )
        assert len(meta.detailed_rates_used) == 2
        assert "USD" in meta.detailed_rates_used
        assert "EUR" in meta.detailed_rates_used
        assert meta.detailed_rates_used["USD"].base_rate == 90.0
        assert meta.detailed_rates_used["USD"].effective_rate == 91.8
        assert meta.detailed_rates_used["EUR"].bank_commission_percent == 0.0

    def test_calculation_meta_detailed_rates_empty(self):
        """detailed_rates_used может быть пустым."""
        meta = CalculationMeta(
            age_years=3,
            age_category="3_5",
            volume_band="2000-2500",
            passing_category="standard",
        )
        assert meta.detailed_rates_used == {}

    def test_calculation_meta_customs_value_eur(self):
        """Проверка поля customs_value_eur."""
        meta = CalculationMeta(
            age_years=3,
            age_category="3_5",
            volume_band="2000-2500",
            passing_category="standard",
            customs_value_eur=15000.0,
        )
        assert meta.customs_value_eur == 15000.0

    def test_calculation_meta_duty_percent(self):
        """Проверка поля duty_percent."""
        meta = CalculationMeta(
            age_years=3,
            age_category="3_5",
            volume_band="2000-2500",
            passing_category="standard",
            duty_percent=15.0,
        )
        assert meta.duty_percent == 15.0

    def test_calculation_meta_duty_rate_eur_per_cc(self):
        """Проверка поля duty_rate_eur_per_cc."""
        meta = CalculationMeta(
            age_years=3,
            age_category="3_5",
            volume_band="2000-2500",
            passing_category="standard",
            duty_rate_eur_per_cc=3.5,
        )
        assert meta.duty_rate_eur_per_cc == 3.5

    def test_calculation_meta_utilization_coefficient(self):
        """Проверка поля utilization_coefficient."""
        meta = CalculationMeta(
            age_years=3,
            age_category="3_5",
            volume_band="2000-2500",
            passing_category="standard",
            utilization_coefficient=0.17,
        )
        assert meta.utilization_coefficient == 0.17

    def test_calculation_meta_vehicle_type(self):
        """Проверка поля vehicle_type."""
        meta = CalculationMeta(
            age_years=3,
            age_category="3_5",
            volume_band="2000-2500",
            passing_category="standard",
            vehicle_type="M1",
        )
        assert meta.vehicle_type == "M1"

    def test_calculation_meta_all_optional_fields(self):
        """Проверка всех опциональных полей вместе."""
        meta = CalculationMeta(
            age_years=5,
            age_category="gt5",
            volume_band="3000-3500",
            passing_category="premium",
            duty_formula_mode="hybrid",
            eur_rate_used="100.5",
            customs_value_eur=20000.0,
            duty_percent=20.0,
            duty_min_rate_eur_per_cc=2.0,
            duty_rate_eur_per_cc=4.0,
            duty_value_bracket_max_eur=30000.0,
            vehicle_type="pickup",
            engine_power_hp=250,
            engine_power_kw=183.875,
            utilization_coefficient=0.2,
            rates_used={"USD_RUB": 95.0},
            detailed_rates_used={
                "USD": RateUsage(
                    base_rate=95.0,
                    effective_rate=96.9,
                    bank_commission_percent=2.0,
                    display="USD/RUB = 95.0 + 2.0%",
                )
            },
            warnings=[WarningItem(code="WARN_TEST", message="Test warning")],
        )
        assert meta.duty_formula_mode == "hybrid"
        assert meta.eur_rate_used == "100.5"
        assert meta.customs_value_eur == 20000.0
        assert meta.duty_percent == 20.0
        assert meta.duty_min_rate_eur_per_cc == 2.0
        assert meta.duty_rate_eur_per_cc == 4.0
        assert meta.duty_value_bracket_max_eur == 30000.0
        assert meta.vehicle_type == "pickup"
        assert meta.engine_power_hp == 250
        assert meta.engine_power_kw == 183.875
        assert meta.utilization_coefficient == 0.2
        assert len(meta.rates_used) == 1
        assert len(meta.detailed_rates_used) == 1
        assert len(meta.warnings) == 1
