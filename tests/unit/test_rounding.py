"""Юнит-тесты для функций округления.

Тестируемый модуль: app/calculation/rounding.py

Покрытие:
- round_rub(): Округление до целых рублей (ROUND_HALF_UP)
- to_decimal(): Безопасное преобразование в Decimal
- quantize4(): Округление до 4 знаков после запятой

Методология: RPG - детерминированные данные, изолированное тестирование.
"""

from decimal import Decimal, InvalidOperation

import pytest

from app.calculation.rounding import quantize4, round_rub, sum_decimals, to_decimal


class TestRoundRub:
    """Тесты для round_rub()."""

    @pytest.mark.parametrize(
        "input_val,expected",
        [
            # Целые числа
            (Decimal("1000.0"), 1000),
            (Decimal("0.0"), 0),
            # Округление вверх
            (Decimal("1234.56"), 1235),
            (Decimal("1234.51"), 1235),
            (Decimal("1234.99"), 1235),
            # Округление вниз
            (Decimal("1234.44"), 1234),
            (Decimal("1234.01"), 1234),
            (Decimal("1234.49"), 1234),
            # Граница 0.5 (HALF_UP)
            (Decimal("1234.50"), 1235),
            (Decimal("0.50"), 1),
            (Decimal("2.50"), 3),
            (Decimal("3.50"), 4),
            # Отрицательные числа
            (Decimal("-1234.56"), -1235),
            (Decimal("-1234.44"), -1234),
            (Decimal("-1234.50"), -1235),  # HALF_UP для отрицательных
            # Очень большие числа
            (Decimal("99999999.99"), 100000000),
            (Decimal("999999.50"), 1000000),
            # Очень малые числа
            (Decimal("0.01"), 0),
            (Decimal("0.49"), 0),
            (Decimal("0.99"), 1),
        ],
    )
    def test_round_rub(self, input_val, expected):
        """Округление до целых рублей."""
        result = round_rub(input_val)
        assert result == expected
        assert isinstance(result, int)  # Должен возвращать int для JSON

    def test_round_rub_accepts_float(self):
        """round_rub() принимает float."""
        assert round_rub(1234.56) == 1235
        assert round_rub(1234.49) == 1234

    def test_round_rub_accepts_int(self):
        """round_rub() принимает int."""
        assert round_rub(1000) == 1000
        assert round_rub(0) == 0


class TestToDecimal:
    """Тесты для to_decimal()."""

    @pytest.mark.parametrize(
        "input_val,expected_str",
        [
            # int → Decimal
            (1000, "1000"),
            (0, "0"),
            (-500, "-500"),
            # float → Decimal (через str для точности)
            (1234.56, "1234.56"),
            (0.01, "0.01"),
            (99.99, "99.99"),
            # str → Decimal
            ("9876.54", "9876.54"),
            ("1000", "1000"),
            ("0.01", "0.01"),
            ("-500.25", "-500.25"),
            # Научная нотация
            (1.23e5, "123000"),
            (1.23e-2, "0.0123"),
        ],
    )
    def test_to_decimal_valid(self, input_val, expected_str):
        """Валидные преобразования."""
        result = to_decimal(input_val)
        assert isinstance(result, Decimal)
        assert result == Decimal(expected_str)

    def test_to_decimal_already_decimal(self):
        """Если уже Decimal - возвращается как есть."""
        dec = Decimal("1234.56")
        result = to_decimal(dec)
        assert result is dec  # Тот же объект

    @pytest.mark.parametrize(
        "invalid_val",
        [
            "abc",  # Невалидная строка
            "12.34.56",  # Неправильный формат
            "",  # Пустая строка
        ],
    )
    def test_to_decimal_invalid_string(self, invalid_val):
        """Невалидные строки → InvalidOperation."""
        with pytest.raises(InvalidOperation):
            to_decimal(invalid_val)

    def test_to_decimal_none(self):
        """None → InvalidOperation."""
        with pytest.raises(InvalidOperation):
            to_decimal(None)

    def test_to_decimal_list(self):
        """Список → InvalidOperation."""

        with pytest.raises(InvalidOperation):
            to_decimal([1, 2, 3])


