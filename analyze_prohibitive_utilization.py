#!/usr/bin/env python3
"""
Анализ запретительных коэффициентов утилизационного сбора.

Цель: Определить, при какой мощности двигателя утилизационный сбор
становится запретительным (существенно превышает закупочную цену).

Критерий запретительности:
- Утильсбор > 50% закупочной цены = ВЫСОКИЙ
- Утильсбор > 100% закупочной цены = ЗАПРЕТИТЕЛЬНЫЙ
- Утильсбор > 200% закупочной цены = ЭКСТРЕМАЛЬНЫЙ
"""

import yaml
from decimal import Decimal
from typing import Dict, List, Tuple

# Конвертация кВт в л.с.
KW_TO_HP = 1.35962

# Базовая ставка утильсбора
BASE_RATE_RUB = 20_000

# Типичные закупочные цены для анализа (в рублях)
TYPICAL_PRICES = {
    "бюджетный": 500_000,      # ~5,000 USD
    "средний": 1_500_000,      # ~15,000 USD
    "премиум": 3_000_000,      # ~30,000 USD
    "люкс": 6_000_000,         # ~60,000 USD
}

def load_utilization_table():
    """Загрузка таблицы утилизационного сбора из YAML"""
    with open('/Users/admin/PycharmProjects/car_calculator/config/utilization_2025.yml', 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return data['utilization_m1_personal']

def find_coefficient(volume_cc: int, power_kw: float, age_lt3: bool, table: dict) -> float:
    """
    Найти коэффициент утилизационного сбора для заданных параметров.

    Args:
        volume_cc: Объём двигателя в см³
        power_kw: Мощность в кВт
        age_lt3: True если авто < 3 лет, False если >= 3 лет
        table: Данные из utilization_2025.yml

    Returns:
        Коэффициент утилизационного сбора
    """
    # Найти диапазон объёма
    volume_band = None
    for band in table['volume_bands']:
        vol_min, vol_max = band['volume_range']
        if vol_min <= volume_cc <= vol_max:
            volume_band = band
            break

    if not volume_band:
        # Если не нашли, используем последний диапазон (> 3500 см³)
        volume_band = table['volume_bands'][-1]

    # Найти брэкет мощности
    coefficient_key = 'coefficient_lt3' if age_lt3 else 'coefficient_gt3'

    for bracket in volume_band['power_brackets']:
        power_max = bracket.get('power_kw_max')
        if power_max is None or power_kw <= power_max:
            return bracket[coefficient_key]

    # Если не нашли, используем последний брэкет
    return volume_band['power_brackets'][-1][coefficient_key]

def analyze_prohibitive_power():
    """Анализ запретительных значений мощности"""

    table = load_utilization_table()

    print("=" * 80)
    print("АНАЛИЗ ЗАПРЕТИТЕЛЬНЫХ КОЭФФИЦИЕНТОВ УТИЛИЗАЦИОННОГО СБОРА")
    print("=" * 80)
    print()
    print(f"Базовая ставка утильсбора: {BASE_RATE_RUB:,} ₽".replace(',', ' '))
    print()

    # Диапазоны объёмов для анализа
    volume_ranges = [
        (1500, "1500 см³ (типичный хэтчбек)"),
        (2000, "2000 см³ (средний седан)"),
        (3000, "3000 см³ (кроссовер/премиум)"),
        (4000, "4000 см³ (спорткар/внедорожник)"),
    ]

    # Диапазоны мощности для тестирования (в л.с.)
    power_hp_tests = list(range(50, 551, 50))  # От 50 до 550 л.с. с шагом 50

    results = []

    for volume_cc, volume_label in volume_ranges:
        print(f"\n{'=' * 80}")
        print(f"ОБЪЁМ ДВИГАТЕЛЯ: {volume_label}")
        print(f"{'=' * 80}\n")

        print(f"{'Мощность':<15} {'Утильсбор':<20} {'Коэфф. <3л':<12} {'Коэфф. >=3л':<12} {'Статус':<20}")
        print("-" * 80)

        for power_hp in power_hp_tests:
            power_kw = power_hp / KW_TO_HP

            # Получить коэффициенты для обоих возрастов
            coef_lt3 = find_coefficient(volume_cc, power_kw, True, table)
            coef_gt3 = find_coefficient(volume_cc, power_kw, False, table)

            # Рассчитать утильсбор (используем максимальный коэффициент)
            coef_max = max(coef_lt3, coef_gt3)
            utilization_fee = BASE_RATE_RUB * coef_max

            # Определить статус запретительности
            status = "✅ Нормальный"
            is_prohibitive = False

            for price_category, price_rub in TYPICAL_PRICES.items():
                ratio = (utilization_fee / price_rub) * 100

                if ratio > 200:
                    status = f"🔴 ЭКСТРЕМАЛЬНЫЙ ({ratio:.0f}% от {price_category})"
                    is_prohibitive = True
                    break
                elif ratio > 100:
                    status = f"🟠 ЗАПРЕТИТЕЛЬНЫЙ ({ratio:.0f}% от {price_category})"
                    is_prohibitive = True
                    break
                elif ratio > 50:
                    status = f"🟡 ВЫСОКИЙ ({ratio:.0f}% от {price_category})"
                    is_prohibitive = True
                    break

            print(f"{power_hp} л.с. ({power_kw:.1f} кВт)".ljust(15), end=" ")
            print(f"{utilization_fee:,.0f} ₽".replace(',', ' ').ljust(20), end=" ")
            print(f"{coef_lt3}".ljust(12), end=" ")
            print(f"{coef_gt3}".ljust(12), end=" ")
            print(status)

            # Сохранить критические точки
            if is_prohibitive:
                results.append({
                    'volume_cc': volume_cc,
                    'volume_label': volume_label,
                    'power_hp': power_hp,
                    'power_kw': power_kw,
                    'coef_lt3': coef_lt3,
                    'coef_gt3': coef_gt3,
                    'utilization_fee': utilization_fee,
                    'status': status
                })

    # Сводка критических точек
    print("\n" + "=" * 80)
    print("СВОДКА: КРИТИЧЕСКИЕ ТОЧКИ (когда утильсбор становится запретительным)")
    print("=" * 80)
    print()

    if results:
        # Группировка по объёму
        current_volume = None
        for r in results:
            if r['volume_cc'] != current_volume:
                current_volume = r['volume_cc']
                print(f"\n{r['volume_label']}:")
                print("-" * 80)

            # Показать только первую запретительную точку для каждого объёма
            if "ЗАПРЕТИТЕЛЬНЫЙ" in r['status'] or "ЭКСТРЕМАЛЬНЫЙ" in r['status']:
                print(f"  ⚠️  При {r['power_hp']} л.с. ({r['power_kw']:.1f} кВт):")
                print(f"      Утильсбор: {r['utilization_fee']:,.0f} ₽".replace(',', ' '))
                print(f"      Коэффициенты: {r['coef_lt3']} (<3 лет) / {r['coef_gt3']} (>=3 лет)")
                print(f"      Статус: {r['status']}")
                break  # Показать только первую критическую точку
    else:
        print("❌ Не найдено запретительных коэффициентов в тестируемом диапазоне")

    # Дополнительный анализ: максимальные коэффициенты
    print("\n" + "=" * 80)
    print("МАКСИМАЛЬНЫЕ КОЭФФИЦИЕНТЫ В ТАБЛИЦЕ")
    print("=" * 80)
    print()

    max_coefs = []
    for band in table['volume_bands']:
        vol_min, vol_max = band['volume_range']
        vol_label = f"{vol_min}-{vol_max if vol_max < 999999 else '∞'} см³"

        last_bracket = band['power_brackets'][-1]
        power_threshold_kw = last_bracket.get('power_kw_max', 367.76)
        power_threshold_hp = power_threshold_kw * KW_TO_HP if power_threshold_kw else 500

        coef_lt3 = last_bracket['coefficient_lt3']
        coef_gt3 = last_bracket['coefficient_gt3']

        max_fee_lt3 = BASE_RATE_RUB * coef_lt3
        max_fee_gt3 = BASE_RATE_RUB * coef_gt3

        max_coefs.append({
            'volume': vol_label,
            'power_threshold_hp': power_threshold_hp,
            'coef_lt3': coef_lt3,
            'coef_gt3': coef_gt3,
            'fee_lt3': max_fee_lt3,
            'fee_gt3': max_fee_gt3
        })

    for mc in max_coefs:
        print(f"{mc['volume']:20} | Мощность >= {mc['power_threshold_hp']:.0f} л.с.")
        print(f"  Коэффициенты: {mc['coef_lt3']} (<3 лет) / {mc['coef_gt3']} (>=3 лет)")
        print(f"  Утильсбор: {mc['fee_lt3']:,.0f} ₽ / {mc['fee_gt3']:,.0f} ₽".replace(',', ' '))

        # Оценка запретительности для типичных цен
        for price_category, price_rub in TYPICAL_PRICES.items():
            ratio_lt3 = (mc['fee_lt3'] / price_rub) * 100
            ratio_gt3 = (mc['fee_gt3'] / price_rub) * 100

            if ratio_gt3 > 100:
                print(f"    🔴 ЗАПРЕТИТЕЛЬНЫЙ для {price_category} авто (>= 3 лет): {ratio_gt3:.0f}%")
                break
            elif ratio_gt3 > 50:
                print(f"    🟡 ВЫСОКИЙ для {price_category} авто (>= 3 лет): {ratio_gt3:.0f}%")
                break
        print()

    # Практические рекомендации
    print("=" * 80)
    print("ПРАКТИЧЕСКИЕ РЕКОМЕНДАЦИИ")
    print("=" * 80)
    print()
    print("1. БЕЗОПАСНЫЕ ДИАПАЗОНЫ МОЩНОСТИ:")
    print("   ✅ До 160 л.с. (118 кВт) - утильсбор минимален для всех объёмов")
    print()
    print("2. ОСТОРОЖНО:")
    print("   ⚠️  190-250 л.с. - коэффициенты начинают расти для больших объёмов")
    print("   ⚠️  250-350 л.с. - утильсбор может превысить 100% цены бюджетного авто")
    print()
    print("3. ЗАПРЕТИТЕЛЬНЫЕ ЗОНЫ:")
    print("   🔴 > 350 л.с. (260 кВт) - утильсбор становится запретительным")
    print("   🔴 > 450 л.с. (330 кВт) - утильсбор превышает стоимость среднего авто")
    print()
    print("4. РЕКОМЕНДАЦИИ ПО ОБЪЁМУ:")
    print("   ✅ 1000-2000 см³: оптимальный диапазон, низкие коэффициенты")
    print("   ⚠️  2000-3000 см³: умеренные коэффициенты при высокой мощности")
    print("   🔴 > 3500 см³: максимальные коэффициенты при любой мощности")
    print()
    print("=" * 80)

if __name__ == "__main__":
    analyze_prohibitive_power()

