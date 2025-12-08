#!/usr/bin/env python3
"""Тест для проверки расчета пошлины с исправленными данными"""
from app.calculation.engine import calculate
from app.calculation.models import CalculationRequest
def test_georgia_2025_1500cc_250hp():
    """
    Тестовый расчет:
    - Грузия, 2025 год (lt3)
    - 1500 см³, 250 л.с.
    - 10,000 USD
    """
    req = CalculationRequest(
        country='georgia',
        year=2025,
        engine_cc=1500,
        engine_power_hp=250,
        purchase_price=10000,
        currency='USD',
        freight_type='open',
        vehicle_type='M1'
    )
    result = calculate(req)
    print('=' * 70)
    print('🔍 ПРОВЕРКА РАСЧЕТА ПОШЛИНЫ')
    print('=' * 70)
    print(f'Страна: Грузия')
    print(f'Год: 2025 (возраст = {result.meta.age_years} лет, категория {result.meta.age_category})')
    print(f'Объём: 1500 см³')
    print(f'Мощность: 250 л.с. ({result.meta.engine_power_kw:.2f} кВт)')
    print(f'Цена: 10,000 USD')
    print()
    print('📊 ДЕТАЛИ РАСЧЕТА:')
    print(f'  Цена в рублях: {result.breakdown.purchase_price_rub:,.0f} ₽')
    print(f'  Таможенная стоимость: {result.meta.customs_value_eur:,.2f} EUR')
    if hasattr(result.meta, 'duty_value_bracket_max_eur') and result.meta.duty_value_bracket_max_eur:
        print(f'  Брэкет пошлины: ≤ {result.meta.duty_value_bracket_max_eur:,.0f} EUR')
    if result.meta.duty_percent:
        print(f'  Процент пошлины: {result.meta.duty_percent * 100:.0f}%')
        duty_by_percent = result.meta.customs_value_eur * result.meta.duty_percent
        print(f'    → Пошлина по проценту: {duty_by_percent:,.2f} EUR')
    if result.meta.duty_min_rate_eur_per_cc:
        print(f'  Мин. ставка: {result.meta.duty_min_rate_eur_per_cc} EUR/см³')
        duty_by_cc = 1500 * result.meta.duty_min_rate_eur_per_cc
        print(f'    → Пошлина по мин. ставке: {duty_by_cc:,.2f} EUR')
    print(f'  Режим расчета: {result.meta.duty_formula_mode}')
    print()
    print('💰 ПОШЛИНА: {0:,.0f} ₽'.format(result.breakdown.duties_rub))
    print()
    print('📋 ПОЛНАЯ ДЕТАЛИЗАЦИЯ:')
    print(f'  • Цена покупки: {result.breakdown.purchase_price_rub:,.0f} ₽')
    print(f'  • Таможенная пошлина: {result.breakdown.duties_rub:,.0f} ₽')
    print(f'  • Утилизационный сбор: {result.breakdown.utilization_fee_rub:,.0f} ₽')
    print(f'    (коэфф. {result.meta.utilization_coefficient})')
    print(f'  • Таможенное оформление: {result.breakdown.customs_services_rub:,.0f} ₽')
    print(f'  • Фрахт: {result.breakdown.freight_rub:,.0f} ₽')
    print(f'  • Расходы в стране: {result.breakdown.country_expenses_rub:,.0f} ₽')
    print(f'  • Комиссия компании: {result.breakdown.company_commission_rub:,.0f} ₽')
    print(f'  • ЭРА-ГЛОНАСС: {result.breakdown.era_glonass_rub:,.0f} ₽')
    print()
    print('💎 ИТОГО: {0:,.0f} ₽'.format(result.breakdown.total_rub))
    print('=' * 70)
    # Assertions для проверки
    assert result.meta.age_category == 'lt3', f"Expected lt3, got {result.meta.age_category}"
    assert result.breakdown.purchase_price_rub == 900000, \
        f"Expected 900,000 RUB, got {result.breakdown.purchase_price_rub}"
    assert result.meta.customs_value_eur == 9000, \
        f"Expected 9,000 EUR, got {result.meta.customs_value_eur}"
    print()
    print('✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!')
if __name__ == '__main__':
    test_georgia_2025_1500cc_250hp()
