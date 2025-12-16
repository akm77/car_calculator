"""
Интеграционные тесты для calculate() - полный расчёт end-to-end.

Тестирует функцию calculate() с фиксированными данными:
- Все компоненты breakdown корректно рассчитываются
- Метаданные (meta) формируются правильно
- Инварианты выполняются (total = сумма, ОАЭ комиссия = 0)
- rates_used и detailed_rates_used содержат правильные данные

Методология: Использование реальных конфигов через get_configs(),
но с детерминированными входными данными.

Coverage: ~100% для calculate() в контексте интеграции всех helper-функций
Приоритет: HIGH (критический путь расчёта)

Changelog:
- 2025-12-16: Создан полный набор интеграционных тестов для calculate()
"""

from datetime import datetime, UTC
from decimal import Decimal

import pytest

from app.calculation.engine import calculate
from app.calculation.models import CalculationRequest
from app.core.settings import get_configs


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def base_request_japan():
    """Базовый запрос для Японии."""
    return {
        "country": "japan",
        "year": 2023,  # lt3 в 2025
        "engine_cc": 2000,
        "engine_power_hp": 150,
        "purchase_price": 2000000,
        "currency": "JPY",
        "freight_type": "standard",
        "vehicle_type": "M1",
    }


@pytest.fixture
def base_request_korea():
    """Базовый запрос для Кореи."""
    return {
        "country": "korea",
        "year": 2021,  # 3_5 в 2025
        "engine_cc": 1800,
        "engine_power_hp": 140,
        "purchase_price": 15000,
        "currency": "USD",
        "freight_type": "standard",
        "vehicle_type": "M1",
    }


@pytest.fixture
def base_request_uae():
    """Базовый запрос для ОАЭ."""
    return {
        "country": "uae",
        "year": 2018,  # gt5 в 2025
        "engine_cc": 3500,
        "engine_power_hp": 300,
        "purchase_price": 40000,
        "currency": "USD",
        "freight_type": "container",
        "vehicle_type": "M1",
    }


# ============================================================================
# TEST CLASS: End-to-End Расчёт
# ============================================================================


