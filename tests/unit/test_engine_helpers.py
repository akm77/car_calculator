"""
Юнит-тесты для helper-функций engine.py.

Покрывает все helper-функции изолированно:
- _compute_duty() - расчёт таможенной пошлины
- _commission() - комиссия компании
- _select_freight() - выбор фрахта
- _japan_country_expenses() - страновые расходы Японии
- _other_country_expenses() - страновые расходы других стран
- _convert() - конвертация валюты
- _effective_currency_rate() - эффективный курс с комиссией
- _get_bank_commission_percent() - извлечение процента банковской комиссии

Методология: Детерминированные данные через фикстуры, изоляция от реальных конфигов.

Coverage: ~100% для всех helper-функций engine.py
Приоритет: HIGH (критические вычисления)

Changelog:
- 2025-12-16: Создан полный набор юнит-тестов для всех helper-функций
"""

from decimal import Decimal

import pytest

from app.calculation.engine import (
    _commission,
    _compute_duty,
    _convert,
    _effective_currency_rate,
    _get_bank_commission_percent,
    _japan_country_expenses,
    _other_country_expenses,
    _select_freight,
)


# ============================================================================
# FIXTURES - Детерминированные конфиги для изоляции тестов
# ============================================================================


@pytest.fixture
def mock_rates_config():
    """Фиксированные курсы для изоляции тестов."""
    return {
        "currencies": {
            "USD_RUB": 90.0,
            "EUR_RUB": 100.0,
            "JPY_RUB": 0.6,
            "CNY_RUB": 12.5,
            "AED_RUB": 24.5,
        }
    }


@pytest.fixture
def mock_duties_config():
    """Фиксированная конфигурация пошлин."""
    return {
        "age_categories": {
            "lt3": {
                "value_brackets": [
                    {"max_customs_value_eur": 8500, "percent": 0.54, "min_rate_eur_per_cc": 2.5},
                    {"max_customs_value_eur": 16700, "percent": 0.48, "min_rate_eur_per_cc": 3.5},
                    {"max_customs_value_eur": 42300, "percent": 0.48, "min_rate_eur_per_cc": 5.5},
                    {"max_customs_value_eur": 84500, "percent": 0.48, "min_rate_eur_per_cc": 7.5},
                    {"max_customs_value_eur": 169000, "percent": 0.48, "min_rate_eur_per_cc": 15},
                    {"percent": 0.48, "min_rate_eur_per_cc": 20},
                ]
            },
            "3_5": {
                "bands": [
                    {"max_cc": 1000, "rate_eur_per_cc": 1.5},
                    {"max_cc": 1500, "rate_eur_per_cc": 1.7},
                    {"max_cc": 1800, "rate_eur_per_cc": 2.5},
                    {"max_cc": 2300, "rate_eur_per_cc": 2.7},
                    {"max_cc": 3000, "rate_eur_per_cc": 3.0},
                    {"rate_eur_per_cc": 3.6},  # >3000
                ]
            },
            "gt5": {
                "bands": [
                    {"max_cc": 1000, "rate_eur_per_cc": 3.0},
                    {"max_cc": 1500, "rate_eur_per_cc": 3.2},
                    {"max_cc": 1800, "rate_eur_per_cc": 3.5},
                    {"max_cc": 2300, "rate_eur_per_cc": 4.8},
                    {"max_cc": 3000, "rate_eur_per_cc": 5.0},
                    {"rate_eur_per_cc": 5.5},  # >3000
                ]
            },
        }
    }


@pytest.fixture
def mock_commissions_config():
    """Фиксированная конфигурация комиссий."""
    return {
        "default_commission_usd": 1000,
        "by_country": {
            "uae": {"commission_usd": 0},
            "georgia": {"commission_usd": 750},
        },
        "bank_commission": {
            "enabled": False,
            "percent": 0.0,
        }
    }


@pytest.fixture
def mock_fees_japan():
    """Конфигурация сборов для Японии."""
    return {
        "country_currency": "JPY",
        "tiers": [
            {"max_price": 3000000, "expenses": 150000},
            {"max_price": 6000000, "expenses": 300000},
            {"expenses": 400000},  # > 6,000,000
        ],
        "freight": {
            "standard": {"amount": 350, "currency": "USD"},
            "sanctioned": {"amount": 2000, "currency": "USD"},
        }
    }


