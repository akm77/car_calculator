"""Юнит-тесты для CostBreakdown и CalculationResult."""

from __future__ import annotations

from decimal import Decimal

from pydantic import ValidationError
import pytest

from app.calculation.models import (
    CalculationMeta,
    CalculationRequest,
    CalculationResult,
    CostBreakdown,
)


class TestCostBreakdown:
    """Тесты для модели CostBreakdown."""

    def test_cost_breakdown_valid(self):
        """Создание валидной детализации стоимости."""
        breakdown = CostBreakdown(
            purchase_price_rub=1000000,
            duties_rub=150000,
            utilization_fee_rub=50000,
            customs_services_rub=25000,
            era_glonass_rub=45000,
            freight_rub=80000,
            country_expenses_rub=30000,
            company_commission_rub=40000,
            total_rub=1420000,
        )
        assert breakdown.purchase_price_rub == 1000000
        assert breakdown.duties_rub == 150000
        assert breakdown.utilization_fee_rub == 50000
        assert breakdown.customs_services_rub == 25000
        assert breakdown.era_glonass_rub == 45000
        assert breakdown.freight_rub == 80000
        assert breakdown.country_expenses_rub == 30000
        assert breakdown.company_commission_rub == 40000
        assert breakdown.total_rub == 1420000

    def test_cost_breakdown_zero_components(self):
        """Детализация с нулевыми компонентами."""
        breakdown = CostBreakdown(
            purchase_price_rub=500000,
            duties_rub=0,
            utilization_fee_rub=0,
            customs_services_rub=0,
            era_glonass_rub=0,
            freight_rub=0,
            country_expenses_rub=0,
            company_commission_rub=0,
            total_rub=500000,
        )
        assert breakdown.duties_rub == 0
        assert breakdown.utilization_fee_rub == 0
        assert breakdown.total_rub == 500000

    def test_cost_breakdown_integrity_valid(self):
        """Проверка инварианта целостности: total = сумма всех компонентов."""
        purchase_price = 1000000
        duties = 150000
        utilization = 50000
        customs = 25000
        era = 45000
        freight = 80000
        country = 30000
        commission = 40000
        total = (
            purchase_price + duties + utilization + customs + era + freight + country + commission
        )

        breakdown = CostBreakdown(
            purchase_price_rub=purchase_price,
            duties_rub=duties,
            utilization_fee_rub=utilization,
            customs_services_rub=customs,
            era_glonass_rub=era,
            freight_rub=freight,
            country_expenses_rub=country,
            company_commission_rub=commission,
            total_rub=total,
        )
        # Проверяем, что total соответствует сумме компонентов
        calculated_total = (
            breakdown.purchase_price_rub
            + breakdown.duties_rub
            + breakdown.utilization_fee_rub
            + breakdown.customs_services_rub
            + breakdown.era_glonass_rub
            + breakdown.freight_rub
            + breakdown.country_expenses_rub
            + breakdown.company_commission_rub
        )
        assert breakdown.total_rub == calculated_total

    @pytest.mark.parametrize(
        "purchase,duties,util,customs,era,freight,country,commission",
        [
            (1000000, 100000, 50000, 20000, 45000, 70000, 25000, 30000),
            (500000, 50000, 25000, 10000, 45000, 40000, 15000, 20000),
            (2000000, 200000, 100000, 40000, 45000, 120000, 50000, 60000),
            (750000, 75000, 37500, 15000, 45000, 60000, 20000, 25000),
        ],
    )
    def test_cost_breakdown_integrity_parametrized(
        self, purchase, duties, util, customs, era, freight, country, commission
    ):
        """Параметризованная проверка инварианта целостности."""
        total = purchase + duties + util + customs + era + freight + country + commission
        breakdown = CostBreakdown(
            purchase_price_rub=purchase,
            duties_rub=duties,
            utilization_fee_rub=util,
            customs_services_rub=customs,
            era_glonass_rub=era,
            freight_rub=freight,
            country_expenses_rub=country,
            company_commission_rub=commission,
            total_rub=total,
        )
        calculated_total = (
            breakdown.purchase_price_rub
            + breakdown.duties_rub
            + breakdown.utilization_fee_rub
            + breakdown.customs_services_rub
            + breakdown.era_glonass_rub
            + breakdown.freight_rub
            + breakdown.country_expenses_rub
            + breakdown.company_commission_rub
        )
        assert breakdown.total_rub == calculated_total

    def test_cost_breakdown_large_values(self):
        """Тест с очень большими значениями."""
        breakdown = CostBreakdown(
            purchase_price_rub=100000000,  # 100 млн
            duties_rub=15000000,  # 15 млн
            utilization_fee_rub=5000000,  # 5 млн
            customs_services_rub=250000,  # 250 тыс
            era_glonass_rub=45000,
            freight_rub=8000000,  # 8 млн
            country_expenses_rub=3000000,  # 3 млн
            company_commission_rub=4000000,  # 4 млн
            total_rub=135295000,  # 135.295 млн
        )
        assert breakdown.purchase_price_rub == 100000000
        assert breakdown.total_rub == 135295000

    def test_cost_breakdown_missing_field(self):
        """Отсутствие обязательного поля — ошибка."""
        with pytest.raises(ValidationError) as exc_info:
            CostBreakdown(
                purchase_price_rub=1000000,
                duties_rub=150000,
                utilization_fee_rub=50000,
                customs_services_rub=25000,
                era_glonass_rub=45000,
                freight_rub=80000,
                country_expenses_rub=30000,
                # company_commission_rub отсутствует
                total_rub=1420000,
            )  # type: ignore
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("company_commission_rub",) for e in errors)

    def test_cost_breakdown_era_glonass_standard(self):
        """ЭРА-ГЛОНАСС обычно составляет 45000 руб."""
        breakdown = CostBreakdown(
            purchase_price_rub=1000000,
            duties_rub=100000,
            utilization_fee_rub=50000,
            customs_services_rub=20000,
            era_glonass_rub=45000,
            freight_rub=70000,
            country_expenses_rub=25000,
            company_commission_rub=30000,
            total_rub=1340000,
        )
        assert breakdown.era_glonass_rub == 45000


