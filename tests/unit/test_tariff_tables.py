"""Юнит-тесты для функций поиска ставок.

Тестируемый модуль: app/calculation/tariff_tables.py

Покрытие:
- get_age_category(): Определение возрастной категории ("lt3", "3_5", "gt5")
- find_duty_rate(): Поиск ставки пошлины по возрасту и объёму
- find_lt3_value_bracket(): Поиск брэкета по таможенной стоимости (≤3 лет)
- get_passing_category(): Определение категории "проходные" / "непроходные"
- format_volume_band(): Форматирование диапазона объёма

Методология: RPG - детерминированные данные, параметризованные тесты.
"""
from decimal import Decimal

import pytest

from app.calculation.tariff_tables import (
    find_duty_rate,
    find_lt3_value_bracket,
    format_volume_band,
    get_age_category,
    get_passing_category,
)
from app.core.settings import get_configs


@pytest.fixture(scope="module")
def duties_config():
    """Конфигурация пошлин."""
    return get_configs().duties


@pytest.fixture(scope="module")
def rates_config():
    """Конфигурация курсов и утильсбора."""
    return get_configs().rates


class TestGetAgeCategory:
    """Тесты для get_age_category()."""

    @pytest.mark.parametrize("age_years,expected_category", [
        # < 3 лет
        (0, "lt3"),
        (1, "lt3"),
        (2, "lt3"),

        # Ровно 3 года (граница)
        (3, "3_5"),

        # 3-5 лет
        (4, "3_5"),
        (5, "3_5"),

        # Ровно 5 лет (граница)
        (5, "3_5"),

        # > 5 лет
        (6, "gt5"),
        (7, "gt5"),
        (10, "gt5"),
        (20, "gt5"),
        (35, "gt5"),  # Очень старое авто
    ])
    def test_age_category(self, age_years, expected_category):
        """Определение возрастной категории."""
        result = get_age_category(age_years)
        assert result == expected_category

    def test_age_boundary_lt3_to_3_5(self):
        """Граница между lt3 и 3_5."""
        assert get_age_category(2) == "lt3"
        assert get_age_category(3) == "3_5"

    def test_age_boundary_3_5_to_gt5(self):
        """Граница между 3_5 и gt5."""
        assert get_age_category(5) == "3_5"
        assert get_age_category(6) == "gt5"


class TestGetPassingCategory:
    """Тесты для get_passing_category()."""

    @pytest.mark.parametrize("age_category,expected", [
        ("lt3", "non_passing"),
        ("3_5", "passing"),
        ("gt5", "non_passing"),
    ])
    def test_passing_category(self, age_category, expected):
        """Определение категории проходные/непроходные."""
        result = get_passing_category(age_category)
        assert result == expected


class TestFindDutyRate:
    """Тесты для find_duty_rate()."""

    def test_find_duty_lt3_not_used_directly(self, duties_config):
        """Для lt3 не используется find_duty_rate (используются value_brackets)."""
        # lt3 в duties.yml не имеет поля "bands", только "value_brackets"
        rate = find_duty_rate(duties_config, "lt3", 1500)
        # Должно вернуть None, т.к. нет bands
        assert rate is None

    @pytest.mark.parametrize("engine_cc,expected_rate", [
        # ≤ 1000 cc
        (500, 1.5),
        (1000, 1.5),

        # 1001-1500 cc
        (1001, 1.7),
        (1250, 1.7),
        (1500, 1.7),

        # 1501-1800 cc
        (1501, 2.5),
        (1800, 2.5),

        # 1801-2300 cc
        (1801, 2.7),
        (2000, 2.7),
        (2300, 2.7),

        # 2301-3000 cc
        (2301, 3.0),
        (2500, 3.0),
        (3000, 3.0),

        # > 3000 cc
        (3001, 3.6),
        (3500, 3.6),
        (5000, 3.6),
    ])
    def test_find_duty_3_5(self, duties_config, engine_cc, expected_rate):
        """Для 3_5 возвращается rate_per_cc (float)."""
        rate = find_duty_rate(duties_config, "3_5", engine_cc)
        assert isinstance(rate, (float, int))
        assert rate == expected_rate

    @pytest.mark.parametrize("engine_cc,expected_rate", [
        # ≤ 1000 cc
        (500, 3.0),
        (1000, 3.0),

        # 1001-1500 cc
        (1001, 3.2),
        (1250, 3.2),
        (1500, 3.2),

        # 1501-1800 cc
        (1501, 3.5),
        (1800, 3.5),

        # 1801-2300 cc
        (1801, 4.8),
        (2000, 4.8),
        (2300, 4.8),

        # 2301-3000 cc
        (2301, 5.0),
        (2500, 5.0),
        (3000, 5.0),

        # > 3000 cc
        (3001, 5.7),
        (3500, 5.7),
        (5000, 5.7),
    ])
    def test_find_duty_gt5(self, duties_config, engine_cc, expected_rate):
        """Для gt5 возвращается rate_per_cc (float)."""
        rate = find_duty_rate(duties_config, "gt5", engine_cc)
        assert isinstance(rate, (float, int))
        assert rate == expected_rate

    def test_find_duty_unknown_category(self, duties_config):
        """Неизвестная категория → None."""
        rate = find_duty_rate(duties_config, "unknown", 1500)
        assert rate is None

    def test_find_duty_boundary_values(self, duties_config):
        """Граничные значения объёма."""
        # 3_5: граница 1000 cc
        assert find_duty_rate(duties_config, "3_5", 1000) == 1.5
        assert find_duty_rate(duties_config, "3_5", 1001) == 1.7

        # 3_5: граница 1500 cc
        assert find_duty_rate(duties_config, "3_5", 1500) == 1.7
        assert find_duty_rate(duties_config, "3_5", 1501) == 2.5

        # 3_5: граница 1800 cc
        assert find_duty_rate(duties_config, "3_5", 1800) == 2.5
        assert find_duty_rate(duties_config, "3_5", 1801) == 2.7


