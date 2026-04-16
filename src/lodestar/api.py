"""FastAPI application — all endpoints for the financial coach PoC."""

import asyncio
import json
import logging
import uuid
from datetime import date, timedelta

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
    """Initialise database, RAG index, and seed data on first run.

    The feed starts empty on every boot — insight cards are generated
    live from transactions as they stream in via POST /demo/transaction
    (or a future real transaction pipeline). This makes the autonomous
    monitoring story demonstrable: judges see the agent react to real
    events instead of a pre-populated feed.
    """
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

    # Start with a clean feed on every boot. Transaction history stays
    # intact so trigger rules still have a baseline to detect anomalies.
    db = await get_db()
    try:
        await db.execute("DELETE FROM insight_cards")
        await db.commit()
    finally:
        await db.close()
    logger.info("Insight feed cleared — waiting for live transactions")


# --- Insight Feed ---

@app.get("/feed/{customer_id}")
async def get_insight_feed(
    customer_id: str,
    limit: int = 10,
    language: str = "vi",
) -> InsightFeed:
    """Ranked insight cards for the customer's feed tab.

    Cards are pre-localised at write time (see background.py templates).
    This endpoint just reads the stored JSON and promotes the requested
    language into the flat `title` / `summary` fields — no LLM calls,
    no cache layer needed.

    Args:
        customer_id: Customer identifier.
        limit: Maximum cards to return.
        language: Display language code (vi | en | ko). Falls back to
            Vietnamese if an unknown code arrives.

    Returns:
        InsightFeed with ranked cards.
    """
    lang = language if language in {"vi", "en", "ko"} else "vi"

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

        cards: list[InsightCard] = []
        for r in rows:
            cols = r.keys()
            title_i18n = _load_json_dict(r["title_i18n"] if "title_i18n" in cols else None)
            summary_i18n = _load_json_dict(r["summary_i18n"] if "summary_i18n" in cols else None)
            action_hint_i18n = _load_action_hint(
                r["action_hint_i18n"] if "action_hint_i18n" in cols else None
            )
            quick_prompts_i18n = _load_quick_prompts(
                r["quick_prompts_i18n"] if "quick_prompts_i18n" in cols else None
            )
            title = (title_i18n or {}).get(lang) or r["title"]
            summary = (summary_i18n or {}).get(lang) or r["summary"]
            cards.append(
                InsightCard(
                    insight_id=r["insight_id"],
                    customer_id=r["customer_id"],
                    title=title,
                    summary=summary,
                    title_i18n=title_i18n,
                    summary_i18n=summary_i18n,
                    action_hint_i18n=action_hint_i18n,
                    quick_prompts_i18n=quick_prompts_i18n,
                    severity=r["severity"],
                    compliance_class=r["compliance_class"],
                    priority_score=r["priority_score"],
                    dismissed=bool(r["dismissed"]),
                    suggested_actions=json.loads(r["suggested_actions"] or "[]"),
                )
            )
    finally:
        await db.close()

    return InsightFeed(customer_id=customer_id, cards=cards, total=len(cards))


def _load_json_dict(raw: str | None) -> dict[str, str] | None:
    """Parse a JSON string column into a dict, returning None on empty/bad
    input. Used when reading the i18n columns off insight_cards rows."""
    if not raw:
        return None
    try:
        value = json.loads(raw)
    except (TypeError, ValueError):
        return None
    return value if isinstance(value, dict) else None


def _load_action_hint(raw: str | None) -> dict[str, list[str]] | None:
    """Parse the action_hint_i18n JSON column."""
    if not raw:
        return None
    try:
        value = json.loads(raw)
    except (TypeError, ValueError):
        return None
    if not isinstance(value, dict):
        return None
    return {
        k: v for k, v in value.items() if isinstance(v, list) and all(isinstance(s, str) for s in v)
    }


