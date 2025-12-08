#!/usr/bin/env python3
"""
Sprint 4 Manual Test: Verify duties lt3 brackets (2025 spec)

Tests the updated duty calculation logic with new brackets:
- 325k, 650k, 1625k, 3250k, 6500k RUB (converted to EUR)

Expected behavior:
- Duty = max(percent × customs_value, min_rate × engine_cc)
- Brackets in EUR, but represent RUB thresholds
"""

from decimal import Decimal
from app.calculation.engine import calculate
from app.calculation.models import CalculationRequest


def test_duty_bracket_1():
    """Test bracket 1: customs_value ≤ 3250 EUR (325k RUB)

    Expected: 54% of customs_value, but not less than 2.5 EUR/cc
    """
    print("\n" + "="*60)
    print("TEST 1: Lt3, Bracket 1 (≤ 325k RUB / 3250 EUR)")
    print("="*60)

    req = CalculationRequest(
        country="japan",
        year=2024,  # lt3 (2025 - 2024 = 1 year)
        engine_cc=1500,
        engine_power_hp=110,
        purchase_price=Decimal("3333"),  # ~300k RUB at 90 USD/RUB
        currency="USD"
    )

    result = calculate(req)

    print(f"Input: 3,333 USD (~300k RUB), 1500cc, 110 л.с., год 2024")
    print(f"Customs value EUR: {result.meta.customs_value_eur}")
    print(f"Duty RUB: {result.breakdown.duties_rub:,.0f}")
    print(f"Duty mode: {result.meta.duty_formula_mode}")
    print(f"Duty percent: {result.meta.duty_percent}")
    print(f"Duty min rate EUR/cc: {result.meta.duty_min_rate_eur_per_cc}")

    # Verification
    # At actual EUR rate ~88.7: 3333 USD × 76 ≈ 253k RUB ≈ 2859 EUR
    # Percent: 2859 × 0.54 ≈ 1544 EUR
    # Min: 1500 × 2.5 = 3750 EUR ≈ 333k RUB (at 88.7 rate)
    # Expected: max(1544, 3750) = 3750 EUR ≈ 333k RUB
    print(f"\n✅ Expected: ~333,000 RUB (min rate, actual EUR rate)")
    assert result.breakdown.duties_rub > Decimal("300000"), "Duty should be > 300k RUB"
    assert result.meta.duty_formula_mode == "min", "Should use min rate"


def test_duty_bracket_2():
    """Test bracket 2: 3251-6500 EUR (325k-650k RUB)

    Expected: 48% of customs_value, but not less than 3.5 EUR/cc
    """
    print("\n" + "="*60)
    print("TEST 2: Lt3, Bracket 2 (325k-650k RUB / 3250-6500 EUR)")
    print("="*60)

    req = CalculationRequest(
        country="korea",
        year=2023,  # lt3 (2025 - 2023 = 2 years)
        engine_cc=2000,
        engine_power_hp=150,
        purchase_price=Decimal("5556"),  # ~500k RUB at 90 USD/RUB
        currency="USD"
    )

    result = calculate(req)

    print(f"Input: 5,556 USD (~500k RUB), 2000cc, 150 л.с., год 2023")
    print(f"Customs value EUR: {result.meta.customs_value_eur}")
    print(f"Duty RUB: {result.breakdown.duties_rub:,.0f}")
    print(f"Duty mode: {result.meta.duty_formula_mode}")
    print(f"Duty percent: {result.meta.duty_percent}")
    print(f"Duty min rate EUR/cc: {result.meta.duty_min_rate_eur_per_cc}")

    # Verification
    # At actual EUR rate ~88.7: 5556 USD × 76 ≈ 422k RUB ≈ 4766 EUR
    # Percent: 4766 × 0.48 ≈ 2288 EUR
    # Min: 2000 × 3.5 = 7000 EUR ≈ 621k RUB (at 88.7 rate)
    # Expected: max(2288, 7000) = 7000 EUR ≈ 621k RUB
    print(f"\n✅ Expected: ~621,000 RUB (min rate, actual EUR rate)")
    assert result.breakdown.duties_rub > Decimal("600000"), "Duty should be > 600k RUB"
    assert result.meta.duty_formula_mode == "min", "Should use min rate"


def test_duty_bracket_3():
    """Test bracket 3: 6501-16250 EUR (650k-1625k RUB)

    Expected: 48% of customs_value, but not less than 5.5 EUR/cc
    """
    print("\n" + "="*60)
    print("TEST 3: Lt3, Bracket 3 (650k-1625k RUB / 6500-16250 EUR)")
    print("="*60)

    req = CalculationRequest(
        country="china",
        year=2024,
        engine_cc=1800,
        engine_power_hp=140,
        purchase_price=Decimal("11111"),  # ~1M RUB at 90 USD/RUB
        currency="USD"
    )

    result = calculate(req)

    print(f"Input: 11,111 USD (~1M RUB), 1800cc, 140 л.с., год 2024")
    print(f"Customs value EUR: {result.meta.customs_value_eur}")
    print(f"Duty RUB: {result.breakdown.duties_rub:,.0f}")
    print(f"Duty mode: {result.meta.duty_formula_mode}")

    # Verification
    # At actual EUR rate ~88.7: 1M RUB ≈ 11,277 EUR
    # Percent: 11,277 × 0.48 ≈ 5,413 EUR ≈ 480k RUB
    # Min: 1800 × 5.5 = 9,900 EUR ≈ 878k RUB (at 88.7 rate)
    # Expected: max(480k, 878k) = 878k RUB
    print(f"\n✅ Expected: ~878,000 RUB (min rate, actual EUR rate)")
    assert result.breakdown.duties_rub > Decimal("800000"), "Duty should be > 800k RUB"


