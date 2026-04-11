"""LangGraph cross-entity scenario simulation workflow."""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from lodestar.models import ChartSpec, ScenarioResult
from lodestar.tools.simulation import simulate_scenario


class ScenarioState(TypedDict):
    """State for the scenario simulation workflow."""

    customer_id: str
    scenario_type: str
    parameters: dict
    result: ScenarioResult | None
    chart_spec: ChartSpec | None
    insight_text: str


async def run_simulation(state: ScenarioState) -> dict:
    """Execute the cross-entity scenario simulation."""
    result = await simulate_scenario(
        customer_id=state["customer_id"],
        scenario_type=state["scenario_type"],
        parameters=state.get("parameters", {}),
    )
    return {"result": result}


def build_chart(state: ScenarioState) -> dict:
    """Generate a comparison chart from simulation results."""
    result = state.get("result")
    if not result:
        return {"chart_spec": None}

    steps = [
        {"label": "Thu nhập hiện tại", "value": result.monthly_cashflow_before, "type": "income"},
    ]
    for impact in result.entity_impacts:
        payment = impact.metrics.get("monthly_payment", 0)
        if payment > 0:
            steps.append({"label": f"{impact.entity} payment", "value": -payment, "type": "expense"})

    steps.append({"label": "Còn lại", "value": result.monthly_cashflow_after, "type": "net"})

    chart = ChartSpec(
        chart_type="waterfall",
        title=f"Kịch bản: {result.scenario_type}",
        data={"steps": steps, "currency": "VND"},
        summary=f"Dòng tiền: {result.monthly_cashflow_before:,.0f} → {result.monthly_cashflow_after:,.0f} VND",
    )
    return {"chart_spec": chart}


def compose_insight(state: ScenarioState) -> dict:
    """Compose human-readable scenario insight."""
    result = state.get("result")
    if not result:
        return {"insight_text": "Không thể mô phỏng kịch bản này."}

    lines = [
        f"Kịch bản: {result.scenario_type}",
        f"Dòng tiền hàng tháng: {result.monthly_cashflow_before:,.0f} → {result.monthly_cashflow_after:,.0f} VND",
        "",
    ]

    for impact in result.entity_impacts:
        lines.append(f"[{impact.entity.upper()}] {impact.summary}")

    if result.risk_flags:
        lines.append("")
        lines.append("Cảnh báo rủi ro:")
        for flag in result.risk_flags:
            lines.append(f"  ⚠ {flag}")

    return {"insight_text": "\n".join(lines)}


def build_scenario_graph() -> StateGraph:
    """Build and return the scenario simulation workflow graph.

    Returns:
        Compiled LangGraph StateGraph.
    """
    builder = StateGraph(ScenarioState)

    builder.add_node("run_simulation", run_simulation)
    builder.add_node("build_chart", build_chart)
    builder.add_node("compose_insight", compose_insight)

    builder.add_edge(START, "run_simulation")
    builder.add_edge("run_simulation", "build_chart")
    builder.add_edge("run_simulation", "compose_insight")
    builder.add_edge("build_chart", END)
    builder.add_edge("compose_insight", END)

    return builder.compile()


scenario_graph = build_scenario_graph()
