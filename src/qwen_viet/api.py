"""FastAPI application — all endpoints for the financial coach PoC."""

import asyncio
import json
import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from qwen_viet.agents.background import run_background_cycle
from qwen_viet.agents.compliance import apply_compliance
from qwen_viet.config import settings
from qwen_viet.database import get_db, init_db
from qwen_viet.models import (
    ChatMessage,
    ChatResponse,
    InsightCard,
    InsightFeed,
    ProductFilters,
    ProductInfo,
    SavingsGoal,
    ScenarioRequest,
    ScenarioResult,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Shinhan Financial Coach API",
    description="SB1 AI Personal Financial Coach for SOL Vietnam",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CreateGoalRequest(BaseModel):
    """Request body for creating a savings goal."""

    customer_id: str
    name: str
    target_amount: float
    target_date: str = ""


class ChatRequest(BaseModel):
    """Request body for drill-down chat."""

    customer_id: str
    message: str
    insight_context: str = ""


class DismissRequest(BaseModel):
    """Request body for dismissing an insight."""

    customer_id: str


# --- Lifecycle ---

@app.on_event("startup")
async def startup() -> None:
    """Initialise database, RAG index, and seed data on first run."""
    settings.ensure_dirs()
    await init_db()

    from qwen_viet.rag.indexer import init_rag
    count = init_rag()
    logger.info("RAG initialised with %d products", count)

    db = await get_db()
    cursor = await db.execute("SELECT COUNT(*) FROM customers")
    row = await cursor.fetchone()
    await db.close()

    if row[0] == 0:
        from qwen_viet.data.seed_data import seed
        await seed()
        logger.info("Seeded synthetic data")

    cards = await run_background_cycle()
    logger.info("Initial background cycle: %d insight cards", len(cards))


# --- Insight Feed ---

@app.get("/feed/{customer_id}")
async def get_insight_feed(customer_id: str, limit: int = 10) -> InsightFeed:
    """Ranked insight cards for the customer's feed tab.

    Args:
        customer_id: Customer identifier.
        limit: Maximum cards to return.

    Returns:
        InsightFeed with ranked cards.
    """
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT * FROM insight_cards
               WHERE customer_id = ? AND dismissed = 0
               ORDER BY priority_score DESC, created_at DESC
               LIMIT ?""",
            (customer_id, limit),
        )
        rows = await cursor.fetchall()

        cards = [
            InsightCard(
                insight_id=r["insight_id"],
                customer_id=r["customer_id"],
                title=r["title"],
                summary=r["summary"],
                severity=r["severity"],
                compliance_class=r["compliance_class"],
                priority_score=r["priority_score"],
                dismissed=bool(r["dismissed"]),
                suggested_actions=json.loads(r["suggested_actions"] or "[]"),
            )
            for r in rows
        ]

        return InsightFeed(customer_id=customer_id, cards=cards, total=len(cards))
    finally:
        await db.close()


@app.post("/dismiss/{insight_id}")
async def dismiss_insight(insight_id: str, body: DismissRequest) -> dict:
    """Dismiss an insight card — feeds back into learning loop.

    Args:
        insight_id: Insight to dismiss.
        body: Request with customer_id.

    Returns:
        Confirmation dict.
    """
    db = await get_db()
    try:
        await db.execute(
            "UPDATE insight_cards SET dismissed = 1 WHERE insight_id = ? AND customer_id = ?",
            (insight_id, body.customer_id),
        )
        await db.commit()
    finally:
        await db.close()

    from qwen_viet.learning.journal import update_importance_post_outcome
    # dismissal = negative signal for any lesson that generated this insight
    # (simplified: we don't track which lesson generated which insight in PoC)

    return {"status": "dismissed", "insight_id": insight_id}


# --- Drill-Down Chat ---

@app.post("/chat/{insight_id}")
async def chat_drill_down(insight_id: str, body: ChatRequest) -> ChatResponse:
    """Scoped conversational thread about a specific insight.

    Args:
        insight_id: Insight being discussed.
        body: Chat request with message.

    Returns:
        ChatResponse with assistant message and optional chart.
    """
    try:
        from qwen_viet.agents.orchestrator import chat

        messages = [ChatMessage(role="user", content=body.message, insight_id=insight_id)]
        response = await chat(messages, body.customer_id, body.insight_context)
        return response
    except Exception as e:
        logger.exception("Chat error")
        return ChatResponse(
            message=ChatMessage(role="assistant", content=f"Lỗi hệ thống: {type(e).__name__}"),
        )


@app.post("/chat")
async def chat_general(body: ChatRequest) -> ChatResponse:
    """General chat without a specific insight context.

    Args:
        body: Chat request with message.

    Returns:
        ChatResponse with assistant message.
    """
    try:
        from qwen_viet.agents.orchestrator import chat

        messages = [ChatMessage(role="user", content=body.message)]
        return await chat(messages, body.customer_id)
    except Exception as e:
        logger.exception("Chat error")
        return ChatResponse(
            message=ChatMessage(role="assistant", content=f"Lỗi hệ thống: {type(e).__name__}"),
        )


# --- Scenario Simulation ---

@app.post("/simulate")
async def simulate_scenario(request: ScenarioRequest) -> ScenarioResult:
    """Cross-entity 'what if' simulation via digital twin.

    Args:
        request: Scenario parameters.

    Returns:
        ScenarioResult with per-entity impact.
    """
    from qwen_viet.tools.simulation import simulate_scenario as _simulate

    return await _simulate(
        customer_id=request.customer_id,
        scenario_type=request.scenario_type,
        parameters=request.parameters,
    )


# --- Goals ---

@app.get("/goals/{customer_id}")
async def get_goals(customer_id: str) -> list[SavingsGoal]:
    """Active savings goals with progress.

    Args:
        customer_id: Customer identifier.

    Returns:
        List of savings goals.
    """
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM goals WHERE customer_id = ?", (customer_id,)
        )
        rows = await cursor.fetchall()
        return [
            SavingsGoal(
                goal_id=r["goal_id"],
                customer_id=r["customer_id"],
                name=r["name"],
                target_amount=r["target_amount"],
                current_amount=r["current_amount"],
                target_date=r["target_date"] or "",
                created_at=r["created_at"] or "",
            )
            for r in rows
        ]
    finally:
        await db.close()


@app.post("/goals")
async def create_goal(body: CreateGoalRequest) -> SavingsGoal:
    """Create a new savings goal.

    Args:
        body: Goal creation parameters.

    Returns:
        The created goal.
    """
    from qwen_viet.tools.goals import create_goal as _create

    return await _create(
        customer_id=body.customer_id,
        name=body.name,
        target_amount=body.target_amount,
        target_date=body.target_date,
    )


# --- Products ---

@app.get("/products/search")
async def search_products(query: str, customer_id: str | None = None) -> list[ProductInfo]:
    """RAG-powered product search with optional eligibility filtering.

    Args:
        query: Search query.
        customer_id: Optional customer for eligibility check.

    Returns:
        Ranked product list.
    """
    from qwen_viet.tools.products import search_products as _search

    return await _search(query)


# --- SSE Insight Stream ---

@app.get("/stream/{customer_id}")
async def stream_insights(customer_id: str) -> EventSourceResponse:
    """SSE stream pushing new insight cards as they're generated.

    Args:
        customer_id: Customer to stream for.

    Returns:
        SSE event stream.
    """
    async def event_generator():
        while True:
            db = await get_db()
            try:
                cursor = await db.execute(
                    """SELECT * FROM insight_cards
                       WHERE customer_id = ? AND dismissed = 0
                       ORDER BY created_at DESC LIMIT 5""",
                    (customer_id,),
                )
                rows = await cursor.fetchall()
                for r in rows:
                    yield {
                        "event": "insight",
                        "data": json.dumps({
                            "insight_id": r["insight_id"],
                            "title": r["title"],
                            "summary": r["summary"],
                            "severity": r["severity"],
                            "priority_score": r["priority_score"],
                        }),
                    }
            finally:
                await db.close()

            await asyncio.sleep(settings.background_poll_interval)

    return EventSourceResponse(event_generator())


# --- Health ---

@app.get("/health")
async def health() -> dict:
    """Health check endpoint."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT COUNT(*) FROM customers")
        row = await cursor.fetchone()
        return {
            "status": "healthy",
            "customers": row[0],
        }
    finally:
        await db.close()
