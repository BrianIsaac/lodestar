"""LangGraph goal tracking workflow — compiled as a callable subgraph."""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from lodestar.models import ChartSpec, GoalProjection, IncomePattern, SavingsRate
from lodestar.tools.charts import generate_goal_progress_chart
from lodestar.tools.goals import compute_savings_rate, project_goal_completion
from lodestar.tools.spending import compute_income_pattern


class GoalState(TypedDict):
    """State for the goal tracking workflow."""

    customer_id: str
    goal_id: str
    income_pattern: IncomePattern | None
    savings_rate: SavingsRate | None
    projection: GoalProjection | None
    chart_spec: ChartSpec | None
    insight_text: dict[str, str]


async def fetch_income(state: GoalState) -> dict:
    """Detect income pattern for the customer."""
    pattern = await compute_income_pattern(state["customer_id"])
    return {"income_pattern": pattern}


async def fetch_savings_rate(state: GoalState) -> dict:
    """Compute savings rate over recent months."""
    rate = await compute_savings_rate(state["customer_id"])
    return {"savings_rate": rate}


async def project_completion(state: GoalState) -> dict:
    """Project when the goal will be completed."""
    projection = await project_goal_completion(state["goal_id"])
    return {"projection": projection}


def build_chart(state: GoalState) -> dict:
    """Generate goal progress chart."""
    projection = state.get("projection")
    if not projection:
        return {"chart_spec": None}

    from lodestar.database import get_db
    import asyncio

    async def _get_goal():
        db = await get_db()
        try:
            cursor = await db.execute(
                "SELECT * FROM goals WHERE goal_id = ?", (state["goal_id"],)
            )
            row = await cursor.fetchone()
            if row:
                from lodestar.models import SavingsGoal
                return SavingsGoal(
                    goal_id=row["goal_id"],
                    customer_id=row["customer_id"],
                    name=row["name"],
                    target_amount=row["target_amount"],
                    current_amount=row["current_amount"],
                )
            return None
        finally:
            await db.close()

    goal = asyncio.get_event_loop().run_until_complete(_get_goal())
    if not goal:
        return {"chart_spec": None}

    chart = generate_goal_progress_chart(goal, projection)
    return {"chart_spec": chart}


_GOAL_COPY: dict[str, dict[str, str]] = {
    "no_projection": {
        "vi": "Không thể dự báo tiến độ mục tiêu.",
        "en": "Cannot project goal progress.",
        "ko": "목표 진척을 예측할 수 없습니다.",
    },
    "on_track": {
        "vi": "Mục tiêu đang đúng tiến độ — dự kiến hoàn thành {d}.",
        "en": "Goal is on track — expected completion {d}.",
        "ko": "목표가 순조롭게 진행 중입니다 — 예상 완료일 {d}.",
    },
    "needs_adjust": {
        "vi": "Mục tiêu cần điều chỉnh — cần {m:,.0f} VND/tháng.",
        "en": "Goal needs adjustment — {m:,.0f} VND/month required.",
        "ko": "목표 조정이 필요합니다 — 월 {m:,.0f} VND 필요.",
    },
    "savings_rate": {
        "vi": "Tỷ lệ tiết kiệm hiện tại: {r:.1f}% thu nhập.",
        "en": "Current savings rate: {r:.1f}% of income.",
        "ko": "현재 저축률: 소득의 {r:.1f}%.",
    },
    "payday": {
        "vi": "Ngày lương phát hiện: ngày {d} hàng tháng.",
        "en": "Payday detected: day {d} of each month.",
        "ko": "급여일 감지: 매월 {d}일.",
    },
}


def compose_insight(state: GoalState) -> dict:
    """Compose human-readable goal tracking insight in every language."""
    projection = state.get("projection")
    savings = state.get("savings_rate")
    income = state.get("income_pattern")

    if not projection:
        return {"insight_text": dict(_GOAL_COPY["no_projection"])}

    out: dict[str, str] = {}
    for lang in ("vi", "en", "ko"):
        lines: list[str] = []
        if projection.on_track:
            lines.append(_GOAL_COPY["on_track"][lang].format(d=projection.projected_date))
        else:
            lines.append(_GOAL_COPY["needs_adjust"][lang].format(m=projection.monthly_required))
        if savings:
            lines.append(_GOAL_COPY["savings_rate"][lang].format(r=savings.rate))
        if income and income.detected_payday:
            lines.append(_GOAL_COPY["payday"][lang].format(d=income.detected_payday))
        out[lang] = "\n".join(lines)

    return {"insight_text": out}


def build_goal_graph() -> StateGraph:
    """Build and return the goal tracking workflow graph.

    Returns:
        Compiled LangGraph StateGraph.
    """
    builder = StateGraph(GoalState)

    builder.add_node("fetch_income", fetch_income)
    builder.add_node("fetch_savings_rate", fetch_savings_rate)
    builder.add_node("project_completion", project_completion)
    builder.add_node("build_chart", build_chart)
    builder.add_node("compose_insight", compose_insight)

    builder.add_edge(START, "fetch_income")
    builder.add_edge(START, "fetch_savings_rate")
    builder.add_edge("fetch_income", "project_completion")
    builder.add_edge("fetch_savings_rate", "project_completion")
    builder.add_edge("project_completion", "build_chart")
    builder.add_edge("build_chart", "compose_insight")
    builder.add_edge("compose_insight", END)

    return builder.compile()


goal_graph = build_goal_graph()