def test_duty_bracket_5_high_value():
    """Test bracket 5: 32501-65000 EUR (3250k-6500k RUB)

    High value car where percent might exceed min rate.
    """
    print("\n" + "="*60)
    print("TEST 4: Lt3, Bracket 5 (3250k-6500k RUB / 32500-65000 EUR)")
    print("="*60)

    req = CalculationRequest(
        country="china",
        year=2025,
        engine_cc=2000,
        engine_power_hp=250,
        purchase_price=Decimal("55556"),  # ~5M RUB at 90 USD/RUB
        currency="USD"
    )

    result = calculate(req)

    print(f"Input: 55,556 USD (~5M RUB), 2000cc, 250 л.с., год 2025")
    print(f"Customs value EUR: {result.meta.customs_value_eur}")
    print(f"Duty RUB: {result.breakdown.duties_rub:,.0f}")
    print(f"Duty mode: {result.meta.duty_formula_mode}")

    # Verification
    # At actual EUR rate ~88.7: 55556 USD × 76 ≈ 4.2M RUB ≈ 47,664 EUR
    # Percent: 47,664 × 0.48 ≈ 22,879 EUR
    # Min: 2000 × 15 = 30,000 EUR ≈ 2.66M RUB (at 88.7 rate)
    # Expected: max(22,879, 30,000) = 30,000 EUR ≈ 2.66M RUB
    print(f"\n✅ Expected: ~2,660,000 RUB (min rate, actual EUR rate)")
    assert result.breakdown.duties_rub > Decimal("2500000"), "Duty should be > 2.5M RUB"


def test_duty_bracket_6_ultra_high():
    """Test bracket 6: > 65000 EUR (> 6500k RUB)

    Ultra-high value car.
    """
    print("\n" + "="*60)
    print("TEST 5: Lt3, Bracket 6 (> 6500k RUB / > 65000 EUR)")
    print("="*60)

    req = CalculationRequest(
        country="uae",
        year=2024,
        engine_cc=3000,
        engine_power_hp=400,
        purchase_price=Decimal("150000"),  # 150k USD ≈ 13.5M RUB
        currency="USD"
    )

    result = calculate(req)

    print(f"Input: 150,000 USD, 3000cc, 400 л.с., год 2024")
    print(f"Customs value EUR: {result.meta.customs_value_eur}")
    print(f"Duty RUB: {result.breakdown.duties_rub:,.0f}")
    print(f"Duty mode: {result.meta.duty_formula_mode}")

    # Verification
    # At 90 USD/RUB: 150k USD ≈ 13.5M RUB ≈ 135k EUR
    # Percent: 135000 × 0.48 = 64800 EUR ≈ 6.5M RUB
    # Min: 3000 × 20 = 60000 EUR = 6M RUB
    # Expected: max(6.5M, 6M) = 6.5M RUB (percent wins)
    print(f"\n✅ Expected: ~6,000,000+ RUB (percent or min)")
    assert result.breakdown.duties_rub > Decimal("5000000"), "Duty should be > 5M RUB"


def test_commission_uae_zero():
    """Test UAE commission = 0 (included in country expenses)"""
    print("\n" + "="*60)
    print("TEST 6: UAE Commission Check")
    print("="*60)

    req = CalculationRequest(
        country="uae",
        year=2024,
        engine_cc=2000,
        engine_power_hp=200,
        purchase_price=Decimal("50000"),
        currency="USD"
    )

    result = calculate(req)

    print(f"Country: UAE")
    print(f"Commission RUB: {result.breakdown.company_commission_rub}")

    print(f"\n✅ Expected: 0 RUB (UAE exception)")
    assert result.breakdown.company_commission_rub == Decimal("0"), "UAE commission must be 0"


def test_commission_other_countries():
    """Test default commission = 1000 USD for other countries"""
    print("\n" + "="*60)
    print("TEST 7: Default Commission (1000 USD)")
    print("="*60)

    for country in ["japan", "korea", "china", "georgia"]:
        req = CalculationRequest(
            country=country,
            year=2024,
            engine_cc=1500,
            engine_power_hp=100,
            purchase_price=Decimal("10000"),  # ~900k RUB at 90 USD/RUB
            currency="USD"
        )

        result = calculate(req)

        print(f"{country.upper()}: Commission = {result.breakdown.company_commission_rub:,.0f} RUB")

        # At ~90 RUB/USD: 1000 USD ≈ 90,000 RUB
        assert result.breakdown.company_commission_rub > Decimal("60000"), f"{country} commission should be ~76k RUB"
        assert result.breakdown.company_commission_rub < Decimal("100000"), f"{country} commission should be ~76k RUB"

    print(f"\n✅ Expected: ~90,000 RUB for all countries (1000 USD × ~90)")


if __name__ == "__main__":
    print("="*60)
    print("SPRINT 4: Duties & Commissions Manual Tests")
    print("="*60)

    try:
        test_duty_bracket_1()
        test_duty_bracket_2()
        test_duty_bracket_3()
        test_duty_bracket_5_high_value()
        test_duty_bracket_6_ultra_high()
        test_commission_uae_zero()
        test_commission_other_countries()

        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED")
        print("="*60)
        print("\nSummary:")
        print("✅ Lt3 brackets updated to 2025 spec (325k-6500k RUB)")
        print("✅ Duty calculation logic works correctly")
        print("✅ Commission system validated (1000 USD + UAE=0)")
        print("✅ Config loads without errors")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()

