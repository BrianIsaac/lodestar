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
    insight_text: str


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


def compose_insight(state: GoalState) -> dict:
    """Compose human-readable goal tracking insight."""
    projection = state.get("projection")
    savings = state.get("savings_rate")
    income = state.get("income_pattern")

    if not projection:
        return {"insight_text": "Không thể dự báo tiến độ mục tiêu."}

    lines = []
    if projection.on_track:
        lines.append(f"Mục tiêu đang đúng tiến độ — dự kiến hoàn thành {projection.projected_date}.")
    else:
        lines.append(f"Mục tiêu cần điều chỉnh — cần {projection.monthly_required:,.0f} VND/tháng.")

    if savings:
        lines.append(f"Tỷ lệ tiết kiệm hiện tại: {savings.rate:.1f}% thu nhập.")

    if income and income.detected_payday:
        lines.append(f"Ngày lương phát hiện: ngày {income.detected_payday} hàng tháng.")

    return {"insight_text": "\n".join(lines)}


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
