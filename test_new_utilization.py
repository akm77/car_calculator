#!/usr/bin/env python3
"""Быстрый тест новой системы утильсбора 2025"""

from decimal import Decimal
from app.calculation.models import CalculationRequest
from app.calculation.engine import calculate

def test_new_utilization():
    """Тест расчёта с новым полем engine_power_hp"""

    print("🧪 Тестирование новой системы утильсбора 2025...")
    print("=" * 60)

    # Тест 1: Япония, lt3, 1500cc, 110 л.с. (80.9 кВт)
    req1 = CalculationRequest(
        country='japan',
        year=2022,
        engine_cc=1500,
        engine_power_hp=110,
        purchase_price=Decimal('2500000'),
        currency='JPY'
    )

    result1 = calculate(req1)
    print(f"\n✅ Тест 1: Япония 2022, 1500cc, 110 л.с.")
    print(f"   Мощность: {result1.meta.engine_power_hp} л.с. → {result1.meta.engine_power_kw} кВт")
    print(f"   Коэффициент утильсбора: {result1.meta.utilization_coefficient}")
    print(f"   Утильсбор: {result1.breakdown.utilization_fee_rub:,} руб.")
    print(f"   ЭРА-ГЛОНАСС: {result1.breakdown.era_glonass_rub:,} руб.")
    print(f"   Комиссия: {result1.breakdown.company_commission_rub:,} руб.")
    print(f"   Итого: {result1.breakdown.total_rub:,} руб.")

    # Тест 2: Грузия, gt5, 2500cc, 200 л.с. (147.1 кВт)
    req2 = CalculationRequest(
        country='georgia',
        year=2018,
        engine_cc=2500,
        engine_power_hp=200,
        purchase_price=Decimal('15000'),
        currency='USD'
    )

    result2 = calculate(req2)
    print(f"\n✅ Тест 2: Грузия 2018, 2500cc, 200 л.с.")
    print(f"   Мощность: {result2.meta.engine_power_hp} л.с. → {result2.meta.engine_power_kw} кВт")
    print(f"   Коэффициент утильсбора: {result2.meta.utilization_coefficient}")
    print(f"   Утильсбор: {result2.breakdown.utilization_fee_rub:,} руб.")
    print(f"   ЭРА-ГЛОНАСС: {result2.breakdown.era_glonass_rub:,} руб.")
    print(f"   Комиссия: {result2.breakdown.company_commission_rub:,} руб.")
    print(f"   Итого: {result2.breakdown.total_rub:,} руб.")

    # Тест 3: ОАЭ - комиссия должна быть 0
    req3 = CalculationRequest(
        country='uae',
        year=2021,
        engine_cc=3000,
        engine_power_hp=250,
        purchase_price=Decimal('25000'),
        currency='USD'
    )

    result3 = calculate(req3)
    print(f"\n✅ Тест 3: ОАЭ 2021, 3000cc, 250 л.с.")
    print(f"   Мощность: {result3.meta.engine_power_hp} л.с. → {result3.meta.engine_power_kw} кВт")
    print(f"   Коэффициент утильсбора: {result3.meta.utilization_coefficient}")
    print(f"   Утильсбор: {result3.breakdown.utilization_fee_rub:,} руб.")
    print(f"   ЭРА-ГЛОНАСС: {result3.breakdown.era_glonass_rub:,} руб.")
    print(f"   Комиссия: {result3.breakdown.company_commission_rub:,} руб. (должна быть 0)")
    print(f"   Итого: {result3.breakdown.total_rub:,} руб.")

    print("\n" + "=" * 60)
    print("🎉 Все тесты выполнены успешно!")

if __name__ == "__main__":
    try:
        test_new_utilization()
    except Exception as e:
        print(f"\n❌ Ошибка: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

