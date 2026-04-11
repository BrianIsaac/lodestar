"""Tests for Pydantic models and deterministic tools."""

import asyncio
from datetime import date, datetime

from qwen_viet.models import (
    AccountBalance,
    ChartSpec,
    CohortInsight,
    CustomerLesson,
    CustomerProfile,
    CustomerReflection,
    GoalProjection,
    InsightCard,
    InsightSeverity,
    MoMChange,
    ProductInfo,
    SavingsGoal,
    ScenarioRequest,
    ScenarioResult,
    SpendingAnomaly,
    SpendingSummary,
    Transaction,
)


class TestModels:
    """Validate all Pydantic models instantiate correctly."""

    def test_customer_profile(self) -> None:
        p = CustomerProfile(
            customer_id="C001",
            full_name="Nguyễn Thị Hương",
            date_of_birth=date(1995, 3, 15),
            gender="F",
            city="Hà Nội",
            income_monthly=12_000_000,
        )
        assert p.segment == "mass"
        assert p.language == "vi"

    def test_transaction(self) -> None:
        t = Transaction(
            transaction_id="TX001",
            customer_id="C001",
            account_id="ACC-001",
            date=date(2026, 3, 15),
            amount=-150_000,
            category="food",
            merchant="Grab Food",
            description="CT DEN Grab Food VCB REF1234567890",
        )
        assert t.amount < 0
        assert t.currency == "VND"

    def test_account_balance(self) -> None:
        a = AccountBalance(
            account_id="ACC-001",
            customer_id="C001",
            entity="bank",
            account_type="current",
            balance=30_000_000,
        )
        assert a.entity == "bank"

    def test_spending_summary(self) -> None:
        s = SpendingSummary(
            customer_id="C001",
            period="2026-03",
            total=12_500_000,
            by_category={"food": 4_200_000, "transport": 1_800_000},
            by_category_pct={"food": 33.6, "transport": 14.4},
        )
        assert s.total > 0

    def test_chart_spec(self) -> None:
        c = ChartSpec(
            chart_type="donut",
            title="Chi tiêu tháng 3/2026",
            data={"labels": ["Ăn uống", "Di chuyển"], "values": [4200000, 1800000]},
        )
        assert c.chart_type == "donut"

    def test_insight_card(self) -> None:
        card = InsightCard(
            insight_id="INS001",
            customer_id="C001",
            title="Spending Alert",
            summary="Food spending 40% above average",
            severity=InsightSeverity.ANOMALY,
        )
        assert card.dismissed is False
        assert card.compliance_class == "information"

    def test_customer_lesson(self) -> None:
        lesson = CustomerLesson(
            lesson_id="L001",
            customer_id="C001",
            conditions="Weekend dining in months with public holidays",
            insight="Customer overspends on food Fri-Sun by 40%",
            confidence=0.85,
            importance=7.5,
        )
        assert lesson.times_evolved == 0

    def test_customer_reflection(self) -> None:
        r = CustomerReflection(
            reflection_id="R001",
            customer_id="C001",
            interaction_id="INT001",
            process_grade="A",
            outcome_quality="good",
            quadrant="earned_reward",
        )
        assert r.lesson_extracted is False

    def test_cohort_insight(self) -> None:
        ci = CohortInsight(
            cohort_key="hcmc_young_professional_mid_income",
            pattern_type="seasonal_overspend",
            category="dining",
            insight="Overspending on dining correlates with public holidays",
            supporting_count=75,
        )
        assert ci.min_customers == 5

    def test_product_info(self) -> None:
        p = ProductInfo(
            product_id="SB-CC-001",
            entity="bank",
            product_type="credit_card",
            name_vi="Thẻ tín dụng Shinhan Cashback",
            interest_rate=24.0,
            min_income=8_000_000,
        )
        assert p.currency == "VND"

    def test_savings_goal(self) -> None:
        g = SavingsGoal(
            goal_id="G001",
            customer_id="C001",
            name="Holiday Fund",
            target_amount=20_000_000,
            current_amount=14_400_000,
        )
        assert g.current_amount < g.target_amount

    def test_goal_projection(self) -> None:
        gp = GoalProjection(
            goal_id="G001",
            projected_date="2026-08",
            monthly_required=1_120_000,
            on_track=True,
            confidence=0.82,
        )
        assert gp.on_track is True

    def test_scenario_request(self) -> None:
        sr = ScenarioRequest(
            customer_id="C002",
            scenario_type="home_purchase",
            parameters={"property_value": 2_000_000_000, "down_payment_pct": 0.2},
        )
        assert sr.scenario_type == "home_purchase"

    def test_scenario_result(self) -> None:
        result = ScenarioResult(
            customer_id="C002",
            scenario_type="home_purchase",
            monthly_cashflow_before=8_300_000,
            monthly_cashflow_after=2_100_000,
            risk_flags=["DTI above 50%"],
        )
        assert len(result.risk_flags) == 1

    def test_spending_anomaly(self) -> None:
        a = SpendingAnomaly(
            category="food",
            current_amount=4_200_000,
            average_amount=3_000_000,
            deviation_pct=40.0,
        )
        assert a.deviation_pct > 0

    def test_mom_change(self) -> None:
        m = MoMChange(
            period="2026-03",
            category="food",
            amount=4_200_000,
            previous_amount=3_750_000,
            change_pct=12.0,
        )
        assert m.change_pct > 0


