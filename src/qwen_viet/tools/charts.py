"""Deterministic chart spec generators — return JSON for frontend rendering."""

from qwen_viet.models import ChartSpec, GoalProjection, MoMChange, SavingsGoal, SpendingSummary


def generate_spending_chart(
    summary: SpendingSummary, chart_type: str = "donut"
) -> ChartSpec:
    """Generate a spending breakdown chart specification.

    Args:
        summary: Pre-computed spending summary.
        chart_type: Chart type (``donut``, ``bar``).

    Returns:
        ChartSpec ready for frontend rendering.
    """
    labels = list(summary.by_category.keys())
    values = list(summary.by_category.values())
    percentages = [summary.by_category_pct.get(k, 0) for k in labels]

    return ChartSpec(
        chart_type=chart_type,
        title=f"Chi tiêu tháng {summary.period}",
        data={
            "labels": labels,
            "values": values,
            "percentages": percentages,
            "currency": summary.currency,
        },
        summary=f"Tổng chi tiêu: {summary.total:,.0f} {summary.currency}",
    )


def generate_goal_progress_chart(
    goal: SavingsGoal, projection: GoalProjection
) -> ChartSpec:
    """Generate a goal progress chart.

    Args:
        goal: Current savings goal state.
        projection: Projected completion data.

    Returns:
        ChartSpec with progress bar and projection line data.
    """
    progress_pct = (goal.current_amount / goal.target_amount * 100) if goal.target_amount > 0 else 0

    return ChartSpec(
        chart_type="progress",
        title=goal.name,
        data={
            "current": goal.current_amount,
            "target": goal.target_amount,
            "progress_pct": round(progress_pct, 1),
            "projected_date": projection.projected_date,
            "monthly_required": projection.monthly_required,
            "on_track": projection.on_track,
            "currency": "VND",
        },
        summary=f"{progress_pct:.0f}% hoàn thành — cần {projection.monthly_required:,.0f} VND/tháng",
    )


def generate_trend_chart(trends: list[MoMChange]) -> ChartSpec:
    """Generate a month-over-month trend line chart.

    Args:
        trends: List of monthly changes.

    Returns:
        ChartSpec for a line or grouped bar chart.
    """
    periods = [t.period for t in trends]
    amounts = [t.amount for t in trends]
    changes = [t.change_pct for t in trends]

    return ChartSpec(
        chart_type="line",
        title="Xu hướng chi tiêu",
        data={
            "periods": periods,
            "amounts": amounts,
            "change_pct": changes,
            "currency": "VND",
        },
        axes={"x": "Tháng", "y": "Số tiền (VND)"},
    )


def generate_cashflow_waterfall(
    income: float,
    spending_by_category: dict[str, float],
    currency: str = "VND",
) -> ChartSpec:
    """Generate an income minus expenses waterfall chart.

    Args:
        income: Monthly income amount.
        spending_by_category: Spending totals per category.
        currency: Currency code.

    Returns:
        ChartSpec for a waterfall chart showing net cashflow.
    """
    total_spending = sum(spending_by_category.values())
    net = income - total_spending

    steps = [{"label": "Thu nhập", "value": income, "type": "income"}]
    for cat, amount in sorted(spending_by_category.items(), key=lambda x: -x[1]):
        steps.append({"label": cat, "value": -amount, "type": "expense"})
    steps.append({"label": "Còn lại", "value": net, "type": "net"})

    return ChartSpec(
        chart_type="waterfall",
        title="Dòng tiền tháng này",
        data={"steps": steps, "currency": currency},
        summary=f"Thu nhập {income:,.0f} - Chi tiêu {total_spending:,.0f} = Còn lại {net:,.0f} {currency}",
    )