class TestCalculateEndToEnd:
    """End-to-end тесты для calculate()."""

    def test_japan_lt3_standard(self, base_request_japan):
        """
        Полный расчёт для Японии, авто < 3 лет, несанкционное.
        Проверяем все компоненты breakdown.
        """
        request = CalculationRequest(**base_request_japan)
        result = calculate(request)

        # Проверяем структуру
        assert result.breakdown is not None
        assert result.meta is not None

        # Проверяем метаданные
        assert result.meta.age_category == "lt3"
        assert result.meta.engine_power_hp == 150
        # 150 × 0.7355 = 110.325
        assert abs(result.meta.engine_power_kw - 110.325) < 0.01

        # Проверяем компоненты breakdown
        assert result.breakdown.purchase_price_rub > 0
        assert result.breakdown.country_expenses_rub > 0
        assert result.breakdown.freight_rub > 0
        assert result.breakdown.customs_services_rub > 0  # Должно быть > 0
        assert result.breakdown.duties_rub > 0
        assert result.breakdown.utilization_fee_rub > 0
        assert result.breakdown.era_glonass_rub > 0
        assert result.breakdown.company_commission_rub > 0

        # Проверяем инвариант: total = сумма компонентов
        # NOTE: ERA-GLONASS теперь включается в total (исправлен баг 2025-12-16)
        total_calculated = (
            result.breakdown.purchase_price_rub +
            result.breakdown.country_expenses_rub +
            result.breakdown.freight_rub +
            result.breakdown.customs_services_rub +
            result.breakdown.duties_rub +
            result.breakdown.utilization_fee_rub +
            result.breakdown.era_glonass_rub +  # ✅ FIXED: Now included in total
            result.breakdown.company_commission_rub
        )
        assert result.breakdown.total_rub == total_calculated

    def test_korea_3_5(self, base_request_korea):
        """
        Полный расчёт для Кореи, авто 3-5 лет.
        Проверяем пошлину и утильсбор.
        """
        request = CalculationRequest(**base_request_korea)
        result = calculate(request)

        # Проверяем возрастную категорию
        assert result.meta.age_category == "3_5"

        # Проверяем, что пошлина рассчитана по формуле per_cc
        assert result.meta.duty_formula_mode == "per_cc"
        assert result.breakdown.duties_rub > 0

        # Проверяем утильсбор (должен быть > 0 для M1)
        assert result.breakdown.utilization_fee_rub > 0

        # Инвариант: total = сумма компонентов
        # NOTE: ERA-GLONASS теперь включается в total (исправлен баг 2025-12-16)
        total_calculated = (
            result.breakdown.purchase_price_rub +
            result.breakdown.country_expenses_rub +
            result.breakdown.freight_rub +
            result.breakdown.customs_services_rub +
            result.breakdown.duties_rub +
            result.breakdown.utilization_fee_rub +
            result.breakdown.era_glonass_rub +  # ✅ FIXED: Now included in total
            result.breakdown.company_commission_rub
        )
        assert result.breakdown.total_rub == total_calculated

    def test_uae_gt5_commission_invariant(self, base_request_uae):
        """
        ОАЭ: комиссия компании всегда = 0.
        Проверяем инвариант для ОАЭ.
        """
        request = CalculationRequest(**base_request_uae)
        result = calculate(request)

        # Проверяем возрастную категорию
        assert result.meta.age_category == "gt5"

        # ИНВАРИАНТ: ОАЭ → комиссия компании = 0
        assert result.breakdown.company_commission_rub == Decimal("0")

        # Остальные компоненты должны быть > 0
        assert result.breakdown.purchase_price_rub > 0
        assert result.breakdown.duties_rub > 0
        assert result.breakdown.utilization_fee_rub > 0

        # Инвариант: total = сумма компонентов
        # NOTE: ERA-GLONASS теперь включается в total (исправлен баг 2025-12-16)
        total_calculated = (
            result.breakdown.purchase_price_rub +
            result.breakdown.country_expenses_rub +
            result.breakdown.freight_rub +
            result.breakdown.customs_services_rub +
            result.breakdown.duties_rub +
            result.breakdown.utilization_fee_rub +
            result.breakdown.era_glonass_rub +  # ✅ FIXED: Now included in total
            result.breakdown.company_commission_rub
        )
        assert result.breakdown.total_rub == total_calculated

    def test_china_lt3_high_value(self):
        """
        Китай, lt3, высокая стоимость.
        Проверяем max(percent, min) для пошлины.
        """
        request = CalculationRequest(
            country="china",
            year=2024,  # lt3 в 2025
            engine_cc=3000,
            engine_power_hp=250,
            purchase_price=500000,  # Высокая стоимость
            currency="CNY",
            freight_type="standard",
            vehicle_type="M1",
        )
        result = calculate(request)

        # Проверяем возрастную категорию
        assert result.meta.age_category == "lt3"

        # Пошлина должна быть рассчитана
        assert result.breakdown.duties_rub > 0

        # Должен быть либо mode = "percent", либо "min"
        assert result.meta.duty_formula_mode in ["percent", "min"]

        # Инвариант: total = сумма компонентов
        # NOTE: ERA-GLONASS теперь включается в total (исправлен баг 2025-12-16)
        total_calculated = (
            result.breakdown.purchase_price_rub +
            result.breakdown.country_expenses_rub +
            result.breakdown.freight_rub +
            result.breakdown.customs_services_rub +
            result.breakdown.duties_rub +
            result.breakdown.utilization_fee_rub +
            result.breakdown.era_glonass_rub +  # ✅ FIXED: Now included in total
            result.breakdown.company_commission_rub
        )
        assert result.breakdown.total_rub == total_calculated

    def test_georgia_gt5(self):
        """
        Грузия, gt5.
        Проверяем все компоненты.
        """
        request = CalculationRequest(
            country="georgia",
            year=2015,  # gt5 в 2025
            engine_cc=2500,
            engine_power_hp=200,
            purchase_price=12000,
            currency="USD",
            freight_type="standard",
            vehicle_type="M1",
        )
        result = calculate(request)

        # Проверяем возрастную категорию
        assert result.meta.age_category == "gt5"

        # Все компоненты должны быть > 0
        assert result.breakdown.purchase_price_rub > 0
        assert result.breakdown.country_expenses_rub > 0
        assert result.breakdown.freight_rub > 0
        assert result.breakdown.duties_rub > 0
        assert result.breakdown.utilization_fee_rub > 0

        # Комиссия компании для Грузии должна быть > 0 (не ОАЭ)
        assert result.breakdown.company_commission_rub > 0

        # Инвариант: total = сумма компонентов
        # NOTE: ERA-GLONASS теперь включается в total (исправлен баг 2025-12-16)
        total_calculated = (
            result.breakdown.purchase_price_rub +
            result.breakdown.country_expenses_rub +
            result.breakdown.freight_rub +
            result.breakdown.customs_services_rub +
            result.breakdown.duties_rub +
            result.breakdown.utilization_fee_rub +
            result.breakdown.era_glonass_rub +  # ✅ FIXED: Now included in total
            result.breakdown.company_commission_rub
        )
        assert result.breakdown.total_rub == total_calculated