@pytest.fixture
def mock_fees_korea():
    """Конфигурация сборов для Кореи."""
    return {
        "country_currency": "USD",
        "base_expenses": {
            "registration": 200,
            "inspection": 150,
            "other": 150,
        },
        "freight": {
            "standard": {"amount": 1000, "currency": "USD"},
        }
    }


@pytest.fixture
def mock_fees_uae():
    """Конфигурация сборов для ОАЭ."""
    return {
        "country_currency": "USD",
        "base_expenses": {
            "registration": 500,
            "inspection": 300,
            "other": 200,
        },
        "freight": {
            "open": {"amount": 2500, "currency": "USD"},
            "container": {"amount": 3800, "currency": "USD"},
        }
    }


# ============================================================================
# TEST CLASS: _compute_duty()
# ============================================================================


class TestComputeDuty:
    """Тесты для _compute_duty() - расчёт таможенной пошлины."""

    # ---- LT3 (авто ≤3 лет) ----

    def test_lt3_low_value_min_wins(self, mock_rates_config, mock_duties_config):
        """
        Низкая стоимость < 8500 EUR: процент 54%, min 2.5 EUR/cc.
        Случай когда min > percent (берём min).
        """
        purchase_price_rub = Decimal("700000")  # 7000 EUR при курсе 100
        engine_cc = 2000
        warnings = []

        duty_rub, mode, details = _compute_duty(
            engine_cc=engine_cc,
            age_category="lt3",
            duties_conf=mock_duties_config,
            rates_conf=mock_rates_config,
            warnings=warnings,
            purchase_price_rub=purchase_price_rub,
        )

        # Ожидаем:
        # customs_value_eur = 700000 / 100 = 7000 EUR
        # duty_percent = 7000 × 0.54 = 3780 EUR
        # duty_min = 2000 × 2.5 = 5000 EUR
        # max(3780, 5000) = 5000 EUR = 500000 RUB
        assert duty_rub == Decimal("500000")
        assert mode == "min"
        assert details["customs_value_eur"] == 7000
        assert details["duty_percent"] == 0.54  # Stored as decimal, not percentage
        assert details["duty_min_rate_eur_per_cc"] == 2.5

    def test_lt3_medium_value_percent_wins(self, mock_rates_config, mock_duties_config):
        """
        Средняя стоимость 8500-16700 EUR: процент 48%, min 3.5 EUR/cc.
        Случай когда percent > min (берём percent).
        """
        purchase_price_rub = Decimal("1500000")  # 15000 EUR при курсе 100
        engine_cc = 1500
        warnings = []

        duty_rub, mode, details = _compute_duty(
            engine_cc=engine_cc,
            age_category="lt3",
            duties_conf=mock_duties_config,
            rates_conf=mock_rates_config,
            warnings=warnings,
            purchase_price_rub=purchase_price_rub,
        )

        # Ожидаем:
        # customs_value_eur = 15000 EUR
        # duty_percent = 15000 × 0.48 = 7200 EUR
        # duty_min = 1500 × 3.5 = 5250 EUR
        # max(7200, 5250) = 7200 EUR = 720000 RUB
        assert duty_rub == Decimal("720000")
        assert mode == "percent"
        assert details["customs_value_eur"] == 15000

    def test_lt3_high_value(self, mock_rates_config, mock_duties_config):
        """
        Высокая стоимость > 169000 EUR: процент 48%, min 20 EUR/cc.
        """
        purchase_price_rub = Decimal("20000000")  # 200000 EUR при курсе 100
        engine_cc = 3000
        warnings = []

        duty_rub, mode, details = _compute_duty(
            engine_cc=engine_cc,
            age_category="lt3",
            duties_conf=mock_duties_config,
            rates_conf=mock_rates_config,
            warnings=warnings,
            purchase_price_rub=purchase_price_rub,
        )

        # Ожидаем:
        # customs_value_eur = 200000 EUR
        # duty_percent = 200000 × 0.48 = 96000 EUR
        # duty_min = 3000 × 20 = 60000 EUR
        # max(96000, 60000) = 96000 EUR = 9600000 RUB
        assert duty_rub == Decimal("9600000")
        assert mode == "percent"

    @pytest.mark.parametrize("purchase_price_rub,expected_customs_value_eur", [
        (850000, 8500),   # Ровно граница первого брэкета
        (1670000, 16700),  # Ровно граница второго брэкета
        (4230000, 42300),  # Ровно граница третьего брэкета
    ])
    def test_lt3_boundary_values(self, mock_rates_config, mock_duties_config,
                                 purchase_price_rub, expected_customs_value_eur):
        """Граничные значения EUR (ровно на границах брэкетов)."""
        warnings = []
        duty_rub, mode, details = _compute_duty(
            engine_cc=2000,
            age_category="lt3",
            duties_conf=mock_duties_config,
            rates_conf=mock_rates_config,
            warnings=warnings,
            purchase_price_rub=Decimal(str(purchase_price_rub)),
        )

        assert details["customs_value_eur"] == expected_customs_value_eur
        assert duty_rub > 0

    # ---- 3_5 (авто 3-5 лет) ----

    @pytest.mark.parametrize("engine_cc,expected_rate,expected_duty_eur", [
        (800, 1.5, 1200),      # ≤1000 cc → 1.5 EUR/cc
        (1000, 1.5, 1500),     # Граница 1000
        (1200, 1.7, 2040),     # 1001-1500 cc → 1.7 EUR/cc
        (1500, 1.7, 2550),     # Граница 1500
        (1700, 2.5, 4250),     # 1501-1800 cc → 2.5 EUR/cc
        (1800, 2.5, 4500),     # Граница 1800
        (2000, 2.7, 5400),     # 1801-2300 cc → 2.7 EUR/cc
        (2300, 2.7, 6210),     # Граница 2300
        (2500, 3.0, 7500),     # 2301-3000 cc → 3.0 EUR/cc
        (3000, 3.0, 9000),     # Граница 3000
        (3500, 3.6, 12600),    # >3000 cc → 3.6 EUR/cc
    ])
    def test_3_5_all_cc_ranges(self, mock_rates_config, mock_duties_config,
                                engine_cc, expected_rate, expected_duty_eur):
        """Все диапазоны объёма для возраста 3-5 лет."""
        warnings = []
        duty_rub, mode, details = _compute_duty(
            engine_cc=engine_cc,
            age_category="3_5",
            duties_conf=mock_duties_config,
            rates_conf=mock_rates_config,
            warnings=warnings,
            purchase_price_rub=Decimal("1000000"),  # Не используется для 3_5
        )

        # duty_rub = engine_cc × rate_eur_per_cc × EUR_RUB
        # duty_rub = engine_cc × rate × 100
        expected_duty_rub = Decimal(str(expected_duty_eur * 100))
        assert duty_rub == expected_duty_rub
        assert mode == "per_cc"
        assert details["duty_rate_eur_per_cc"] == expected_rate

    # ---- GT5 (авто >5 лет) ----

    @pytest.mark.parametrize("engine_cc,expected_rate,expected_duty_eur", [
        (800, 3.0, 2400),      # ≤1000 cc → 3.0 EUR/cc
        (1001, 3.2, 3203.2),   # 1001-1500 cc → 3.2 EUR/cc
        (1600, 3.5, 5600),     # 1501-1800 cc → 3.5 EUR/cc
        (2000, 4.8, 9600),     # 1801-2300 cc → 4.8 EUR/cc
        (2500, 5.0, 12500),    # 2301-3000 cc → 5.0 EUR/cc
        (4000, 5.5, 22000),    # >3000 cc → 5.5 EUR/cc
    ])
    def test_gt5_all_cc_ranges(self, mock_rates_config, mock_duties_config,
                                engine_cc, expected_rate, expected_duty_eur):
        """Все диапазоны объёма для возраста >5 лет."""
        warnings = []
        duty_rub, mode, details = _compute_duty(
            engine_cc=engine_cc,
            age_category="gt5",
            duties_conf=mock_duties_config,
            rates_conf=mock_rates_config,
            warnings=warnings,
            purchase_price_rub=Decimal("1000000"),
        )

        expected_duty_rub = Decimal(str(expected_duty_eur * 100))
        assert duty_rub == expected_duty_rub
        assert mode == "per_cc"
        assert details["duty_rate_eur_per_cc"] == expected_rate

    def test_gt5_rates_higher_than_3_5(self, mock_rates_config, mock_duties_config):
        """Проверка что ставки gt5 > ставок 3_5 (согласно SPEC)."""
        engine_cc = 2000
        warnings = []

        duty_3_5, _, _ = _compute_duty(
            engine_cc=engine_cc,
            age_category="3_5",
            duties_conf=mock_duties_config,
            rates_conf=mock_rates_config,
            warnings=warnings,
            purchase_price_rub=Decimal("1000000"),
        )

        duty_gt5, _, _ = _compute_duty(
            engine_cc=engine_cc,
            age_category="gt5",
            duties_conf=mock_duties_config,
            rates_conf=mock_rates_config,
            warnings=warnings,
            purchase_price_rub=Decimal("1000000"),
        )

        assert duty_gt5 > duty_3_5


