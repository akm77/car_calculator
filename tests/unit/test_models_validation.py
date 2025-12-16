"""Юнит-тесты валидации CalculationRequest."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from pydantic import ValidationError
import pytest

from app.calculation.models import CalculationRequest


class TestYearValidation:
    """Тесты для поля year."""

    def test_valid_year_current(self):
        """Текущий год — валиден."""
        current_year = datetime.now(UTC).year
        req = CalculationRequest(
            country="japan",
            year=current_year,
            engine_cc=2000,
            engine_power_hp=150,
            purchase_price=Decimal("1000000"),
            currency="JPY",
        )
        assert req.year == current_year

    def test_valid_year_1990(self):
        """1990 — минимально допустимый год."""
        req = CalculationRequest(
            country="japan",
            year=1990,
            engine_cc=2000,
            engine_power_hp=150,
            purchase_price=Decimal("1000000"),
            currency="JPY",
        )
        assert req.year == 1990

    @pytest.mark.parametrize("year", [1991, 2000, 2010, 2020])
    def test_valid_year_range(self, year):
        """Валидные годы в диапазоне."""
        req = CalculationRequest(
            country="japan",
            year=year,
            engine_cc=2000,
            engine_power_hp=150,
            purchase_price=Decimal("1000000"),
            currency="JPY",
        )
        assert req.year == year

    def test_invalid_year_future(self):
        """Год в будущем — ошибка."""
        future_year = datetime.now(UTC).year + 1
        with pytest.raises(ValidationError) as exc_info:
            CalculationRequest(
                country="japan",
                year=future_year,
                engine_cc=2000,
                engine_power_hp=150,
                purchase_price=Decimal("1000000"),
                currency="JPY",
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("year",) for e in errors)
        assert any("future" in str(e["msg"]).lower() for e in errors)

    def test_invalid_year_too_old(self):
        """Год < 1990 — ошибка."""
        with pytest.raises(ValidationError) as exc_info:
            CalculationRequest(
                country="japan",
                year=1989,
                engine_cc=2000,
                engine_power_hp=150,
                purchase_price=Decimal("1000000"),
                currency="JPY",
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("year",) for e in errors)
        assert any("old" in str(e["msg"]).lower() for e in errors)

    @pytest.mark.parametrize("year", [1800, 1950, 1980, 1989])
    def test_invalid_year_too_old_range(self, year):
        """Различные старые годы — ошибка."""
        with pytest.raises(ValidationError):
            CalculationRequest(
                country="japan",
                year=year,
                engine_cc=2000,
                engine_power_hp=150,
                purchase_price=Decimal("1000000"),
                currency="JPY",
            )

    def test_year_type_string_coerced(self):
        """Строковый год конвертируется в int (Pydantic coercion)."""
        req = CalculationRequest(
            country="japan",
            year="2020",  # type: ignore
            engine_cc=2000,
            engine_power_hp=150,
            purchase_price=Decimal("1000000"),
            currency="JPY",
        )
        assert req.year == 2020
        assert isinstance(req.year, int)

    def test_invalid_year_type_float(self):
        """Неверный тип года (float) — ошибка."""
        with pytest.raises(ValidationError):
            CalculationRequest(
                country="japan",
                year=2020.5,  # type: ignore
                engine_cc=2000,
                engine_power_hp=150,
                purchase_price=Decimal("1000000"),
                currency="JPY",
            )


class TestEngineCcValidation:
    """Тесты для поля engine_cc (объём двигателя)."""

    @pytest.mark.parametrize("cc", [500, 1000, 1500, 2000, 3000, 5000, 8000, 10000])
    def test_valid_engine_cc(self, cc):
        """Валидные значения объёма двигателя."""
        req = CalculationRequest(
            country="japan",
            year=2020,
            engine_cc=cc,
            engine_power_hp=150,
            purchase_price=Decimal("1000000"),
            currency="JPY",
        )
        assert req.engine_cc == cc

    def test_invalid_engine_cc_zero(self):
        """Нулевой объём — ошибка."""
        with pytest.raises(ValidationError) as exc_info:
            CalculationRequest(
                country="japan",
                year=2020,
                engine_cc=0,
                engine_power_hp=150,
                purchase_price=Decimal("1000000"),
                currency="JPY",
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("engine_cc",) for e in errors)

    def test_invalid_engine_cc_negative(self):
        """Отрицательный объём — ошибка."""
        with pytest.raises(ValidationError):
            CalculationRequest(
                country="japan",
                year=2020,
                engine_cc=-1000,
                engine_power_hp=150,
                purchase_price=Decimal("1000000"),
                currency="JPY",
            )

    def test_invalid_engine_cc_too_high(self):
        """Объём выше максимума (10000) — ошибка."""
        with pytest.raises(ValidationError) as exc_info:
            CalculationRequest(
                country="japan",
                year=2020,
                engine_cc=10001,
                engine_power_hp=150,
                purchase_price=Decimal("1000000"),
                currency="JPY",
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("engine_cc",) for e in errors)

    @pytest.mark.parametrize("cc", [15000, 20000, 100000])
    def test_invalid_engine_cc_extremely_high(self, cc):
        """Экстремально высокий объём — ошибка."""
        with pytest.raises(ValidationError):
            CalculationRequest(
                country="japan",
                year=2020,
                engine_cc=cc,
                engine_power_hp=150,
                purchase_price=Decimal("1000000"),
                currency="JPY",
            )


class TestEnginePowerHpValidation:
    """Тесты для обязательного поля engine_power_hp."""

    @pytest.mark.parametrize("hp", [1, 50, 100, 150, 300, 500, 1000, 1500])
    def test_valid_power(self, hp):
        """Валидные значения мощности."""
        req = CalculationRequest(
            country="japan",
            year=2020,
            engine_cc=2000,
            engine_power_hp=hp,
            purchase_price=Decimal("1000000"),
            currency="JPY",
        )
        assert req.engine_power_hp == hp

    def test_invalid_power_zero(self):
        """Нулевая мощность — ошибка."""
        with pytest.raises(ValidationError) as exc_info:
            CalculationRequest(
                country="japan",
                year=2020,
                engine_cc=2000,
                engine_power_hp=0,
                purchase_price=Decimal("1000000"),
                currency="JPY",
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("engine_power_hp",) for e in errors)

    def test_invalid_power_negative(self):
        """Отрицательная мощность — ошибка."""
        with pytest.raises(ValidationError):
            CalculationRequest(
                country="japan",
                year=2020,
                engine_cc=2000,
                engine_power_hp=-10,
                purchase_price=Decimal("1000000"),
                currency="JPY",
            )

    def test_invalid_power_too_high(self):
        """Мощность выше максимума (1500) — ошибка."""
        with pytest.raises(ValidationError) as exc_info:
            CalculationRequest(
                country="japan",
                year=2020,
                engine_cc=2000,
                engine_power_hp=1501,
                purchase_price=Decimal("1000000"),
                currency="JPY",
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("engine_power_hp",) for e in errors)

    @pytest.mark.parametrize("hp", [2000, 5000, 10000])
    def test_invalid_power_extremely_high(self, hp):
        """Экстремально высокая мощность — ошибка."""
        with pytest.raises(ValidationError):
            CalculationRequest(
                country="japan",
                year=2020,
                engine_cc=2000,
                engine_power_hp=hp,
                purchase_price=Decimal("1000000"),
                currency="JPY",
            )


class TestPurchasePriceValidation:
    """Тесты для поля purchase_price."""

    @pytest.mark.parametrize(
        "price",
        [
            Decimal("1"),
            Decimal("1000"),
            Decimal("500000"),
            Decimal("1000000"),
            Decimal("10000000"),
            Decimal("100000000"),
        ],
    )
    def test_valid_purchase_price(self, price):
        """Валидные значения стоимости."""
        req = CalculationRequest(
            country="japan",
            year=2020,
            engine_cc=2000,
            engine_power_hp=150,
            purchase_price=price,
            currency="JPY",
        )
        assert req.purchase_price == price

    def test_invalid_purchase_price_zero(self):
        """Нулевая стоимость — ошибка."""
        with pytest.raises(ValidationError) as exc_info:
            CalculationRequest(
                country="japan",
                year=2020,
                engine_cc=2000,
                engine_power_hp=150,
                purchase_price=Decimal("0"),
                currency="JPY",
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("purchase_price",) for e in errors)

    def test_invalid_purchase_price_negative(self):
        """Отрицательная стоимость — ошибка."""
        with pytest.raises(ValidationError):
            CalculationRequest(
                country="japan",
                year=2020,
                engine_cc=2000,
                engine_power_hp=150,
                purchase_price=Decimal("-1000"),
                currency="JPY",
            )

    @pytest.mark.parametrize("price", [Decimal("-1"), Decimal("-100000"), Decimal("-9999999")])
    def test_invalid_purchase_price_negative_range(self, price):
        """Различные отрицательные стоимости — ошибка."""
        with pytest.raises(ValidationError):
            CalculationRequest(
                country="japan",
                year=2020,
                engine_cc=2000,
                engine_power_hp=150,
                purchase_price=price,
                currency="JPY",
            )


class TestCurrencyValidation:
    """Тесты для поля currency."""

    @pytest.mark.parametrize("currency", ["RUB", "USD", "EUR", "JPY", "CNY", "AED"])
    def test_valid_currency_uppercase(self, currency):
        """Валидные валюты в верхнем регистре."""
        req = CalculationRequest(
            country="japan",
            year=2020,
            engine_cc=2000,
            engine_power_hp=150,
            purchase_price=Decimal("1000000"),
            currency=currency,
        )
        assert req.currency == currency

    @pytest.mark.parametrize("currency", ["rub", "usd", "eur", "jpy", "cny", "aed"])
    def test_valid_currency_lowercase_normalized(self, currency):
        """Валюты в нижнем регистре нормализуются в верхний."""
        req = CalculationRequest(
            country="japan",
            year=2020,
            engine_cc=2000,
            engine_power_hp=150,
            purchase_price=Decimal("1000000"),
            currency=currency,
        )
        assert req.currency == currency.upper()

    @pytest.mark.parametrize("currency", ["Rub", "UsD", "EuR", "jPy"])
    def test_valid_currency_mixed_case_normalized(self, currency):
        """Валюты в смешанном регистре нормализуются."""
        req = CalculationRequest(
            country="japan",
            year=2020,
            engine_cc=2000,
            engine_power_hp=150,
            purchase_price=Decimal("1000000"),
            currency=currency,
        )
        assert req.currency == currency.upper()

    def test_currency_with_whitespace_normalized(self):
        """Валюта с пробелами нормализуется."""
        req = CalculationRequest(
            country="japan",
            year=2020,
            engine_cc=2000,
            engine_power_hp=150,
            purchase_price=Decimal("1000000"),
            currency="  JPY  ",
        )
        assert req.currency == "JPY"


class TestCountryValidation:
    """Тесты для поля country."""

    @pytest.mark.parametrize("country", ["japan", "korea", "uae", "china", "georgia"])
    def test_valid_country_lowercase(self, country):
        """Валидные страны в нижнем регистре."""
        req = CalculationRequest(
            country=country,  # type: ignore
            year=2020,
            engine_cc=2000,
            engine_power_hp=150,
            purchase_price=Decimal("1000000"),
            currency="JPY",
        )
        assert req.country == country

    def test_invalid_country_usa(self):
        """Неподдерживаемая страна (USA) — ошибка."""
        with pytest.raises(ValidationError) as exc_info:
            CalculationRequest(
                country="usa",  # type: ignore
                year=2020,
                engine_cc=2000,
                engine_power_hp=150,
                purchase_price=Decimal("1000000"),
                currency="USD",
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("country",) for e in errors)

    @pytest.mark.parametrize("country", ["germany", "france", "uk", "canada", "mexico"])
    def test_invalid_country_unsupported(self, country):
        """Различные неподдерживаемые страны — ошибка."""
        with pytest.raises(ValidationError):
            CalculationRequest(
                country=country,  # type: ignore
                year=2020,
                engine_cc=2000,
                engine_power_hp=150,
                purchase_price=Decimal("1000000"),
                currency="USD",
            )


class TestFreightTypeValidation:
    """Тесты для поля freight_type."""

    @pytest.mark.parametrize("freight_type", ["standard", "open", "container"])
    def test_valid_freight_type(self, freight_type):
        """Валидные типы транспортировки."""
        req = CalculationRequest(
            country="japan",
            year=2020,
            engine_cc=2000,
            engine_power_hp=150,
            purchase_price=Decimal("1000000"),
            currency="JPY",
            freight_type=freight_type,  # type: ignore
        )
        assert req.freight_type == freight_type

    def test_freight_type_none_default(self):
        """freight_type может быть None (опциональное поле)."""
        req = CalculationRequest(
            country="japan",
            year=2020,
            engine_cc=2000,
            engine_power_hp=150,
            purchase_price=Decimal("1000000"),
            currency="JPY",
        )
        assert req.freight_type is None

    def test_invalid_freight_type_express(self):
        """Неподдерживаемый тип транспортировки (express) — ошибка."""
        with pytest.raises(ValidationError) as exc_info:
            CalculationRequest(
                country="japan",
                year=2020,
                engine_cc=2000,
                engine_power_hp=150,
                purchase_price=Decimal("1000000"),
                currency="JPY",
                freight_type="express",  # type: ignore
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("freight_type",) for e in errors)

    @pytest.mark.parametrize("freight_type", ["fast", "slow", "air", "sea"])
    def test_invalid_freight_type_unsupported(self, freight_type):
        """Различные неподдерживаемые типы транспортировки — ошибка."""
        with pytest.raises(ValidationError):
            CalculationRequest(
                country="japan",
                year=2020,
                engine_cc=2000,
                engine_power_hp=150,
                purchase_price=Decimal("1000000"),
                currency="JPY",
                freight_type=freight_type,  # type: ignore
            )


class TestVehicleTypeValidation:
    """Тесты для поля vehicle_type."""

    @pytest.mark.parametrize("vehicle_type", ["M1", "pickup", "bus", "motorhome", "other"])
    def test_valid_vehicle_type(self, vehicle_type):
        """Валидные типы транспортных средств."""
        req = CalculationRequest(
            country="japan",
            year=2020,
            engine_cc=2000,
            engine_power_hp=150,
            purchase_price=Decimal("1000000"),
            currency="JPY",
            vehicle_type=vehicle_type,  # type: ignore
        )
        assert req.vehicle_type == vehicle_type

    def test_vehicle_type_default_m1(self):
        """По умолчанию vehicle_type = M1."""
        req = CalculationRequest(
            country="japan",
            year=2020,
            engine_cc=2000,
            engine_power_hp=150,
            purchase_price=Decimal("1000000"),
            currency="JPY",
        )
        assert req.vehicle_type == "M1"

    def test_invalid_vehicle_type_truck(self):
        """Неподдерживаемый тип ТС (truck) — ошибка."""
        with pytest.raises(ValidationError) as exc_info:
            CalculationRequest(
                country="japan",
                year=2020,
                engine_cc=2000,
                engine_power_hp=150,
                purchase_price=Decimal("1000000"),
                currency="JPY",
                vehicle_type="truck",  # type: ignore
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("vehicle_type",) for e in errors)


class TestSanctionsUnknownValidation:
    """Тесты для поля sanctions_unknown."""

    @pytest.mark.parametrize("sanctions_unknown", [True, False])
    def test_valid_sanctions_unknown(self, sanctions_unknown):
        """Валидные значения sanctions_unknown."""
        req = CalculationRequest(
            country="japan",
            year=2020,
            engine_cc=2000,
            engine_power_hp=150,
            purchase_price=Decimal("1000000"),
            currency="JPY",
            sanctions_unknown=sanctions_unknown,
        )
        assert req.sanctions_unknown is sanctions_unknown

    def test_sanctions_unknown_default_false(self):
        """По умолчанию sanctions_unknown = False."""
        req = CalculationRequest(
            country="japan",
            year=2020,
            engine_cc=2000,
            engine_power_hp=150,
            purchase_price=Decimal("1000000"),
            currency="JPY",
        )
        assert req.sanctions_unknown is False

    def test_sanctions_unknown_type_string_coerced(self):
        """Непустая строка sanctions_unknown конвертируется в True (Pydantic coercion)."""
        req = CalculationRequest(
            country="japan",
            year=2020,
            engine_cc=2000,
            engine_power_hp=150,
            purchase_price=Decimal("1000000"),
            currency="JPY",
            sanctions_unknown="yes",  # type: ignore
        )
        assert req.sanctions_unknown is True
        assert isinstance(req.sanctions_unknown, bool)