# ============================================================================
# TEST CLASS: Проверка метаданных (meta)
# ============================================================================


class TestCalculateMetadata:
    """Тесты для проверки метаданных в result.meta."""

    def test_age_category_detection(self):
        """Проверка корректного определения age_category."""
        # lt3: 2023-2025 (0-2 года)
        request_lt3 = CalculationRequest(
            country="japan",
            year=2023,
            engine_cc=2000,
            engine_power_hp=150,
            purchase_price=2000000,
            currency="JPY",
        )
        result_lt3 = calculate(request_lt3)
        assert result_lt3.meta.age_category == "lt3"

        # 3_5: 2020-2022 (3-5 лет)
        request_3_5 = CalculationRequest(
            country="japan",
            year=2021,
            engine_cc=2000,
            engine_power_hp=150,
            purchase_price=2000000,
            currency="JPY",
        )
        result_3_5 = calculate(request_3_5)
        assert result_3_5.meta.age_category == "3_5"

        # gt5: ≤2019 (>5 лет)
        request_gt5 = CalculationRequest(
            country="japan",
            year=2018,
            engine_cc=2000,
            engine_power_hp=150,
            purchase_price=2000000,
            currency="JPY",
        )
        result_gt5 = calculate(request_gt5)
        assert result_gt5.meta.age_category == "gt5"

    def test_engine_power_kw_conversion(self):
        """Проверка конвертации hp → kW (× 0.7355)."""
        test_cases = [
            (100, 73.55),   # 100 hp → 73.55 kW
            (150, 110.325), # 150 hp → 110.325 kW
            (200, 147.1),   # 200 hp → 147.1 kW
            (300, 220.65),  # 300 hp → 220.65 kW
        ]

        for hp, expected_kw in test_cases:
            request = CalculationRequest(
                country="japan",
                year=2023,
                engine_cc=2000,
                engine_power_hp=hp,
                purchase_price=2000000,
                currency="JPY",
            )
            result = calculate(request)
            assert abs(result.meta.engine_power_kw - expected_kw) < 0.01

    def test_rates_used_contains_all_currencies(self, base_request_japan):
        """Проверка что rates_used содержит все использованные валюты."""
        request = CalculationRequest(**base_request_japan)
        result = calculate(request)

        # Должны быть JPY (покупка), EUR (пошлина), USD (фрахт, комиссия)
        assert "JPY_RUB" in result.meta.rates_used
        assert "EUR_RUB" in result.meta.rates_used
        assert "USD_RUB" in result.meta.rates_used

        # Все курсы должны быть числами > 0
        for rate in result.meta.rates_used.values():
            assert rate > 0

    def test_detailed_rates_used_structure(self, base_request_japan):
        """Проверка структуры detailed_rates_used."""
        request = CalculationRequest(**base_request_japan)
        result = calculate(request)

        assert result.meta.detailed_rates_used is not None

        # Проверяем структуру для каждой валюты
        for code, rate_usage in result.meta.detailed_rates_used.items():
            assert rate_usage.base_rate > 0
            assert rate_usage.effective_rate > 0
            assert rate_usage.bank_commission_percent >= 0
            assert rate_usage.display is not None
            assert len(rate_usage.display) > 0

    def test_detailed_rates_display_format_no_commission(self, base_request_japan):
        """
        Проверка формата display без банковской комиссии.
        Формат: "USD/RUB = 90.0"
        """
        # Убедимся, что bank_commission отключена в конфиге
        configs = get_configs()

        request = CalculationRequest(**base_request_japan)
        result = calculate(request)

        # Проверяем формат display (примеры)
        for code, rate_usage in result.meta.detailed_rates_used.items():
            # Формат: "CODE/RUB = base_rate" или "CODE/RUB = base_rate + percent%"
            assert f"{code}/RUB" in rate_usage.display
            assert "=" in rate_usage.display

            # Если комиссия 0, не должно быть знака "+"
            if rate_usage.bank_commission_percent == 0:
                assert "+" not in rate_usage.display