class TestCalculationResult:
    """Тесты для модели CalculationResult."""

    def test_calculation_result_valid(self):
        """Создание валидного результата расчёта."""
        request = CalculationRequest(
            country="japan",
            year=2020,
            engine_cc=2000,
            engine_power_hp=150,
            purchase_price=Decimal("1000000"),
            currency="JPY",
        )
        meta = CalculationMeta(
            age_years=5,
            age_category="gt5",
            volume_band="2000-2500",
            passing_category="standard",
        )
        breakdown = CostBreakdown(
            purchase_price_rub=1000000,
            duties_rub=150000,
            utilization_fee_rub=50000,
            customs_services_rub=25000,
            era_glonass_rub=45000,
            freight_rub=80000,
            country_expenses_rub=30000,
            company_commission_rub=40000,
            total_rub=1420000,
        )
        result = CalculationResult(request=request, meta=meta, breakdown=breakdown)
        assert result.request == request
        assert result.meta == meta
        assert result.breakdown == breakdown

    def test_calculation_result_request_data_preserved(self):
        """Данные запроса сохраняются в результате."""
        request = CalculationRequest(
            country="korea",
            year=2019,
            engine_cc=3000,
            engine_power_hp=250,
            purchase_price=Decimal("50000"),
            currency="USD",
            vehicle_type="pickup",
        )
        meta = CalculationMeta(
            age_years=6,
            age_category="gt5",
            volume_band="3000-3500",
            passing_category="standard",
        )
        breakdown = CostBreakdown(
            purchase_price_rub=4500000,
            duties_rub=900000,
            utilization_fee_rub=200000,
            customs_services_rub=75000,
            era_glonass_rub=45000,
            freight_rub=300000,
            country_expenses_rub=100000,
            company_commission_rub=150000,
            total_rub=6270000,
        )
        result = CalculationResult(request=request, meta=meta, breakdown=breakdown)
        assert result.request.country == "korea"
        assert result.request.year == 2019
        assert result.request.engine_cc == 3000
        assert result.request.engine_power_hp == 250
        assert result.request.vehicle_type == "pickup"

    def test_calculation_result_meta_data_preserved(self):
        """Метаданные сохраняются в результате."""
        request = CalculationRequest(
            country="japan",
            year=2020,
            engine_cc=2000,
            engine_power_hp=150,
            purchase_price=Decimal("1000000"),
            currency="JPY",
        )
        meta = CalculationMeta(
            age_years=5,
            age_category="gt5",
            volume_band="2000-2500",
            passing_category="standard",
            engine_power_hp=150,
            engine_power_kw=110.325,
            utilization_coefficient=0.17,
        )
        breakdown = CostBreakdown(
            purchase_price_rub=1000000,
            duties_rub=150000,
            utilization_fee_rub=50000,
            customs_services_rub=25000,
            era_glonass_rub=45000,
            freight_rub=80000,
            country_expenses_rub=30000,
            company_commission_rub=40000,
            total_rub=1420000,
        )
        result = CalculationResult(request=request, meta=meta, breakdown=breakdown)
        assert result.meta.age_years == 5
        assert result.meta.age_category == "gt5"
        assert result.meta.engine_power_hp == 150
        assert result.meta.engine_power_kw == 110.325
        assert result.meta.utilization_coefficient == 0.17

    def test_calculation_result_breakdown_data_preserved(self):
        """Детализация стоимости сохраняется в результате."""
        request = CalculationRequest(
            country="japan",
            year=2020,
            engine_cc=2000,
            engine_power_hp=150,
            purchase_price=Decimal("1000000"),
            currency="JPY",
        )
        meta = CalculationMeta(
            age_years=5,
            age_category="gt5",
            volume_band="2000-2500",
            passing_category="standard",
        )
        breakdown = CostBreakdown(
            purchase_price_rub=1000000,
            duties_rub=150000,
            utilization_fee_rub=50000,
            customs_services_rub=25000,
            era_glonass_rub=45000,
            freight_rub=80000,
            country_expenses_rub=30000,
            company_commission_rub=40000,
            total_rub=1420000,
        )
        result = CalculationResult(request=request, meta=meta, breakdown=breakdown)
        assert result.breakdown.purchase_price_rub == 1000000
        assert result.breakdown.duties_rub == 150000
        assert result.breakdown.utilization_fee_rub == 50000
        assert result.breakdown.total_rub == 1420000

    def test_calculation_result_missing_request(self):
        """Отсутствие request — ошибка."""
        meta = CalculationMeta(
            age_years=5,
            age_category="gt5",
            volume_band="2000-2500",
            passing_category="standard",
        )
        breakdown = CostBreakdown(
            purchase_price_rub=1000000,
            duties_rub=150000,
            utilization_fee_rub=50000,
            customs_services_rub=25000,
            era_glonass_rub=45000,
            freight_rub=80000,
            country_expenses_rub=30000,
            company_commission_rub=40000,
            total_rub=1420000,
        )
        with pytest.raises(ValidationError) as exc_info:
            CalculationResult(meta=meta, breakdown=breakdown)  # type: ignore
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("request",) for e in errors)

    def test_calculation_result_missing_meta(self):
        """Отсутствие meta — ошибка."""
        request = CalculationRequest(
            country="japan",
            year=2020,
            engine_cc=2000,
            engine_power_hp=150,
            purchase_price=Decimal("1000000"),
            currency="JPY",
        )
        breakdown = CostBreakdown(
            purchase_price_rub=1000000,
            duties_rub=150000,
            utilization_fee_rub=50000,
            customs_services_rub=25000,
            era_glonass_rub=45000,
            freight_rub=80000,
            country_expenses_rub=30000,
            company_commission_rub=40000,
            total_rub=1420000,
        )
        with pytest.raises(ValidationError) as exc_info:
            CalculationResult(request=request, breakdown=breakdown)  # type: ignore
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("meta",) for e in errors)

    def test_calculation_result_missing_breakdown(self):
        """Отсутствие breakdown — ошибка."""
        request = CalculationRequest(
            country="japan",
            year=2020,
            engine_cc=2000,
            engine_power_hp=150,
            purchase_price=Decimal("1000000"),
            currency="JPY",
        )
        meta = CalculationMeta(
            age_years=5,
            age_category="gt5",
            volume_band="2000-2500",
            passing_category="standard",
        )
        with pytest.raises(ValidationError) as exc_info:
            CalculationResult(request=request, meta=meta)  # type: ignore
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("breakdown",) for e in errors)
