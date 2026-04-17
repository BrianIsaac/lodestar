"""Deterministic chart spec generators — return JSON for frontend rendering.

Every caption, axis label, and data label is authored in all three
supported locales at write time so the frontend can swap the chart
caption on language toggle without a round-trip. The i18n strings come
from :mod:`lodestar.i18n`, which keeps fixed chart-vocabulary
translations out of the LLM path.
"""

from lodestar.i18n import LANGS, localise_categories, localise_triple
from lodestar.models import ChartSpec, GoalProjection, MoMChange, SavingsGoal, SpendingSummary


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

    labels_i18n = {lang: localise_categories(labels, lang) for lang in LANGS}

    return ChartSpec(
        chart_type=chart_type,
        title=f"Chi tiêu tháng {summary.period}",
        title_i18n=localise_triple("chart.spending_title", period=summary.period),
        data={
            "labels": labels,
            "values": values,
            "percentages": percentages,
            "currency": summary.currency,
        },
        labels_i18n=labels_i18n,
        summary=f"Tổng chi tiêu: {summary.total:,.0f} {summary.currency}",
        summary_i18n=localise_triple(
            "chart.spending_summary",
            total=summary.total,
            currency=summary.currency,
        ),
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
        title_i18n={lang: goal.name for lang in LANGS},
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
        summary_i18n=localise_triple(
            "chart.goal_summary",
            pct=progress_pct,
            need=projection.monthly_required,
        ),
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

    # Axes keys that carry translatable captions — month names and
    # amount units. Periods themselves stay as raw date-like strings.
    axes_i18n = {
        lang: {
            "x": localise_triple("chart.axis_month")[lang],
            "y": localise_triple("chart.axis_amount_vnd")[lang],
        }
        for lang in LANGS
    }

    return ChartSpec(
        chart_type="line",
        title="Xu hướng chi tiêu",
        title_i18n=localise_triple("chart.trend_title"),
        data={
            "periods": periods,
            "amounts": amounts,
            "change_pct": changes,
            "currency": "VND",
        },
        axes={"x": "Tháng", "y": "Số tiền (VND)"},
        axes_i18n=axes_i18n,
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

    # Canonical step labels (what lives in data.steps). Keeping the raw
    # Vietnamese here preserves backwards compat; the i18n bundle below
    # carries the per-locale version used at render time.
    canonical_keys = ["step.income", *list(spending_by_category.keys()), "step.remaining"]
    steps = [{"label": "Thu nhập", "value": income, "type": "income"}]
    for cat, amount in sorted(spending_by_category.items(), key=lambda x: -x[1]):
        steps.append({"label": cat, "value": -amount, "type": "expense"})
    steps.append({"label": "Còn lại", "value": net, "type": "net"})

    # Build the step_labels_i18n arrays in the SAME order as steps above
    # so the frontend can index-lookup by step position. The sort order
    # above (by amount desc) has to match here.
    sorted_cats = [cat for cat, _ in sorted(spending_by_category.items(), key=lambda x: -x[1])]
    step_labels_i18n: dict[str, list[str]] = {}
    for lang in LANGS:
        lang_labels = [localise_triple("step.income")[lang]]
        lang_labels.extend(localise_categories(sorted_cats, lang))
        lang_labels.append(localise_triple("step.remaining")[lang])
        step_labels_i18n[lang] = lang_labels

    # Suppress unused-var warning — kept as a breadcrumb for future
    # refactors that may want canonical-key rendering.
    _ = canonical_keys

    return ChartSpec(
        chart_type="waterfall",
        title="Dòng tiền tháng này",
        title_i18n=localise_triple("chart.cashflow_title"),
        data={"steps": steps, "currency": currency},
        step_labels_i18n=step_labels_i18n,
        summary=f"Thu nhập {income:,.0f} - Chi tiêu {total_spending:,.0f} = Còn lại {net:,.0f} {currency}",
        summary_i18n=localise_triple(
            "chart.cashflow_summary",
            income=income,
            spend=total_spending,
            net=net,
            currency=currency,
        ),
    )