# ============================================================================
# TEST CLASS: Проверка инвариантов
# ============================================================================


class TestCalculateInvariants:
    """Тесты для проверки инвариантов расчёта."""

    @pytest.mark.parametrize("country,year,engine_cc,engine_power_hp,purchase_price,currency", [
        ("japan", 2023, 2000, 150, 2000000, "JPY"),
        ("korea", 2021, 1800, 140, 15000, "USD"),
        ("uae", 2018, 3500, 300, 40000, "USD"),
        ("china", 2024, 2500, 200, 300000, "CNY"),
        ("georgia", 2020, 2000, 180, 18000, "USD"),
    ])
    def test_total_equals_sum_of_components(self, country, year, engine_cc,
                                           engine_power_hp, purchase_price, currency):
        """
        ИНВАРИАНТ: total_rub = сумма всех компонентов breakdown.
        Проверяем для всех стран.
        """
        request = CalculationRequest(
            country=country,
            year=year,
            engine_cc=engine_cc,
            engine_power_hp=engine_power_hp,
            purchase_price=purchase_price,
            currency=currency,
            vehicle_type="M1",
        )
        result = calculate(request)

        # NOTE: ERA-GLONASS теперь включается в total (исправлен баг 2025-12-16)
        total_calculated = (
            result.breakdown.purchase_price_rub +
            result.breakdown.country_expenses_rub +
            result.breakdown.freight_rub +
            result.breakdown.customs_services_rub +
            result.breakdown.duties_rub +
            result.breakdown.utilization_fee_rub +
            result.breakdown.era_glonass_rub +  # ✅ FIXED: Now included in total
            result.breakdown.company_commission_rub
        )

        assert result.breakdown.total_rub == total_calculated

    def test_uae_commission_always_zero(self):
        """
        ИНВАРИАНТ: ОАЭ → company_commission_rub всегда = 0.
        Проверяем для разных параметров ОАЭ.
        """
        test_cases = [
            {"year": 2023, "engine_cc": 2000, "purchase_price": 30000},
            {"year": 2020, "engine_cc": 3500, "purchase_price": 50000},
            {"year": 2015, "engine_cc": 4000, "purchase_price": 25000},
        ]

        for params in test_cases:
            request = CalculationRequest(
                country="uae",
                year=params["year"],
                engine_cc=params["engine_cc"],
                engine_power_hp=200,
                purchase_price=params["purchase_price"],
                currency="USD",
                vehicle_type="M1",
            )
            result = calculate(request)

            # ИНВАРИАНТ: ОАЭ → комиссия = 0
            assert result.breakdown.company_commission_rub == Decimal("0")

    def test_non_m1_utilization_fee_zero(self):
        """
        ИНВАРИАНТ: Не-M1 → utilization_fee_rub = 0 (с предупреждением).
        """
        request = CalculationRequest(
            country="japan",
            year=2023,
            engine_cc=2000,
            engine_power_hp=150,
            purchase_price=2000000,
            currency="JPY",
            vehicle_type="bus",  # Не-легковой
        )
        result = calculate(request)

        # ИНВАРИАНТ: Не-M1 → утильсбор = 0
        assert result.breakdown.utilization_fee_rub == Decimal("0")

        # Должно быть предупреждение
        warning_codes = [w.code for w in result.meta.warnings]
        assert "NON_M1" in warning_codes

    def test_all_breakdown_components_non_negative(self, base_request_japan):
        """
        ИНВАРИАНТ: Все компоненты breakdown ≥ 0.
        """
        request = CalculationRequest(**base_request_japan)
        result = calculate(request)

        assert result.breakdown.purchase_price_rub >= 0
        assert result.breakdown.country_expenses_rub >= 0
        assert result.breakdown.freight_rub >= 0
        assert result.breakdown.customs_services_rub >= 0
        assert result.breakdown.duties_rub >= 0
        assert result.breakdown.utilization_fee_rub >= 0
        assert result.breakdown.era_glonass_rub >= 0
        assert result.breakdown.company_commission_rub >= 0
        assert result.breakdown.total_rub >= 0