# ============================================================================
# TEST CLASS: _commission()
# ============================================================================


class TestCommission:
    """Тесты для _commission() - комиссия компании."""

    @pytest.mark.parametrize("country", ["japan", "korea", "china"])
    def test_default_commission(self, mock_rates_config, mock_commissions_config, country):
        """Дефолтная комиссия 1000 USD для всех стран кроме ОАЭ."""
        commission_rub = _commission(
            amount_rub=Decimal("0"),  # Не используется в новой версии
            commissions_conf=mock_commissions_config,
            country=country,
            rates_conf=mock_rates_config,
            bank_commission_percent=0.0,
        )

        # Ожидаем: 1000 × 90.0 = 90000 RUB
        assert commission_rub == Decimal("90000")

    def test_uae_zero_commission(self, mock_rates_config, mock_commissions_config):
        """ОАЭ: комиссия = 0 USD → 0 RUB."""
        commission_rub = _commission(
            amount_rub=Decimal("0"),
            commissions_conf=mock_commissions_config,
            country="uae",
            rates_conf=mock_rates_config,
            bank_commission_percent=0.0,
        )

        assert commission_rub == Decimal("0")

    def test_georgia_custom_commission(self, mock_rates_config, mock_commissions_config):
        """Грузия: кастомная комиссия 750 USD."""
        commission_rub = _commission(
            amount_rub=Decimal("0"),
            commissions_conf=mock_commissions_config,
            country="georgia",
            rates_conf=mock_rates_config,
            bank_commission_percent=0.0,
        )

        # Ожидаем: 750 × 90.0 = 67500 RUB
        assert commission_rub == Decimal("67500")

    def test_commission_with_bank_commission(self, mock_rates_config, mock_commissions_config):
        """С банковской комиссией 2%: effective_rate = base_rate × 1.02."""
        commission_rub = _commission(
            amount_rub=Decimal("0"),
            commissions_conf=mock_commissions_config,
            country="japan",
            rates_conf=mock_rates_config,
            bank_commission_percent=2.0,
        )

        # Ожидаем: 1000 × (90.0 × 1.02) = 1000 × 91.8 = 91800 RUB
        assert commission_rub == Decimal("91800")