class TestFindLt3ValueBracket:
    """Тесты для find_lt3_value_bracket()."""

    @pytest.mark.parametrize("customs_value_eur,expected_percent,expected_min", [
        # < 8500 EUR
        (1000, 0.54, 2.5),
        (5000, 0.54, 2.5),
        (8000, 0.54, 2.5),
        (8499.99, 0.54, 2.5),

        # 8500 EUR (граница - попадает в первый брэкет)
        (8500, 0.54, 2.5),

        # 8500-16700 EUR
        (8500.01, 0.48, 3.5),
        (9000, 0.48, 3.5),
        (10000, 0.48, 3.5),
        (15000, 0.48, 3.5),
        (16699.99, 0.48, 3.5),

        # 16700 EUR (граница - попадает во второй брэкет)
        (16700, 0.48, 3.5),

        # 16700-42300 EUR
        (16700.01, 0.48, 5.5),
        (20000, 0.48, 5.5),
        (30000, 0.48, 5.5),
        (42299.99, 0.48, 5.5),

        # 42300 EUR (граница - попадает в третий брэкет)
        (42300, 0.48, 5.5),

        # 42300-84500 EUR
        (42300.01, 0.48, 7.5),
        (50000, 0.48, 7.5),
        (70000, 0.48, 7.5),
        (84499.99, 0.48, 7.5),

        # 84500 EUR (граница - попадает в четвертый брэкет)
        (84500, 0.48, 7.5),

        # 84500-169000 EUR
        (84500.01, 0.48, 15.0),
        (90000, 0.48, 15.0),
        (100000, 0.48, 15.0),
        (150000, 0.48, 15.0),
        (168999.99, 0.48, 15.0),

        # 169000 EUR (граница - попадает в пятый брэкет)
        (169000, 0.48, 15),

        # > 169000 EUR
        (170000, 0.48, 20.0),
        (200000, 0.48, 20.0),
        (500000, 0.48, 20.0),
        (1000000, 0.48, 20.0),
    ])
    def test_lt3_bracket(self, duties_config, customs_value_eur, expected_percent, expected_min):
        """Поиск брэкета по таможенной стоимости."""
        bracket = find_lt3_value_bracket(duties_config, customs_value_eur)
        assert bracket is not None
        assert bracket["percent"] == expected_percent
        assert bracket["min_rate_eur_per_cc"] == expected_min

    def test_lt3_bracket_exact_boundaries(self, duties_config):
        """Точные граничные значения."""
        # Границы попадают в брэкет с max_customs_value_eur равным этому значению
        # т.е. используется логика <=
        boundaries = [8500, 16700, 42300, 84500, 169000]
        expected_mins = [2.5, 3.5, 5.5, 7.5, 15]  # Значение на границе попадает в текущий брэкет

        for boundary, expected_min in zip(boundaries, expected_mins, strict=True):
            bracket = find_lt3_value_bracket(duties_config, boundary)
            assert bracket["min_rate_eur_per_cc"] == expected_min

    def test_lt3_bracket_zero(self, duties_config):
        """Нулевая стоимость → первый брэкет."""
        bracket = find_lt3_value_bracket(duties_config, 0)
        assert bracket["percent"] == 0.54
        assert bracket["min_rate_eur_per_cc"] == 2.5

    def test_lt3_bracket_very_small(self, duties_config):
        """Очень малая стоимость."""
        bracket = find_lt3_value_bracket(duties_config, 0.01)
        assert bracket["percent"] == 0.54
        assert bracket["min_rate_eur_per_cc"] == 2.5

    def test_lt3_bracket_returns_dict(self, duties_config):
        """Возвращается словарь с нужными ключами."""
        bracket = find_lt3_value_bracket(duties_config, 10000)
        assert isinstance(bracket, dict)
        assert "percent" in bracket
        assert "min_rate_eur_per_cc" in bracket


