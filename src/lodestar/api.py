"""FastAPI application — all endpoints for the financial coach PoC."""

import asyncio
import json
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from lodestar.agents.background import run_background_cycle
from lodestar.config import settings
from lodestar.database import get_db, init_db
from lodestar.models import (
    ChatMessage,
    ChatResponse,
    InsightCard,
    InsightFeed,
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
    language: str = "vi"


class DismissRequest(BaseModel):
    """Request body for dismissing an insight."""

    customer_id: str


# --- Lifecycle ---

@app.on_event("startup")
async def startup() -> None:
    """Initialise database, RAG index, and seed data on first run."""
    settings.ensure_dirs()
    await init_db()

    from lodestar.rag.indexer import init_rag
    count = init_rag()
    logger.info("RAG initialised with %d products", count)

    db = await get_db()
    cursor = await db.execute("SELECT COUNT(*) FROM customers")
    row = await cursor.fetchone()
    await db.close()

    if row[0] == 0:
        from lodestar.data.seed_data import seed
        await seed()
        logger.info("Seeded synthetic data")

    cards = await run_background_cycle()
    logger.info("Initial background cycle: %d insight cards", len(cards))

    # Fire-and-forget: translate current feed titles + summaries into En and
    # Ko so the first user who toggles language after boot sees an instant
    # cached feed instead of paying the LLM round-trip per card.
    if cards:
        from lodestar.agents.translate import warm_cache_for_cards
        pairs = [(c.title, c.summary) for c in cards]
        asyncio.create_task(warm_cache_for_cards(pairs))
        logger.info("Translation warm-up queued for %d cards", len(cards))


# --- Insight Feed ---

@app.get("/feed/{customer_id}")
async def get_insight_feed(
    customer_id: str,
    limit: int = 10,
    language: str = "vi",
) -> InsightFeed:
    """Ranked insight cards for the customer's feed tab.

    Args:
        customer_id: Customer identifier.
        limit: Maximum cards to return.
        language: Display language — "vi" returns stored text verbatim,
            "en" or "ko" runs a cached LLM translation over title and
            summary for each card.

    Returns:
        InsightFeed with ranked cards (translated if needed).
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
    finally:
        await db.close()

    if language != "vi" and cards:
        from lodestar.agents.translate import translate_many

        titles = await translate_many([c.title for c in cards], language)
        summaries = await translate_many([c.summary for c in cards], language)
        cards = [
            c.model_copy(update={"title": titles[i], "summary": summaries[i]})
            for i, c in enumerate(cards)
        ]

    return InsightFeed(customer_id=customer_id, cards=cards, total=len(cards))


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
        from lodestar.agents.orchestrator import chat

        messages = [ChatMessage(role="user", content=body.message, insight_id=insight_id)]
        response = await chat(
            messages,
            body.customer_id,
            body.insight_context,
            language=body.language,
        )
        return response
    except Exception as e:
        logger.exception("Chat error")
        return ChatResponse(
            message=ChatMessage(role="assistant", content=_system_error(body.language, e)),
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
        from lodestar.agents.orchestrator import chat

        messages = [ChatMessage(role="user", content=body.message)]
        return await chat(messages, body.customer_id, language=body.language)
    except Exception as e:
        logger.exception("Chat error")
        return ChatResponse(
            message=ChatMessage(role="assistant", content=_system_error(body.language, e)),
        )


_SYSTEM_ERROR: dict[str, str] = {
    "vi": "Lỗi hệ thống",
    "en": "System error",
    "ko": "시스템 오류",
}


def _system_error(language: str, exc: BaseException) -> str:
    """Format a language-appropriate system error line for a chat response."""
    prefix = _SYSTEM_ERROR.get(language, _SYSTEM_ERROR["vi"])
    return f"{prefix}: {type(exc).__name__}"


# --- Scenario Simulation ---

@app.post("/simulate")
async def simulate_scenario(request: ScenarioRequest) -> ScenarioResult:
    """Cross-entity 'what if' simulation via digital twin.

    Args:
        request: Scenario parameters.

    Returns:
        ScenarioResult with per-entity impact.
    """
    from lodestar.tools.simulation import simulate_scenario as _simulate

    return await _simulate(
        customer_id=request.customer_id,
        scenario_type=request.scenario_type,
        parameters=request.parameters,
        language=request.language,
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
    from lodestar.tools.goals import create_goal as _create

    return await _create(
        customer_id=body.customer_id,
        name=body.name,
        target_amount=body.target_amount,
        target_date=body.target_date,
    )


# --- Products ---

@app.get("/products/search")
async def search_products(
    query: str,
    customer_id: str | None = None,
    language: str = "vi",
) -> list[ProductInfo]:
    """RAG-powered product search with optional eligibility filtering.

    Args:
        query: Search query (Vietnamese or English — bge-m3 is multilingual).
        customer_id: Optional customer for eligibility check.
        language: Display language. Vietnamese returns stored fields
            verbatim. For English, the catalogue already carries `name_en`
            on every product, so names are free. For Korean — and for
            descriptions in any non-Vi locale — text is fed through the
            two-tier translation cache so repeat searches are instant.

    Returns:
        Ranked product list, localised to the requested language.
    """
    from lodestar.tools.products import search_products as _search
    from lodestar.agents.translate import translate_many

    products = await _search(query)

    if language == "vi" or not products:
        return products

    # Vietnamese descriptions → target language (always translated since
    # the catalogue has only Vietnamese descriptions).
    descriptions_vi = [p.description_vi or "" for p in products]
    descriptions_out = await translate_many(descriptions_vi, language)

    # Names: Korean has no catalogue field, so translate from Vietnamese.
    # English already has name_en on every product — use it directly.
    if language == "ko":
        names_out = await translate_many([p.name_vi for p in products], language)
    else:
        names_out = [p.name_en or p.name_vi for p in products]

    out: list[ProductInfo] = []
    for p, new_name, new_desc in zip(products, names_out, descriptions_out):
        out.append(
            p.model_copy(
                update={
                    "name_vi": new_name,
                    "description_vi": new_desc,
                }
            )
        )
    return out


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