class TestSpendingTools:
    """Test deterministic spending tools against seeded data."""

    async def test_compute_spending_summary(self) -> None:
        from qwen_viet.tools.spending import compute_spending_summary

        summary = await compute_spending_summary("C001", "2025-09")
        assert summary.total > 0
        assert len(summary.by_category) > 0
        total_from_cats = sum(summary.by_category.values())
        assert abs(total_from_cats - summary.total) < 1.0
        pct_sum = sum(summary.by_category_pct.values())
        assert 99.0 <= pct_sum <= 101.0, f"Percentages sum to {pct_sum}"

    async def test_compute_income_pattern(self) -> None:
        from qwen_viet.tools.spending import compute_income_pattern

        pattern = await compute_income_pattern("C001")
        assert pattern.detected_payday is not None
        assert 20 <= pattern.detected_payday <= 28
        assert pattern.average_income > 0
        assert pattern.regularity_score > 0.5

    async def test_detect_anomalies(self) -> None:
        from qwen_viet.tools.spending import detect_anomalies

        anomalies = await detect_anomalies("C001", "2026-01")
        assert isinstance(anomalies, list)

    async def test_detect_recurring_charges(self) -> None:
        from qwen_viet.tools.spending import detect_recurring_charges

        charges = await detect_recurring_charges("C001")
        assert len(charges) > 0
        assert all(c.average_amount > 0 for c in charges)

    async def test_mom_change_tool(self) -> None:
        from qwen_viet.tools.spending import compute_month_over_month_change

        changes = await compute_month_over_month_change("C001", "food")
        assert len(changes) > 0


class TestChartTools:
    """Test chart spec generators."""

    def test_spending_chart_donut(self) -> None:
        from qwen_viet.tools.charts import generate_spending_chart

        summary = SpendingSummary(
            customer_id="C001",
            period="2026-03",
            total=10_000_000,
            by_category={"food": 4_000_000, "transport": 2_000_000, "shopping": 4_000_000},
            by_category_pct={"food": 40.0, "transport": 20.0, "shopping": 40.0},
        )
        chart = generate_spending_chart(summary)
        assert chart.chart_type == "donut"
        assert "labels" in chart.data
        assert len(chart.data["labels"]) == 3

    def test_goal_progress_chart(self) -> None:
        from qwen_viet.tools.charts import generate_goal_progress_chart

        goal = SavingsGoal(goal_id="G1", customer_id="C1", name="Holiday", target_amount=20_000_000, current_amount=14_000_000)
        proj = GoalProjection(goal_id="G1", projected_date="2026-08", monthly_required=1_200_000, on_track=True, confidence=0.8)
        chart = generate_goal_progress_chart(goal, proj)
        assert chart.chart_type == "progress"
        assert chart.data["progress_pct"] == 70.0

    def test_cashflow_waterfall(self) -> None:
        from qwen_viet.tools.charts import generate_cashflow_waterfall

        chart = generate_cashflow_waterfall(
            income=12_000_000,
            spending_by_category={"food": 4_000_000, "bills": 2_000_000},
        )
        assert chart.chart_type == "waterfall"
        steps = chart.data["steps"]
        assert steps[0]["type"] == "income"
        assert steps[-1]["type"] == "net"
        assert steps[-1]["value"] == 6_000_000


class TestGoalTools:
    """Test goal and financial projection tools."""

    async def test_savings_rate(self) -> None:
        from qwen_viet.tools.goals import compute_savings_rate

        rate = await compute_savings_rate("C001")
        assert rate.rate != 0, "Savings rate should be computed (non-zero)"
        assert rate.average_monthly_savings != 0, "Monthly savings should be computed"

    async def test_loan_affordability(self) -> None:
        from qwen_viet.tools.goals import calculate_loan_affordability

        result = await calculate_loan_affordability(
            customer_id="C001",
            loan_amount=500_000_000,
            term=120,
            rate=8.0,
        )
        assert result.monthly_payment > 0
        assert result.dti_after > 0
        assert result.max_affordable_amount >= 0


class TestSimulationTools:
    """Test cross-entity scenario simulation."""

    async def test_home_purchase_scenario(self) -> None:
        from qwen_viet.tools.simulation import simulate_scenario

        result = await simulate_scenario(
            customer_id="C002",
            scenario_type="home_purchase",
            parameters={"property_value": 2_000_000_000, "down_payment_pct": 0.2},
        )
        assert result.scenario_type == "home_purchase"
        assert len(result.entity_impacts) == 4
        entities = {e.entity for e in result.entity_impacts}
        assert entities == {"bank", "finance", "securities", "life"}
        assert result.monthly_cashflow_after < result.monthly_cashflow_before