# ============================================================================
# TEST CLASS: _select_freight()
# ============================================================================


class TestSelectFreight:
    """Тесты для _select_freight() - выбор фрахта."""

    def test_japan_standard(self, mock_fees_japan):
        """Япония (несанкционный): 350 USD."""
        amount, freight_type, currency = _select_freight(
            mock_fees_japan, "standard"
        )

        assert amount == Decimal("350")
        assert freight_type == "standard"
        assert currency == "USD"

    def test_japan_sanctioned(self, mock_fees_japan):
        """Япония (санкционный): 2000 USD."""
        amount, freight_type, currency = _select_freight(
            mock_fees_japan, "sanctioned"
        )

        assert amount == Decimal("2000")
        assert freight_type == "sanctioned"
        assert currency == "USD"

    def test_korea_standard(self, mock_fees_korea):
        """Корея: 1000 USD."""
        amount, freight_type, currency = _select_freight(
            mock_fees_korea, "standard"
        )

        assert amount == Decimal("1000")
        assert freight_type == "standard"
        assert currency == "USD"

    def test_uae_open(self, mock_fees_uae):
        """ОАЭ (open): 2500 USD."""
        amount, freight_type, currency = _select_freight(
            mock_fees_uae, "open"
        )

        assert amount == Decimal("2500")
        assert freight_type == "open"
        assert currency == "USD"

    def test_uae_container(self, mock_fees_uae):
        """ОАЭ (container): 3800 USD."""
        amount, freight_type, currency = _select_freight(
            mock_fees_uae, "container"
        )

        assert amount == Decimal("3800")
        assert freight_type == "container"
        assert currency == "USD"

    def test_default_freight_type(self, mock_fees_japan):
        """Если freight_type не указан, берём первый доступный."""
        amount, freight_type, currency = _select_freight(
            mock_fees_japan, None
        )

        # Должен взять первый доступный (standard)
        assert amount == Decimal("350")
        assert freight_type == "standard"
        assert currency == "USD"