def _load_quick_prompts(raw: str | None):
    """Parse the quick_prompts_i18n JSON column into QuickPrompt objects."""
    if not raw:
        return None
    try:
        value = json.loads(raw)
    except (TypeError, ValueError):
        return None
    if not isinstance(value, dict):
        return None
    from lodestar.models import QuickPrompt as _QP
    out: dict[str, list] = {}
    for lang, items in value.items():
        if not isinstance(items, list):
            continue
        out[lang] = [_QP(**item) if isinstance(item, dict) else item for item in items]
    return out or None


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

    All name/description variants are authored upfront in the catalogue,
    so this endpoint returns the full ProductInfo unchanged and lets the
    client pick the right field by `language`. `language` is accepted
    for future server-side filtering but does not trigger translation.

    Args:
        query: Search query (Vietnamese, English, or Korean — bge-m3 is
            multilingual).
        customer_id: Optional customer for eligibility check.
        language: Client locale hint (vi | en | ko). Informational only.

    Returns:
        Ranked product list with all language fields populated.
    """
    _ = language  # reserved for future server-side localisation
    from lodestar.tools.products import search_products as _search

    return await _search(query)


# --- Recent transactions ---


@app.get("/transactions/{customer_id}")
async def recent_transactions(customer_id: str, limit: int = 10) -> list[dict]:
    """Return the most recent transactions for a customer.

    Used by the feed-tab transaction strip so the audience can see the
    cause (transaction) and the effect (insight card) in the same view.

    Args:
        customer_id: Customer identifier.
        limit: Number of transactions to return, newest first.

    Returns:
        List of transaction dicts ordered by date DESC.
    """
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT transaction_id, date, amount, category, merchant, entity
               FROM transactions WHERE customer_id = ?
               ORDER BY date DESC, transaction_id DESC
               LIMIT ?""",
            (customer_id, limit),
        )
        rows = await cursor.fetchall()
        return [
            {
                "transaction_id": r["transaction_id"],
                "date": r["date"],
                "amount": r["amount"],
                "category": r["category"],
                "merchant": r["merchant"],
                "entity": r["entity"],
            }
            for r in rows
        ]
    finally:
        await db.close()


# --- SSE Insight Stream ---

@app.get("/stream/{customer_id}")
async def stream_insights(customer_id: str) -> EventSourceResponse:
    """SSE stream emitting insight cards as they're created.

    Diff-only semantics: cards already present when the connection opens
    are captured in a `seen` set and never re-emitted. Only rows whose
    `insight_id` appears AFTER the connection was established flow through
    to the client — giving the frontend a clean "a new card just arrived"
    signal that it can animate in.

    Args:
        customer_id: Customer to stream for.

    Returns:
        SSE event stream.
    """
    async def event_generator():
        seen: set[str] = set()
        # Seed the seen set with whatever's already on screen so we only
        # emit genuinely new arrivals after connection.
        db = await get_db()
        try:
            cursor = await db.execute(
                "SELECT insight_id FROM insight_cards WHERE customer_id = ?",
                (customer_id,),
            )
            rows = await cursor.fetchall()
            seen.update(r["insight_id"] for r in rows)
        finally:
            await db.close()

        # Tighter poll cadence than the old background interval — the demo
        # flow wants sub-second feedback when a transaction drops.
        poll_interval_seconds = max(1, min(2, settings.background_poll_interval))

        while True:
            db = await get_db()
            try:
                cursor = await db.execute(
                    """SELECT * FROM insight_cards
                       WHERE customer_id = ? AND dismissed = 0
                       ORDER BY created_at ASC""",
                    (customer_id,),
                )
                rows = await cursor.fetchall()
            finally:
                await db.close()

            for r in rows:
                iid = r["insight_id"]
                if iid in seen:
                    continue
                seen.add(iid)
                title_i18n = _load_json_dict(
                    r["title_i18n"] if "title_i18n" in r.keys() else None
                )
                summary_i18n = _load_json_dict(
                    r["summary_i18n"] if "summary_i18n" in r.keys() else None
                )
                action_hint_i18n = _load_action_hint(
                    r["action_hint_i18n"] if "action_hint_i18n" in r.keys() else None
                )
                quick_prompts_i18n = _load_quick_prompts(
                    r["quick_prompts_i18n"] if "quick_prompts_i18n" in r.keys() else None
                )
                payload = {
                    "insight_id": iid,
                    "customer_id": r["customer_id"],
                    "title": r["title"],
                    "summary": r["summary"],
                    "title_i18n": title_i18n,
                    "summary_i18n": summary_i18n,
                    "action_hint_i18n": action_hint_i18n,
                    "quick_prompts_i18n": (
                        {
                            lang: [
                                p.model_dump() if hasattr(p, "model_dump") else p
                                for p in prompts
                            ]
                            for lang, prompts in quick_prompts_i18n.items()
                        }
                        if quick_prompts_i18n
                        else None
                    ),
                    "severity": r["severity"],
                    "priority_score": r["priority_score"],
                    "dismissed": bool(r["dismissed"]),
                }
                yield {
                    "event": "insight",
                    "data": json.dumps(payload, ensure_ascii=False),
                }

            await asyncio.sleep(poll_interval_seconds)

    return EventSourceResponse(event_generator())