class TestQuantize4:
    """Тесты для quantize4()."""

    @pytest.mark.parametrize(
        "input_val,expected_str",
        [
            # Точно 4 знака
            (Decimal("90.1234"), "90.1234"),
            (Decimal("0.1234"), "0.1234"),
            (Decimal("123.4567"), "123.4567"),
            # Меньше 4 знаков - дополняется нулями
            (Decimal("90.12"), "90.1200"),
            (Decimal("90.1"), "90.1000"),
            (Decimal("90"), "90.0000"),
            (Decimal("0.1"), "0.1000"),
            # Больше 4 знаков - округляется
            (Decimal("90.123456"), "90.1235"),
            (Decimal("90.123444"), "90.1234"),
            (Decimal("90.123499"), "90.1235"),
            # Граница 0.00005 (ROUND_HALF_EVEN - banker's rounding)
            (Decimal("90.12345"), "90.1234"),  # 5 округляется к ближайшему чётному
            (Decimal("90.12344"), "90.1234"),
            (Decimal("90.12346"), "90.1235"),
            (Decimal("90.12355"), "90.1236"),  # 5 округляется к ближайшему чётному
            # Очень малые числа
            (Decimal("0.00005"), "0.0000"),  # 5 округляется к ближайшему чётному (0)
            (Decimal("0.00004"), "0.0000"),
            (Decimal("0.00001"), "0.0000"),
            (Decimal("0.00015"), "0.0002"),  # 5 округляется к ближайшему чётному (2)
            # Отрицательные
            (Decimal("-90.12345"), "-90.1234"),  # 5 округляется к ближайшему чётному
            (Decimal("-90.12"), "-90.1200"),
        ],
    )
    def test_quantize4(self, input_val, expected_str):
        """Округление до 4 знаков."""
        result = quantize4(input_val)
        assert isinstance(result, Decimal)
        assert result == Decimal(expected_str)

    def test_quantize4_accepts_float(self):
        """quantize4() принимает float."""
        result = quantize4(90.1234)
        assert result == Decimal("90.1234")

    def test_quantize4_accepts_int(self):
        """quantize4() принимает int."""
        result = quantize4(90)
        assert result == Decimal("90.0000")

    def test_quantize4_currency_rate_scenario(self):
        """Сценарий использования для курса валют."""
        # Курс EUR = 100.123456 RUB
        rate = quantize4(Decimal("100.123456"))
        assert rate == Decimal("100.1235")

        # Курс JPY = 0.5678 RUB
        rate = quantize4(Decimal("0.5678"))
        assert rate == Decimal("0.5678")


class TestSumDecimals:
    """Тесты для sum_decimals()."""

    def test_sum_empty(self):
        """Сумма пустого списка = 0."""
        result = sum_decimals([])
        assert result == Decimal("0")

    def test_sum_single(self):
        """Сумма одного элемента."""
        result = sum_decimals([Decimal("100.50")])
        assert result == Decimal("100.50")

    def test_sum_multiple(self):
        """Сумма нескольких элементов."""
        values = [
            Decimal("100.25"),
            Decimal("200.50"),
            Decimal("300.75"),
        ]
        result = sum_decimals(values)
        assert result == Decimal("601.50")

    def test_sum_precision(self):
        """Проверка точности (нет float drift)."""
        # Классический пример float drift: 0.1 + 0.2 = 0.30000000000000004
        values = [Decimal("0.1"), Decimal("0.2")]
        result = sum_decimals(values)
        assert result == Decimal("0.3")  # Точно 0.3

    def test_sum_large_numbers(self):
        """Сумма больших чисел."""
        values = [
            Decimal("999999.99"),
            Decimal("0.01"),
        ]
        result = sum_decimals(values)
        assert result == Decimal("1000000.00")

    def test_sum_generator(self):
        """sum_decimals() работает с генератором."""
        values = (Decimal(str(i)) for i in range(1, 6))  # 1, 2, 3, 4, 5
        result = sum_decimals(values)
        assert result == Decimal("15")