# ============================================================================
# TEST CLASS: _japan_country_expenses()
# ============================================================================


class TestJapanCountryExpenses:
    """Тесты для _japan_country_expenses() - страновые расходы Японии."""

    @pytest.mark.parametrize("purchase_price_jpy,expected_expenses", [
        (2000000, 150000),    # ≤ 3,000,000 JPY → 150,000 JPY
        (3000000, 150000),    # Ровно граница → 150,000 JPY
        (4000000, 300000),    # 3,000,001 - 6,000,000 JPY → 300,000 JPY
        (6000000, 300000),    # Ровно граница → 300,000 JPY
        (8000000, 400000),    # > 6,000,000 JPY → 400,000 JPY
        (10000000, 400000),   # Высокая цена → 400,000 JPY
    ])
    def test_japan_tiers(self, mock_fees_japan, purchase_price_jpy, expected_expenses):
        """Тесты для всех тиров страновых расходов Японии."""
        expenses = _japan_country_expenses(
            mock_fees_japan,
            Decimal(str(purchase_price_jpy))
        )

        assert expenses == Decimal(str(expected_expenses))


# ============================================================================
# TEST CLASS: _other_country_expenses()
# ============================================================================


class TestOtherCountryExpenses:
    """Тесты для _other_country_expenses() - страновые расходы других стран."""

    def test_korea_expenses(self, mock_fees_korea):
        """Корея: 500 USD (200 + 150 + 150)."""
        expenses = _other_country_expenses(mock_fees_korea)

        # 200 + 150 + 150 = 500
        assert expenses == Decimal("500")

    def test_uae_expenses(self, mock_fees_uae):
        """ОАЭ: 1000 USD (500 + 300 + 200)."""
        expenses = _other_country_expenses(mock_fees_uae)

        # 500 + 300 + 200 = 1000
        assert expenses == Decimal("1000")


# ============================================================================
# TEST CLASS: _convert()
# ============================================================================


class TestConvert:
    """Тесты для _convert() - конвертация валюты."""

    @pytest.mark.parametrize("amount,currency,expected_rub", [
        (1000, "USD", 90000),       # 1000 × 90.0 = 90000
        (1000, "EUR", 100000),      # 1000 × 100.0 = 100000
        (1000000, "JPY", 600000),   # 1000000 × 0.6 = 600000
        (100, "CNY", 1250),         # 100 × 12.5 = 1250
        (100, "AED", 2450),         # 100 × 24.5 = 2450
    ])
    def test_convert_no_commission(self, mock_rates_config, amount, currency, expected_rub):
        """Конвертация без банковской комиссии."""
        result = _convert(
            amount=Decimal(str(amount)),
            currency=currency,
            rates_conf=mock_rates_config,
            bank_commission_percent=0.0,
        )

        assert result == Decimal(str(expected_rub))

    def test_convert_with_commission_2_percent(self, mock_rates_config):
        """Конвертация с банковской комиссией 2%."""
        result = _convert(
            amount=Decimal("1000"),
            currency="USD",
            rates_conf=mock_rates_config,
            bank_commission_percent=2.0,
        )

        # Ожидаем: 1000 × (90.0 × 1.02) = 1000 × 91.8 = 91800
        assert result == Decimal("91800")

    def test_convert_with_commission_5_percent(self, mock_rates_config):
        """Конвертация с банковской комиссией 5%."""
        result = _convert(
            amount=Decimal("1000"),
            currency="EUR",
            rates_conf=mock_rates_config,
            bank_commission_percent=5.0,
        )

        # Ожидаем: 1000 × (100.0 × 1.05) = 1000 × 105.0 = 105000
        assert result == Decimal("105000")

    def test_convert_backwards_compatible_none_commission(self, mock_rates_config):
        """Обратная совместимость: bank_commission_percent=None использует базовый курс."""
        result = _convert(
            amount=Decimal("1000"),
            currency="USD",
            rates_conf=mock_rates_config,
            bank_commission_percent=None,
        )

        # Ожидаем базовый курс без комиссии: 1000 × 90.0 = 90000
        assert result == Decimal("90000")