# --- Demo transactions ---


class DemoTransactionRequest(BaseModel):
    """Body for POST /demo/transaction — synthesises a customer action and
    immediately runs the trigger pipeline so judges can see the agent
    react in real time."""

    customer_id: str
    merchant: str
    amount: float  # negative for outflow, positive for credit
    category: str = "shopping"
    entity: str = "bank"
    description: str = ""


@app.post("/demo/transaction")
async def inject_demo_transaction(body: DemoTransactionRequest) -> dict:
    """Insert a synthetic transaction, re-evaluate triggers for that
    customer, and return any new insight cards that fired.

    Uses the exact same trigger + compose path as the background loop —
    `/demo/transaction` is literally the autonomous pipeline invoked by
    an explicit event rather than a timer.
    """
    from lodestar.agents.background import (
        _compose_insight_card,
        _is_duplicate,
        _store_insight,
    )
    from lodestar.agents.triggers import run_all_triggers

    today = date.today().isoformat()
    transaction_id = f"TX-DEMO-{uuid.uuid4().hex[:10]}"

    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT account_id FROM accounts WHERE customer_id = ? LIMIT 1",
            (body.customer_id,),
        )
        account_row = await cursor.fetchone()
        account_id = account_row["account_id"] if account_row else body.customer_id

        await db.execute(
            """INSERT INTO transactions
               (transaction_id, customer_id, account_id, date, amount, category,
                merchant, description, entity, currency)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'VND')""",
            (
                transaction_id,
                body.customer_id,
                account_id,
                today,
                body.amount,
                body.category,
                body.merchant,
                body.description or body.merchant,
                body.entity,
            ),
        )
        await db.commit()

        # Re-fetch the customer's recent transaction window for trigger eval.
        start_date = (date.today() - timedelta(days=120)).isoformat()
        cursor = await db.execute(
            "SELECT * FROM transactions WHERE customer_id = ? AND date >= ? ORDER BY date",
            (body.customer_id, start_date),
        )
        tx_rows = await cursor.fetchall()
    finally:
        await db.close()

    from lodestar.models import Transaction as _Tx
    transactions = [
        _Tx(
            transaction_id=r["transaction_id"],
            customer_id=r["customer_id"],
            account_id=r["account_id"],
            date=r["date"],
            amount=r["amount"],
            category=r["category"],
            merchant=r["merchant"],
            description=r["description"],
            entity=r["entity"],
        )
        for r in tx_rows
    ]

    events = run_all_triggers(transactions, body.customer_id)
    new_cards: list[InsightCard] = []
    for event in events:
        if await _is_duplicate(body.customer_id, event.trigger_type):
            continue
        card = _compose_insight_card(event)
        await _store_insight(card)
        new_cards.append(card)
        logger.info("Demo insight: %s for %s", card.title, body.customer_id)

    return {
        "transaction_id": transaction_id,
        "transaction": {
            "merchant": body.merchant,
            "amount": body.amount,
            "category": body.category,
            "entity": body.entity,
            "date": today,
        },
        "new_insights": [c.model_dump() for c in new_cards],
    }


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
