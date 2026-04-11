"""LangGraph spending analysis workflow — compiled as a callable subgraph."""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from lodestar.models import ChartSpec, SpendingSummary
from lodestar.tools.charts import generate_spending_chart
from lodestar.tools.spending import (
    compute_spending_summary,
    detect_anomalies,
)


class SpendingState(TypedDict):
    """State for the spending analysis workflow."""

    customer_id: str
    period: str
    summary: SpendingSummary | None
    anomalies: list
    chart_spec: ChartSpec | None
    insight_text: str


async def fetch_and_summarise(state: SpendingState) -> dict:
    """Fetch transactions and compute spending summary."""
    summary = await compute_spending_summary(state["customer_id"], state["period"])
    return {"summary": summary}


async def check_anomalies(state: SpendingState) -> dict:
    """Detect spending anomalies against 3-month averages."""
    anomalies = await detect_anomalies(state["customer_id"], state["period"])
    return {"anomalies": anomalies}


def build_chart(state: SpendingState) -> dict:
    """Generate chart spec from the computed summary."""
    summary = state["summary"]
    if not summary or summary.total == 0:
        return {"chart_spec": None}
    chart = generate_spending_chart(summary, chart_type="donut")
    return {"chart_spec": chart}


def compose_insight(state: SpendingState) -> dict:
    """Compose human-readable insight text from tool results."""
    summary = state["summary"]
    anomalies = state.get("anomalies", [])

    if not summary or summary.total == 0:
        return {"insight_text": "Không có dữ liệu chi tiêu cho kỳ này."}

    top_cats = sorted(summary.by_category.items(), key=lambda x: -x[1])[:3]
    lines = [f"Tổng chi tiêu tháng {summary.period}: {summary.total:,.0f} VND"]
    for cat, amount in top_cats:
        pct = summary.by_category_pct.get(cat, 0)
        lines.append(f"  - {cat}: {amount:,.0f} VND ({pct}%)")

    if anomalies:
        lines.append("")
        for a in anomalies:
            lines.append(f"  ⚠ {a.description}")

    return {"insight_text": "\n".join(lines)}


def build_spending_graph() -> StateGraph:
    """Build and return the spending analysis workflow graph.

    Returns:
        Compiled LangGraph StateGraph.
    """
    builder = StateGraph(SpendingState)

    builder.add_node("fetch_and_summarise", fetch_and_summarise)
    builder.add_node("check_anomalies", check_anomalies)
    builder.add_node("build_chart", build_chart)
    builder.add_node("compose_insight", compose_insight)

    builder.add_edge(START, "fetch_and_summarise")
    builder.add_edge("fetch_and_summarise", "check_anomalies")
    builder.add_edge("fetch_and_summarise", "build_chart")
    builder.add_edge("check_anomalies", "compose_insight")
    builder.add_edge("build_chart", "compose_insight")
    builder.add_edge("compose_insight", END)

    return builder.compile()


spending_graph = build_spending_graph()