# ============================================================================
# TEST CLASS: _effective_currency_rate()
# ============================================================================


class TestEffectiveCurrencyRate:
    """Тесты для _effective_currency_rate() - эффективный курс с комиссией."""

    def test_zero_commission(self, mock_rates_config):
        """Комиссия 0% → базовый курс."""
        rate = _effective_currency_rate(
            mock_rates_config, "USD", 0.0
        )

        assert rate == Decimal("90")

    def test_commission_2_percent(self, mock_rates_config):
        """Комиссия 2%: base_rate × 1.02."""
        rate = _effective_currency_rate(
            mock_rates_config, "USD", 2.0
        )

        # 90.0 × 1.02 = 91.8
        assert rate == Decimal("91.8")

    def test_commission_5_percent(self, mock_rates_config):
        """Комиссия 5%: base_rate × 1.05."""
        rate = _effective_currency_rate(
            mock_rates_config, "EUR", 5.0
        )

        # 100.0 × 1.05 = 105.0
        assert rate == Decimal("105")

    def test_commission_10_percent_jpy(self, mock_rates_config):
        """Комиссия 10% для JPY: base_rate × 1.10."""
        rate = _effective_currency_rate(
            mock_rates_config, "JPY", 10.0
        )

        # 0.6 × 1.10 = 0.66
        assert rate == Decimal("0.66")


# ============================================================================
# TEST CLASS: _get_bank_commission_percent()
# ============================================================================


class TestGetBankCommissionPercent:
    """Тесты для _get_bank_commission_percent() - извлечение процента банковской комиссии."""

    def test_enabled_true_with_percent(self):
        """enabled=true, percent=2.0 → 2.0."""
        config = {
            "bank_commission": {
                "enabled": True,
                "percent": 2.0,
            }
        }
        result = _get_bank_commission_percent(config)
        assert result == 2.0

    def test_enabled_false(self):
        """enabled=false → 0.0."""
        config = {
            "bank_commission": {
                "enabled": False,
                "percent": 5.0,
            }
        }
        result = _get_bank_commission_percent(config)
        assert result == 0.0

    def test_missing_section(self):
        """Отсутствует секция bank_commission → 0.0."""
        config = {}
        result = _get_bank_commission_percent(config)
        assert result == 0.0

    def test_percent_not_set_use_default(self):
        """percent не задан, есть meta.default_percent → использовать default."""
        config = {
            "bank_commission": {
                "enabled": True,
                "meta": {
                    "default_percent": 3.5,
                }
            }
        }
        result = _get_bank_commission_percent(config)
        assert result == 3.5

    def test_invalid_percent_string(self):
        """Невалидное значение percent (строка) → 0.0 (fallback)."""
        config = {
            "bank_commission": {
                "enabled": True,
                "percent": "invalid",
                "meta": {
                    "default_percent": "also-invalid",
                }
            }
        }
        result = _get_bank_commission_percent(config)
        assert result == 0.0

    def test_invalid_percent_none(self):
        """percent = None, нет default → 0.0."""
        config = {
            "bank_commission": {
                "enabled": True,
                "percent": None,
            }
        }
        result = _get_bank_commission_percent(config)
        assert result == 0.0

    def test_not_dict(self):
        """bank_commission не dict → 0.0."""
        config = {
            "bank_commission": "not a dict"
        }
        result = _get_bank_commission_percent(config)
        assert result == 0.0

