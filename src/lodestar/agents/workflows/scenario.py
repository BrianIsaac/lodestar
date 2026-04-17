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
    insight_text: dict[str, str]


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
    from lodestar.i18n import LANGS, localise_triple

    result = state.get("result")
    if not result:
        return {"chart_spec": None}

    steps = [
        {"label": "Thu nhập hiện tại", "value": result.monthly_cashflow_before, "type": "income"},
    ]
    # Snapshot the paying entities in declaration order so the i18n
    # arrays line up 1:1 with data["steps"].
    paying_entities: list[str] = []
    for impact in result.entity_impacts:
        payment = impact.metrics.get("monthly_payment", 0)
        if payment > 0:
            steps.append({"label": f"{impact.entity} payment", "value": -payment, "type": "expense"})
            paying_entities.append(impact.entity)

    steps.append({"label": "Còn lại", "value": result.monthly_cashflow_after, "type": "net"})

    step_labels_i18n: dict[str, list[str]] = {}
    for lang in LANGS:
        lang_labels = [localise_triple("step.current_income")[lang]]
        entity_template = localise_triple("step.entity_payment")
        lang_labels.extend(
            entity_template[lang].format(entity=ent.upper())
            for ent in paying_entities
        )
        lang_labels.append(localise_triple("step.remaining")[lang])
        step_labels_i18n[lang] = lang_labels

    chart = ChartSpec(
        chart_type="waterfall",
        title=f"Kịch bản: {result.scenario_type}",
        title_i18n=localise_triple("chart.scenario_title", t=result.scenario_type),
        data={"steps": steps, "currency": "VND"},
        step_labels_i18n=step_labels_i18n,
        summary=f"Dòng tiền: {result.monthly_cashflow_before:,.0f} → {result.monthly_cashflow_after:,.0f} VND",
        summary_i18n=localise_triple(
            "chart.scenario_summary",
            b=result.monthly_cashflow_before,
            a=result.monthly_cashflow_after,
        ),
    )
    return {"chart_spec": chart}


_SCENARIO_COPY: dict[str, dict[str, str]] = {
    "no_result": {
        "vi": "Không thể mô phỏng kịch bản này.",
        "en": "This scenario could not be simulated.",
        "ko": "이 시나리오는 시뮬레이션할 수 없습니다.",
    },
    "scenario": {
        "vi": "Kịch bản: {t}",
        "en": "Scenario: {t}",
        "ko": "시나리오: {t}",
    },
    "cashflow": {
        "vi": "Dòng tiền hàng tháng: {b:,.0f} → {a:,.0f} VND",
        "en": "Monthly cashflow: {b:,.0f} → {a:,.0f} VND",
        "ko": "월 현금흐름: {b:,.0f} → {a:,.0f} VND",
    },
    "risk_header": {
        "vi": "Cảnh báo rủi ro:",
        "en": "Risk flags:",
        "ko": "위험 경고:",
    },
}


async def compose_insight(state: ScenarioState) -> dict:
    """Compose human-readable scenario insight in every supported language.

    Runs the deterministic simulation tool once per language (no LLM, no
    DB writes) and renders the narrative using locale-specific headers.
    The tool itself already authors entity summaries + risk flags in all
    three locales (see tools/simulation.py)."""
    import asyncio

    from lodestar.tools.simulation import simulate_scenario

    result = state.get("result")
    if not result:
        return {"insight_text": dict(_SCENARIO_COPY["no_result"])}

    async def _per_lang(lang: str) -> str:
        localised = await simulate_scenario(
            customer_id=state["customer_id"],
            scenario_type=state["scenario_type"],
            parameters=state.get("parameters", {}),
            language=lang,
        )
        lines = [
            _SCENARIO_COPY["scenario"][lang].format(t=localised.scenario_type),
            _SCENARIO_COPY["cashflow"][lang].format(
                b=localised.monthly_cashflow_before,
                a=localised.monthly_cashflow_after,
            ),
            "",
        ]
        for impact in localised.entity_impacts:
            lines.append(f"[{impact.entity.upper()}] {impact.summary}")
        if localised.risk_flags:
            lines.append("")
            lines.append(_SCENARIO_COPY["risk_header"][lang])
            for flag in localised.risk_flags:
                lines.append(f"  ⚠ {flag}")
        return "\n".join(lines)

    rendered = await asyncio.gather(*[_per_lang(lang) for lang in ("vi", "en", "ko")])
    return {"insight_text": {"vi": rendered[0], "en": rendered[1], "ko": rendered[2]}}


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
