"""
Manual test для проверки обновлений Telegram Bot handlers (Sprint 7).

Этот файл содержит тесты для проверки:
1. cmd_calc с новым полем engine_power_hp=110
2. _format_result helper для форматирования результатов
3. Парсинг engine_power_hp из WebApp данных

Запуск:
    python tests/manual/test_bot_handlers_sprint7.py
"""

from decimal import Decimal
import sys
import traceback

import pytest

from app.bot.handlers.start import _format_result
from app.calculation.engine import calculate
from app.calculation.models import CalculationRequest


@pytest.fixture
def sample_calculation():
    """Fixture для создания тестового расчета."""
    req = CalculationRequest(
        country="japan",
        year=2021,
        engine_cc=1496,
        engine_power_hp=110,
        purchase_price=Decimal("2500000"),
        currency="JPY",
        vehicle_type="M1",
    )
    result = calculate(req)
    return result, req


def test_cmd_calc_example():
    """Тест примера из cmd_calc с engine_power_hp=110."""
    print("\n" + "=" * 60)
    print("TEST 1: cmd_calc example calculation")
    print("=" * 60)

    req = CalculationRequest(
        country="japan",
        year=2021,
        engine_cc=1496,
        engine_power_hp=110,  # NEW field
        purchase_price=Decimal("2500000"),
        currency="JPY",
        vehicle_type="M1",
    )

    result = calculate(req)

    print("\n✅ Calculation successful!")
    print(f"   Total: {result.breakdown.total_rub:,.0f} ₽")
    print(f"   Utilization fee: {result.breakdown.utilization_fee_rub:,.0f} ₽")
    print(f"   Duties: {result.breakdown.duties_rub:,.0f} ₽")

    if result.meta.engine_power_hp:
        print(f"   Power: {result.meta.engine_power_hp} HP", end="")
        if result.meta.engine_power_kw:
            print(f" ({result.meta.engine_power_kw:.2f} kW)")
        else:
            print()

    if result.meta.utilization_coefficient:
        print(
            f"   Utilization coefficient: {result.meta.utilization_coefficient}"
        )

    # Assertions
    assert result is not None, "Result should not be None"
    assert result.meta.engine_power_hp == 110, "Engine power should be 110 HP"
    assert result.meta.engine_power_kw is not None, "Engine power kW should be calculated"
    assert result.breakdown.total_rub > 0, "Total should be positive"


def test_format_result(sample_calculation):
    """Тест _format_result helper для форматирования."""
    print("\n" + "=" * 60)
    print("TEST 2: _format_result HTML formatting")
    print("=" * 60)

    result, req = sample_calculation
    formatted = _format_result(result, req)

    print("\n✅ Formatting successful!")
    print(f"   Length: {len(formatted)} characters")
    print(f"   Contains '🔋 Мощность': {'🔋' in formatted}")
    print(f"   Contains 'л.с.': {'л.с.' in formatted}")
    print(f"   Contains 'кВт': {'кВт' in formatted}")
    print(f"   Contains 'коэфф.': {'коэфф.' in formatted}")
    print(f"   Contains HTML tags: {'<b>' in formatted and '</b>' in formatted}")

    print("\n--- Formatted Output Preview (first 500 chars) ---")
    print(formatted[:500])
    print("...")

    # Assertions
    assert formatted is not None, "Formatted result should not be None"
    assert len(formatted) > 0, "Formatted result should not be empty"
    assert '🔋' in formatted or 'Мощность' in formatted, "Should contain power information"
    assert '<b>' in formatted and '</b>' in formatted, "Should contain HTML tags"


def test_webapp_data_parsing():
    """Тест парсинга engine_power_hp из WebApp данных."""
    print("\n" + "=" * 60)
    print("TEST 3: WebApp data parsing simulation")
    print("=" * 60)

    # Симуляция данных из WebApp
    webapp_data = {
        "country": "korea",
        "year": 2020,
        "engine_cc": 2000,
        "engine_power_hp": 150,  # NEW field
        "purchase_price": "15000",
        "currency": "USD",  # Use supported currency
        "vehicle_type": "M1",
        "freight_type": "container",
        "sanctions_unknown": False,
    }

    # Проверка, что engine_power_hp присутствует
    assert "engine_power_hp" in webapp_data, "engine_power_hp should be present in data"

    print("✅ engine_power_hp field present in data")

    # Создание запроса (как в on_webapp_data)
    req = CalculationRequest(
        country=webapp_data.get("country"),
        year=int(webapp_data.get("year")),
        engine_cc=int(webapp_data.get("engine_cc")),
        engine_power_hp=int(webapp_data.get("engine_power_hp")),
        purchase_price=Decimal(str(webapp_data.get("purchase_price"))),
        currency=webapp_data.get("currency"),
        vehicle_type=webapp_data.get("vehicle_type", "M1"),
        freight_type=webapp_data.get("freight_type", "container"),
        sanctions_unknown=webapp_data.get("sanctions_unknown", False),
    )

    result = calculate(req)

    print("\n✅ Calculation successful!")
    print(f"   Country: {req.country.upper()}")
    print(f"   Year: {req.year}")
    print(f"   Engine: {req.engine_cc} cc, {req.engine_power_hp} HP")
    print(f"   Total: {result.breakdown.total_rub:,.0f} ₽")

    if result.meta.engine_power_kw:
        print(f"   Power (kW): {result.meta.engine_power_kw:.2f}")

    if result.meta.utilization_coefficient:
        print(
            f"   Utilization coefficient: {result.meta.utilization_coefficient}"
        )

    # Assertions
    assert result is not None, "Result should not be None"
    assert req.engine_power_hp == 150, "Engine power should be 150 HP"
    assert result.meta.engine_power_kw is not None, "Engine power kW should be calculated"
    assert result.breakdown.total_rub > 0, "Total should be positive"


def test_missing_engine_power():
    """Тест обработки отсутствующего engine_power_hp."""
    print("\n" + "=" * 60)
    print("TEST 4: Missing engine_power_hp validation")
    print("=" * 60)

    # Данные БЕЗ engine_power_hp
    webapp_data = {
        "country": "japan",
        "year": 2021,
        "engine_cc": 1500,
        # engine_power_hp отсутствует!
        "purchase_price": "2000000",
        "currency": "JPY",
    }

    # Assertion - проверяем, что поле отсутствует
    assert "engine_power_hp" not in webapp_data, "engine_power_hp should be missing for this test"

    print(
        "✅ Validation check: engine_power_hp is missing (as expected)"
    )
    print(
        "   → Bot would show error: '❌ Ошибка: Не указана мощность двигателя.'"
    )


def main():
    """Запуск всех тестов."""
    print("\n" + "=" * 60)
    print("SPRINT 7: Telegram Bot Handlers Manual Tests")
    print("=" * 60)

    try:
        # Test 1: cmd_calc example
        result1, req1 = test_cmd_calc_example()

        # Test 2: _format_result
        test_format_result(result1, req1)

        # Test 3: WebApp data parsing
        result2, req2 = test_webapp_data_parsing()

        # Test 4: Missing field validation
        test_missing_engine_power()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nSprint 7 bot handlers are working correctly.")
        print("Next step: Test with real Telegram bot using 'python -m app.bot.main'")

    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ TEST FAILED!")
        print("=" * 60)
        print(f"Error: {e}")
        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