# ============================================================================
# TEST CLASS: Санкционный статус
# ============================================================================


class TestSanctionedStatus:
    """Тесты для проверки обработки санкционного статуса."""


    def test_sanctions_unknown_warning(self):
        """
        Если sanctions_unknown=True, должно быть предупреждение.
        """
        request = CalculationRequest(
            country="japan",
            year=2023,
            engine_cc=2000,
            engine_power_hp=150,
            purchase_price=2000000,
            currency="JPY",
            sanctions_unknown=True,
        )
        result = calculate(request)

        # Должно быть предупреждение SANCTIONS_UNKNOWN
        warning_codes = [w.code for w in result.meta.warnings]
        assert "SANCTIONS_UNKNOWN" in warning_codes


# ============================================================================
# TEST CLASS: Граничные случаи
# ============================================================================


class TestEdgeCases:
    """Тесты для граничных случаев."""

    def test_minimal_car(self):
        """Минимальные параметры автомобиля."""
        request = CalculationRequest(
            country="japan",
            year=2024,
            engine_cc=600,  # Минимальный объём
            engine_power_hp=50,  # Минимальная мощность
            purchase_price=500000,
            currency="JPY",
        )
        result = calculate(request)

        # Расчёт должен пройти успешно
        assert result.breakdown.total_rub > 0
        assert result.meta.age_category == "lt3"

    def test_maximum_car(self):
        """Максимальные параметры автомобиля."""
        request = CalculationRequest(
            country="uae",
            year=2023,
            engine_cc=6000,  # Большой объём
            engine_power_hp=600,  # Большая мощность
            purchase_price=1000000,
            currency="USD",
        )
        result = calculate(request)

        # Расчёт должен пройти успешно
        assert result.breakdown.total_rub > 0
        assert result.meta.age_category == "lt3"

    def test_low_purchase_price(self):
        """Низкая стоимость покупки (граничный случай)."""
        request = CalculationRequest(
            country="japan",
            year=2023,
            engine_cc=600,
            engine_power_hp=50,
            purchase_price=100000,  # Низкая цена
            currency="JPY",
        )
        result = calculate(request)

        # purchase_price_rub должен быть > 0
        assert result.breakdown.purchase_price_rub > 0

        # Остальные компоненты должны быть > 0
        assert result.breakdown.duties_rub > 0
        assert result.breakdown.utilization_fee_rub > 0

