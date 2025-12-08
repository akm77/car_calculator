#!/usr/bin/env python3
"""
Исследование оптимального возраста автомобиля для минимальной пошлины.

Цель: Определить при каком возрасте автомобиля пошлина минимальна,
и найти критерии "проходной" машины.
"""

import yaml
from decimal import Decimal
from typing import Dict, List, Tuple
from datetime import datetime

# Текущий год
CURRENT_YEAR = 2025

# Курс EUR/RUB для расчётов
EUR_TO_RUB = 100.0

def load_duties():
    """Загрузка таблицы пошлин из YAML"""
    with open('/Users/admin/PycharmProjects/car_calculator/config/duties.yml', 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return data['age_categories']

def calculate_age_category(year: int) -> str:
    """Определить категорию возраста автомобиля"""
    age = CURRENT_YEAR - year
    if age <= 3:
        return 'lt3'
    elif 3 < age <= 5:
        return '3_5'
    else:
        return 'gt5'

def calculate_duty_lt3(customs_value_eur: float, engine_cc: int, duties: dict) -> float:
    """
    Расчёт пошлины для авто <= 3 лет.
    Формула: MAX(customs_value × percent, engine_cc × min_rate_eur_per_cc)
    """
    brackets = duties['lt3']['value_brackets']

    # Найти подходящий брэкет
    bracket = None
    for b in brackets:
        max_val = b.get('max_customs_value_eur')
        if max_val is None or customs_value_eur <= max_val:
            bracket = b
            break

    if not bracket:
        bracket = brackets[-1]  # Последний брэкет для больших стоимостей

    # Расчёт по двум формулам
    duty_by_percent = customs_value_eur * bracket['percent']
    duty_by_cc = engine_cc * bracket['min_rate_eur_per_cc']

    # Берём максимум
    duty_eur = max(duty_by_percent, duty_by_cc)

    return duty_eur

def calculate_duty_3_5_or_gt5(engine_cc: int, age_category: str, duties: dict) -> float:
    """
    Расчёт пошлины для авто 3-5 лет или > 5 лет.
    Формула: engine_cc × rate_eur_per_cc
    """
    bands = duties[age_category]['bands']

    # Найти подходящий диапазон
    rate = None
    for band in bands:
        max_cc = band.get('max_cc')
        if max_cc is None or engine_cc <= max_cc:
            rate = band['rate_eur_per_cc']
            break

    if rate is None:
        rate = bands[-1]['rate_eur_per_cc']

    duty_eur = engine_cc * rate
    return duty_eur

def analyze_optimal_age():
    """Главный анализ оптимального возраста"""

    duties = load_duties()

    print("=" * 90)
    print("ИССЛЕДОВАНИЕ ОПТИМАЛЬНОГО ВОЗРАСТА АВТОМОБИЛЯ ДЛЯ МИНИМАЛЬНОЙ ПОШЛИНЫ")
    print("=" * 90)
    print()
    print(f"Текущий год: {CURRENT_YEAR}")
    print(f"Курс EUR/RUB: {EUR_TO_RUB:.0f}")
    print()

    # Тестовые сценарии: различные комбинации цены и объёма
    test_scenarios = [
        # (описание, закупочная цена EUR, объём см³)
        ("Бюджетный хэтчбек", 5000, 1500),
        ("Средний седан", 10000, 2000),
        ("Премиум кроссовер", 25000, 2500),
        ("Люкс седан", 40000, 3000),
        ("Спорткар", 60000, 3500),
    ]

    # Годы выпуска для анализа
    years_to_test = [
        2025,  # 0 лет (новый)
        2024,  # 1 год
        2023,  # 2 года
        2022,  # 3 года (граница lt3/3_5)
        2021,  # 4 года
        2020,  # 5 лет (граница 3_5/gt5)
        2019,  # 6 лет
        2018,  # 7 лет
        2015,  # 10 лет
        2010,  # 15 лет
    ]

    results = []

    for scenario_name, purchase_price_eur, engine_cc in test_scenarios:
        print("=" * 90)
        print(f"СЦЕНАРИЙ: {scenario_name}")
        print(f"Закупочная цена: {purchase_price_eur:,} EUR ({purchase_price_eur * EUR_TO_RUB:,.0f} ₽)".replace(',', ' '))
        print(f"Объём двигателя: {engine_cc:,} см³".replace(',', ' '))
        print("=" * 90)
        print()

        print(f"{'Год':<8} {'Возраст':<10} {'Категория':<12} {'Пошлина EUR':<15} {'Пошлина RUB':<20} {'% от цены':<12}")
        print("-" * 90)

        scenario_results = []

        for year in years_to_test:
            age = CURRENT_YEAR - year
            age_category = calculate_age_category(year)

            # Расчёт пошлины в зависимости от категории
            if age_category == 'lt3':
                duty_eur = calculate_duty_lt3(purchase_price_eur, engine_cc, duties)
            else:
                duty_eur = calculate_duty_3_5_or_gt5(engine_cc, age_category, duties)

            duty_rub = duty_eur * EUR_TO_RUB
            duty_percent = (duty_eur / purchase_price_eur) * 100

            # Форматирование для вывода
            age_label = f"{age} {'год' if age == 1 else 'года' if age < 5 else 'лет'}"

            print(f"{year:<8} {age_label:<10} {age_category:<12} {duty_eur:>13,.0f} {duty_rub:>18,.0f} ₽ {duty_percent:>10.1f}%".replace(',', ' '))

            scenario_results.append({
                'scenario': scenario_name,
                'year': year,
                'age': age,
                'age_category': age_category,
                'purchase_price_eur': purchase_price_eur,
                'engine_cc': engine_cc,
                'duty_eur': duty_eur,
                'duty_rub': duty_rub,
                'duty_percent': duty_percent
            })

        results.extend(scenario_results)

        # Найти минимальную пошлину для этого сценария
        min_duty = min(scenario_results, key=lambda x: x['duty_eur'])
        max_duty = max(scenario_results, key=lambda x: x['duty_eur'])

        print()
        print(f"📊 АНАЛИЗ ДЛЯ {scenario_name.upper()}:")
        print(f"   Минимальная пошлина: {min_duty['duty_rub']:,.0f} ₽ ({min_duty['duty_percent']:.1f}%) при возрасте {min_duty['age']} лет (год {min_duty['year']})".replace(',', ' '))
        print(f"   Максимальная пошлина: {max_duty['duty_rub']:,.0f} ₽ ({max_duty['duty_percent']:.1f}%) при возрасте {max_duty['age']} лет (год {max_duty['year']})".replace(',', ' '))
        print(f"   Разница: {(max_duty['duty_rub'] - min_duty['duty_rub']):,.0f} ₽ ({((max_duty['duty_percent'] - min_duty['duty_percent'])):.1f} п.п.)".replace(',', ' '))
        print()

    # СВОДНЫЙ АНАЛИЗ
    print("\n" + "=" * 90)
    print("СВОДНЫЙ АНАЛИЗ: ОПТИМАЛЬНЫЙ ВОЗРАСТ ПО КАТЕГОРИЯМ")
    print("=" * 90)
    print()

    # Группировка по категориям возраста
    for age_cat in ['lt3', '3_5', 'gt5']:
        cat_results = [r for r in results if r['age_category'] == age_cat]
        if not cat_results:
            continue

        avg_duty_percent = sum(r['duty_percent'] for r in cat_results) / len(cat_results)
        min_duty = min(cat_results, key=lambda x: x['duty_percent'])
        max_duty = max(cat_results, key=lambda x: x['duty_percent'])

        age_label = {
            'lt3': '≤ 3 лет (новые и свежие)',
            '3_5': '3-5 лет (средний возраст)',
            'gt5': '> 5 лет (старые)'
        }[age_cat]

        print(f"📌 {age_label}:")
        print(f"   Средняя доля пошлины: {avg_duty_percent:.1f}% от цены")
        print(f"   Диапазон: {min_duty['duty_percent']:.1f}% - {max_duty['duty_percent']:.1f}%")
        print()

    # КРИТЕРИИ "ПРОХОДНОЙ" МАШИНЫ
    print("=" * 90)
    print('КРИТЕРИИ "ПРОХОДНОЙ" МАШИНЫ (минимальная пошлина)')
    print("=" * 90)
    print()

    # Анализ по объёму двигателя
    print("1️⃣ ПО ОБЪЁМУ ДВИГАТЕЛЯ:")
    print()

    for engine_label, engine_cc in [("≤ 1000 см³ (малолитражка)", 1000),
                                      ("1001-1500 см³ (компакт)", 1500),
                                      ("1501-1800 см³ (средний)", 1800),
                                      ("1801-2300 см³ (крупный)", 2300),
                                      ("2301-3000 см³ (премиум)", 3000),
                                      ("> 3000 см³ (большой)", 3500)]:

        print(f"   {engine_label}:")

        # Расчёт пошлины для типичной цены (15,000 EUR)
        typical_price = 15000

        for age_cat in ['lt3', '3_5', 'gt5']:
            if age_cat == 'lt3':
                duty = calculate_duty_lt3(typical_price, engine_cc, duties)
            else:
                duty = calculate_duty_3_5_or_gt5(engine_cc, age_cat, duties)

            duty_percent = (duty / typical_price) * 100

            age_label_short = {
                'lt3': '≤3 лет',
                '3_5': '3-5 лет',
                'gt5': '>5 лет'
            }[age_cat]

            status = "✅" if duty_percent < 30 else "⚠️" if duty_percent < 50 else "🔴"

            print(f"      {age_label_short:8} → {duty:>8,.0f} EUR ({duty_percent:>5.1f}%) {status}".replace(',', ' '))

        print()

    # РЕКОМЕНДАЦИИ
    print("=" * 90)
    print("РЕКОМЕНДАЦИИ ПО ОПТИМАЛЬНОМУ ВОЗРАСТУ")
    print("=" * 90)
    print()

    print("✅ МИНИМАЛЬНАЯ ПОШЛИНА:")
    print("   • Возраст: 3-5 лет (категория 3_5)")
    print("   • Объём: ≤ 1500 см³")
    print("   • Формула: фиксированная ставка EUR/см³ (не зависит от стоимости)")
    print()

    print("⚠️  СРЕДНЯЯ ПОШЛИНА:")
    print("   • Возраст: ≤ 3 лет (категория lt3) - для недорогих авто")
    print("   • Объём: 1500-2300 см³")
    print("   • Особенность: пошлина зависит от стоимости (процент или EUR/см³)")
    print()

    print("🔴 ВЫСОКАЯ ПОШЛИНА:")
    print("   • Возраст: > 5 лет (категория gt5)")
    print("   • Объём: > 2300 см³")
    print("   • Причина: высокие ставки EUR/см³")
    print()

    # ПАРАДОКС ВОЗРАСТА
    print("=" * 90)
    print("⚡ ПАРАДОКС ВОЗРАСТА АВТОМОБИЛЯ")
    print("=" * 90)
    print()
    print("ВАЖНОЕ ОТКРЫТИЕ:")
    print()
    print("Для ДОРОГИХ автомобилей (> 25,000 EUR):")
    print("   • ≤ 3 лет: ВЫСОКАЯ пошлина (54% или MIN по EUR/см³)")
    print("   • 3-5 лет: НИЗКАЯ пошлина (фиксированная ставка 1.5-3.6 EUR/см³)")
    print("   • > 5 лет: СРЕДНЯЯ пошлина (ставка 3.0-5.7 EUR/см³)")
    print()
    print("ВЫВОД: Для дорогих машин выгоднее брать авто возраста 3-5 лет!")
    print()
    print("Для ДЕШЁВЫХ автомобилей (< 10,000 EUR):")
    print("   • ≤ 3 лет: НИЗКАЯ пошлина (54% от маленькой суммы)")
    print("   • 3-5 лет: НИЗКАЯ пошлина (фиксированная ставка)")
    print("   • > 5 лет: ВЫСОКАЯ пошлина (ставка выше, чем 3-5 лет)")
    print()
    print("ВЫВОД: Для дешёвых машин возраст менее критичен (≤ 5 лет OK)")
    print()

    print("=" * 90)

if __name__ == "__main__":
    analyze_optimal_age()