class TestFormatVolumeBand:
    """Тесты для format_volume_band()."""

    def test_format_lt3_returns_marker(self, duties_config):
        """Для lt3 возвращается маркер 'value_brackets'."""
        result = format_volume_band(duties_config, "lt3", 1500)
        assert result == "value_brackets"

    @pytest.mark.parametrize("engine_cc,expected_pattern", [
        (500, "<= 1000"),
        (1000, "<= 1000"),
        (1001, "<= 1500"),
        (1500, "<= 1500"),
        (1501, "<= 1800"),
        (1800, "<= 1800"),
        (1801, "<= 2300"),
        (2300, "<= 2300"),
        (2301, "<= 3000"),
        (3000, "<= 3000"),
        (3001, "> last"),
        (5000, "> last"),
    ])
    def test_format_volume_band_3_5(self, duties_config, engine_cc, expected_pattern):
        """Форматирование диапазона для 3_5."""
        result = format_volume_band(duties_config, "3_5", engine_cc)
        assert expected_pattern in result
        assert "@" in result  # Должен содержать ставку

    @pytest.mark.parametrize("engine_cc", [500, 1500, 2500, 3500, 5000])
    def test_format_volume_band_gt5(self, duties_config, engine_cc):
        """Форматирование диапазона для gt5."""
        result = format_volume_band(duties_config, "gt5", engine_cc)
        assert isinstance(result, str)
        # Должен содержать либо "<=" либо "> last"
        assert ("<=" in result) or ("> last" in result)

    def test_format_volume_band_unknown_category(self, duties_config):
        """Неизвестная категория → 'n/a'."""
        result = format_volume_band(duties_config, "unknown", 1500)
        assert result == "n/a"


class TestEdgeCases:
    """Тесты граничных случаев и нестандартных ситуаций."""

    def test_age_category_negative(self):
        """Отрицательный возраст (недопустимо, но проверяем)."""
        # В реальной системе такого быть не должно
        result = get_age_category(-1)
        # Технически < 3, поэтому "lt3"
        assert result == "lt3"

    def test_age_category_very_old(self):
        """Очень старое авто (100 лет)."""
        result = get_age_category(100)
        assert result == "gt5"

    def test_find_duty_rate_minimal_cc(self, duties_config):
        """Минимальный объём двигателя."""
        rate = find_duty_rate(duties_config, "3_5", 1)
        assert rate == 1.5  # Попадает в первый диапазон

    def test_find_duty_rate_huge_cc(self, duties_config):
        """Огромный объём двигателя."""
        rate = find_duty_rate(duties_config, "3_5", 10000)
        # Должен попасть в последний диапазон (> 3000)
        assert rate == 3.6

    def test_lt3_bracket_negative_value(self, duties_config):
        """Отрицательная стоимость (недопустимо)."""
        # В реальной системе не должно происходить
        bracket = find_lt3_value_bracket(duties_config, -1000)
        # Технически попадёт в первый брэкет
        assert bracket["percent"] == 0.54

    def test_find_duty_rate_empty_config(self):
        """Пустая конфигурация."""
        empty_config = {"age_categories": {}}
        rate = find_duty_rate(empty_config, "3_5", 1500)
        assert rate is None

    def test_find_lt3_bracket_empty_config(self):
        """Пустая конфигурация для lt3."""
        empty_config = {"age_categories": {"lt3": {}}}
        bracket = find_lt3_value_bracket(empty_config, 10000)
        assert bracket is None

    def test_find_lt3_bracket_no_brackets(self):
        """Конфигурация lt3 без value_brackets."""
        config = {"age_categories": {"lt3": {"value_brackets": []}}}
        bracket = find_lt3_value_bracket(config, 10000)
        assert bracket is None


class TestDecimalCompatibility:
    """Тесты совместимости с Decimal."""

    def test_find_lt3_bracket_with_decimal(self, duties_config):
        """find_lt3_value_bracket() работает с Decimal."""
        bracket = find_lt3_value_bracket(duties_config, Decimal("10000.50"))
        assert bracket is not None
        assert bracket["percent"] == 0.48
        assert bracket["min_rate_eur_per_cc"] == 3.5

    def test_find_lt3_bracket_boundary_with_decimal(self, duties_config):
        """Граничное значение с Decimal."""
        # Ровно 8500.00 - попадает в брэкет <= 8500
        bracket = find_lt3_value_bracket(duties_config, Decimal("8500.00"))
        assert bracket["min_rate_eur_per_cc"] == 2.5

        # Чуть меньше 8500
        bracket = find_lt3_value_bracket(duties_config, Decimal("8499.99"))
        assert bracket["min_rate_eur_per_cc"] == 2.5

    def test_find_lt3_bracket_precision(self, duties_config):
        """Проверка точности с малыми значениями."""
        bracket = find_lt3_value_bracket(duties_config, Decimal("8500.001"))
        assert bracket["min_rate_eur_per_cc"] == 3.5  # Больше 8500 → следующий брэкет

