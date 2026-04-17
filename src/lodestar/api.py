"""FastAPI application — all endpoints for the financial coach PoC."""

import asyncio
import json
import logging
import uuid
from contextlib import asynccontextmanager
from datetime import date, timedelta
from typing import Any, AsyncIterator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

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


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Startup + shutdown hook for the ASGI app.

    Replaces the deprecated ``@app.on_event("startup")`` pattern so the
    init path has a single, testable entry point.
    """
    settings.ensure_dirs()
    await init_db()

    from lodestar.rag.embeddings import embed_texts
    from lodestar.rag.indexer import init_rag

    count = init_rag()
    logger.info("RAG initialised with %d products", count)

    # Warm bge-m3 unconditionally. init_rag only embeds on first ingest
    # and skips on schema-version match, which would leave the first
    # live /products/search request to absorb the ~30s model load.
    try:
        embed_texts(["warmup"])
        logger.info("Embedder warmed")
    except Exception:
        logger.exception("Embedder warmup failed")

    db = await get_db()
    try:
        cursor = await db.execute("SELECT COUNT(*) FROM customers")
        row = await cursor.fetchone()
    finally:
        await db.close()

    customer_count = row[0] if row else 0
    if customer_count == 0:
        from lodestar.data.seed_data import seed
        await seed()
        logger.info("Seeded synthetic data")

    # Start with a clean feed on every boot. Transaction history and the
    # learning journal are preserved — only the ephemeral card stream
    # resets, along with the interactions/reflections that reference each
    # card via FK (otherwise DELETE FROM insight_cards aborts).
    db = await get_db()
    try:
        await db.execute("DELETE FROM reflections")
        await db.execute("DELETE FROM interactions")
        await db.execute("DELETE FROM insight_cards")
        await db.commit()
    finally:
        await db.close()
    logger.info("Insight feed cleared — waiting for live transactions")

    yield


app = FastAPI(
    title="Shinhan Financial Coach API",
    description="SB1 AI Personal Financial Coach for SOL Vietnam",
    version="0.1.0",
    lifespan=lifespan,
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


def _lessons_applied_from_interaction(interaction: dict[str, Any]) -> list[str]:
    """Extract the lesson IDs that fed a card's memory injection, if any.

    The agent_reasoning message persisted at card-birth carries the
    ``lessons_applied`` list. Returns an empty list when the shape is
    unexpected (older interactions, partial rows).
    """
    for msg in interaction.get("messages") or []:
        if isinstance(msg, dict) and msg.get("role") == "agent_reasoning":
            ids = msg.get("lessons_applied") or []
            if isinstance(ids, list):
                return [str(x) for x in ids if x]
    return []


# --- Insight Feed ---

@app.get("/feed/{customer_id}")
async def get_insight_feed(
    customer_id: str,
    limit: int = 10,
    language: str = "vi",
) -> InsightFeed:
    """Ranked insight cards for the customer's feed tab.

    Cards are authored by the detector agent in all supported locales at
    write time, so `/feed` is a pure SELECT with no runtime translation.
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
            chart_spec = _load_chart_spec(
                r["chart_spec"] if "chart_spec" in cols else None
            )
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
                    chart_spec=chart_spec,
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


def _load_chart_spec(raw: str | None):
    """Parse the chart_spec JSON column into a ChartSpec, returning None on
    empty/bad input. Declared as a local import so ChartSpec stays out of the
    hot path for feeds that don't carry a chart.

    Any parse or validation failure is logged at WARNING so a stored schema
    drift is observable without surfacing as a 500 to the caller.
    """
    if not raw:
        return None
    try:
        value = json.loads(raw)
    except (TypeError, ValueError):
        logger.warning("chart_spec column is not valid JSON")
        return None
    if not isinstance(value, dict):
        logger.warning("chart_spec column is not a JSON object")
        return None
    from lodestar.models import ChartSpec

    try:
        return ChartSpec(**value)
    except Exception:
        logger.warning("chart_spec column failed ChartSpec validation", exc_info=True)
        return None


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
    """Dismiss an insight card and feed the dismissal into the learning loop.

    Dismissal is a negative outcome signal: the detector's process was
    sound (it produced a well-formed card) but the customer did not find
    it useful. The reflection/lesson pipeline records this as a
    ``bad_luck`` quadrant and stores a dampening lesson so future
    detector runs for this customer reduce the frequency of cards with
    the same conditions.
    """
    from lodestar.learning.cohort import aggregate_to_cohort
    from lodestar.learning.interactions import (
        append_to_interaction,
        get_interaction_for_insight,
    )
    from lodestar.learning.journal import (
        cohort_key_for_customer,
        update_importance_post_outcome,
    )
    from lodestar.learning.reflection import (
        extract_and_store_lesson,
        has_reflection_for_interaction,
        run_reflection,
    )

    db = await get_db()
    try:
        await db.execute(
            "UPDATE insight_cards SET dismissed = 1 WHERE insight_id = ? AND customer_id = ?",
            (insight_id, body.customer_id),
        )
        cursor = await db.execute(
            """SELECT title, suggested_actions, priority_score
               FROM insight_cards WHERE insight_id = ? AND customer_id = ?""",
            (insight_id, body.customer_id),
        )
        row = await cursor.fetchone()
        await db.commit()
    finally:
        await db.close()

    # The detector agent runs as a background task after /demo/transaction
    # returns; an impatient dismiss can arrive before record_interaction
    # commits. Poll briefly so the reflection/lesson arc is not silently
    # skipped for fast demo clicks.
    interaction = None
    for _ in range(10):
        interaction = await get_interaction_for_insight(insight_id)
        if interaction:
            break
        await asyncio.sleep(0.25)
    if interaction is None:
        logger.warning(
            "dismiss for %s arrived before interaction row — learning arc skipped",
            insight_id,
        )
    await append_to_interaction(
        insight_id, {"role": "engagement", "content": "dismissed"}
    )

    if row and interaction:
        interaction_id = interaction["interaction_id"]
        already_reflected = await has_reflection_for_interaction(
            interaction_id, quadrant="bad_luck"
        )
        if not already_reflected:
            suggested = (row["suggested_actions"] or "").strip('"[]')
            trigger_type = suggested.split('"')[0] if suggested else "unknown"
            conditions = f"trigger={trigger_type}; card_title≈{row['title'][:60]}"
            reflection = await run_reflection(
                customer_id=body.customer_id,
                interaction_id=interaction_id,
                process_grade="A",
                outcome_quality="bad",
            )
            lesson = await extract_and_store_lesson(
                reflection,
                conditions=conditions,
                insight=(
                    "Customer dismissed this card. Reduce frequency or rephrase "
                    "future cards with the same trigger + merchant profile."
                ),
                confidence=0.75,
                importance=4.0,
                error_type="timing",
            )
            if lesson is not None:
                cohort_key = await cohort_key_for_customer(body.customer_id)
                if cohort_key:
                    await aggregate_to_cohort(
                        lesson_conditions=conditions,
                        lesson_insight=lesson.insight,
                        pattern_type=trigger_type,
                        category="engagement",
                        cohort_key=cohort_key,
                        confidence=lesson.confidence,
                    )

            # Close the loop on any lessons that were *applied* when the card
            # was produced — the dismissal says those lessons did not help.
            for lesson_id in _lessons_applied_from_interaction(interaction):
                await update_importance_post_outcome(lesson_id, helped=False)

    return {"status": "dismissed", "insight_id": insight_id}


# --- Drill-Down Chat ---

@app.post("/chat/{insight_id}")
async def chat_drill_down(insight_id: str, body: ChatRequest) -> ChatResponse:
    """Scoped conversational thread about a specific insight.

    A chat turn is a positive engagement signal — the customer found the
    card worth a follow-up question. We append to the interaction log and
    fire a ``earned_reward`` reflection so the learning pipeline stores
    a reinforcing lesson for this customer/trigger pattern.
    """
    from lodestar.agents.orchestrator import chat
    from lodestar.learning.cohort import aggregate_to_cohort
    from lodestar.learning.interactions import (
        append_to_interaction,
        get_interaction_for_insight,
    )
    from lodestar.learning.journal import (
        cohort_key_for_customer,
        update_importance_post_outcome,
    )
    from lodestar.learning.reflection import (
        extract_and_store_lesson,
        has_reflection_for_interaction,
        run_reflection,
    )

    try:
        messages = [ChatMessage(role="user", content=body.message, insight_id=insight_id)]
        response, user_message_i18n = await chat(
            messages,
            body.customer_id,
            body.insight_context,
            language=body.language,
        )
    except Exception as e:
        logger.exception("Chat error")
        raise HTTPException(
            status_code=502,
            detail=_system_error(body.language, e),
        ) from e

    # Append the Q+A to the interaction timeline. The stored entries carry
    # content_i18n so the history endpoint can replay bubbles with proper
    # language-toggle behaviour. Each locale value is capped at 800 chars
    # to bound the row size — the `messages` column is unbounded TEXT but
    # a runaway chat could still blow up the row. Empty-string locales are
    # dropped so the history replay never surfaces a blank bubble for a
    # locale that compliance silently stripped to "".
    def _capped(d: dict[str, str] | None) -> dict[str, str]:
        out: dict[str, str] = {}
        for k, v in (d or {}).items():
            if not isinstance(v, str):
                continue
            trimmed = v.strip()
            if not trimmed:
                continue
            out[k] = v[:800]
        return out

    assistant_content = (response.message.content or "")[:800]
    await append_to_interaction(
        insight_id,
        {
            "role": "user",
            "content": body.message[:800],
            "content_i18n": _capped(user_message_i18n) or None,
        },
    )
    await append_to_interaction(
        insight_id,
        {
            "role": "assistant",
            "content": assistant_content,
            "content_i18n": _capped(response.message.content_i18n) or None,
            # Persisting the tool call names on the assistant entry lets
            # the history endpoint reconstruct the visible tool chips on
            # replay — otherwise a returning visitor sees a clean bubble
            # with no trace of the agent's tool-calling loop.
            "tool_calls": list(response.tool_calls or []) or None,
        },
    )

    # First engagement (chat) is the earned_reward signal. Subsequent
    # turns on the same insight reinforce the conversation but must not
    # re-fire reflection — that would inflate the reflection count and
    # double-boost lesson confidence on every turn.
    interaction = None
    for _ in range(10):
        interaction = await get_interaction_for_insight(insight_id)
        if interaction:
            break
        await asyncio.sleep(0.25)
    if interaction is None:
        logger.warning(
            "chat for %s arrived before interaction row — learning arc skipped",
            insight_id,
        )
    if interaction:
        interaction_id = interaction["interaction_id"]
        already_reflected = await has_reflection_for_interaction(
            interaction_id, quadrant="earned_reward"
        )
        if not already_reflected:
            db = await get_db()
            try:
                cursor = await db.execute(
                    """SELECT title, suggested_actions FROM insight_cards
                       WHERE insight_id = ? AND customer_id = ?""",
                    (insight_id, body.customer_id),
                )
                row = await cursor.fetchone()
            finally:
                await db.close()

            if row:
                suggested = (row["suggested_actions"] or "").strip('"[]')
                trigger_type = suggested.split('"')[0] if suggested else "unknown"
                conditions = f"trigger={trigger_type}; card_title≈{row['title'][:60]}"
                reflection = await run_reflection(
                    customer_id=body.customer_id,
                    interaction_id=interaction_id,
                    process_grade="A",
                    outcome_quality="good",
                )
                lesson = await extract_and_store_lesson(
                    reflection,
                    conditions=conditions,
                    insight=(
                        "Customer engaged with this card via chat. Continue "
                        "surfacing cards with the same trigger + merchant profile."
                    ),
                    confidence=0.85,
                    importance=6.0,
                    error_type="missed_factor",
                )
                if lesson is not None:
                    cohort_key = await cohort_key_for_customer(body.customer_id)
                    if cohort_key:
                        await aggregate_to_cohort(
                            lesson_conditions=conditions,
                            lesson_insight=lesson.insight,
                            pattern_type=trigger_type,
                            category="engagement",
                            cohort_key=cohort_key,
                            confidence=lesson.confidence,
                        )

                # Close the loop on any lessons that fed this card via memory
                # injection — engagement confirms they helped, so bump them.
                for lesson_id in _lessons_applied_from_interaction(interaction):
                    await update_importance_post_outcome(lesson_id, helped=True)

    return response


@app.get("/chat/{insight_id}/history")
async def chat_history(insight_id: str) -> list[ChatMessage]:
    """Return the persisted user + assistant turns bound to an insight.

    Used by the drill-down chat to restore its message list on remount
    (navigating away and back would otherwise lose the thread, since the
    component's message array lives only in React local state). Each
    bubble carries ``content_i18n`` so a language toggle swaps the text
    without a round-trip. When an assistant turn was synthesised via
    tool calls, the stored ``tool_calls`` list is replayed as synthetic
    ``role="tool"`` chip entries placed immediately before the assistant
    bubble, preserving the live-session visual cue on history replay.
    Internal timeline entries (``event`` / ``agent_reasoning`` /
    ``card`` / ``engagement``) are hidden.
    """
    from lodestar.learning.interactions import get_interaction_for_insight

    interaction = await get_interaction_for_insight(insight_id)
    if interaction is None:
        return []

    out: list[ChatMessage] = []
    for msg in interaction.get("messages") or []:
        if not isinstance(msg, dict):
            continue
        role = msg.get("role")
        if role not in ("user", "assistant"):
            continue
        content_i18n = msg.get("content_i18n")
        if not isinstance(content_i18n, dict):
            content_i18n = None

        # Replay any tool chips that preceded this assistant bubble in
        # the live session. The chip's ``content`` holds the tool name;
        # the frontend renders it via the ``chat_tool_running`` i18n
        # template just like it does for live sends.
        if role == "assistant":
            for tool_name in msg.get("tool_calls") or []:
                if not isinstance(tool_name, str) or not tool_name:
                    continue
                out.append(
                    ChatMessage(
                        role="tool",
                        content=tool_name,
                        insight_id=insight_id,
                    )
                )

        out.append(
            ChatMessage(
                role=role,
                content=str(msg.get("content") or ""),
                content_i18n=content_i18n,
                insight_id=insight_id,
            )
        )
    return out


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
        response, _ = await chat(messages, body.customer_id, language=body.language)
        return response
    except Exception as e:
        logger.exception("Chat error")
        raise HTTPException(
            status_code=502,
            detail=_system_error(body.language, e),
        ) from e


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

    try:
        return await _simulate(
            customer_id=request.customer_id,
            scenario_type=request.scenario_type,
            parameters=request.parameters,
            language=request.language,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


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

    The catalogue carries all three locales upfront. The server returns
    every variant in each hit and additionally surfaces a ``name`` /
    ``description`` pair resolved to the requested ``language`` so clients
    that only render one locale can consume the response without client-
    side selection. When ``customer_id`` is provided, products whose
    ``min_income`` exceeds the customer's recorded monthly income are
    dropped from the result set.

    Args:
        query: Search query (Vietnamese, English, or Korean — bge-m3 is
            multilingual).
        customer_id: Optional customer for eligibility filtering.
        language: Display locale (vi | en | ko). Unknown codes fall back
            to Vietnamese.

    Returns:
        Ranked product list with all language fields populated and the
        name/description fields projected to the requested locale.
    """
    from lodestar.tools.products import search_products as _search

    lang = language if language in ("vi", "en", "ko") else "vi"
    hits = await _search(query)

    monthly_income: float | None = None
    if customer_id:
        db = await get_db()
        try:
            cursor = await db.execute(
                "SELECT income_monthly FROM customers WHERE customer_id = ?",
                (customer_id,),
            )
            row = await cursor.fetchone()
        finally:
            await db.close()
        if row and row["income_monthly"] is not None:
            monthly_income = float(row["income_monthly"])

    projected: list[ProductInfo] = []
    for p in hits:
        if (
            monthly_income is not None
            and p.min_income is not None
            and p.min_income > monthly_income
        ):
            continue
        localised_name = getattr(p, f"name_{lang}", "") or p.name_vi
        localised_desc = (
            getattr(p, f"description_{lang}", "") or p.description_vi
        )
        p.name = localised_name
        p.description = localised_desc
        projected.append(p)
    return projected


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
                chart_spec = _load_chart_spec(
                    r["chart_spec"] if "chart_spec" in r.keys() else None
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
                    "chart_spec": chart_spec.model_dump() if chart_spec else None,
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
    """Insert a synthetic transaction and hand it to the autonomous agent.

    The endpoint itself is fast: it writes the transaction row and fires
    `agents.detector.analyze_transaction` in the background. The agent
    decides — via an LLM tool-call loop over the rule sensors — whether
    the new transaction warrants a card, and composes the card in all
    three locales if so. Cards appear in the feed via SSE when the agent
    finishes reasoning (typically 3-15s depending on LLM backend).

    This is the agentic pipeline invoked by an explicit customer action.
    """
    from lodestar.agents.background import _store_insight
    from lodestar.agents.detector import analyze_transaction
    from lodestar.models import Transaction as _Tx

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

        # Re-fetch the customer's recent transaction window for the agent.
        start_date = (date.today() - timedelta(days=120)).isoformat()
        cursor = await db.execute(
            "SELECT * FROM transactions WHERE customer_id = ? AND date >= ? ORDER BY date",
            (body.customer_id, start_date),
        )
        tx_rows = await cursor.fetchall()
    finally:
        await db.close()

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
    new_tx = next(
        (t for t in transactions if t.transaction_id == transaction_id), transactions[-1]
    )

    async def _run_agent():
        from lodestar.learning.interactions import record_interaction

        try:
            results = await analyze_transaction(new_tx, transactions, body.customer_id)
            for result in results:
                await _store_insight(result.card)
                await record_interaction(
                    body.customer_id,
                    result.card.insight_id,
                    messages=[
                        {
                            "role": "event",
                            "content": (
                                f"Transaction {new_tx.transaction_id} at "
                                f"{new_tx.merchant} for {new_tx.amount:,.0f} VND "
                                f"({new_tx.category}) on {new_tx.date}"
                            ),
                        },
                        {
                            "role": "agent_reasoning",
                            "content": result.reasoning,
                            "tools_used": result.tools_used,
                            "lessons_applied": result.lessons_applied,
                        },
                        {
                            "role": "card",
                            "content": result.card.title,
                            "summary": result.card.summary,
                            "severity": result.card.severity,
                        },
                    ],
                )
                logger.info(
                    "Agent insight stored: %s for %s (%s) — tools=%s, lessons_applied=%d",
                    result.card.title,
                    body.customer_id,
                    result.card.insight_id,
                    result.tools_used,
                    len(result.lessons_applied),
                )
        except Exception:
            logger.exception("Detector agent failed for tx %s", transaction_id)

    asyncio.create_task(_run_agent())

    return {
        "transaction_id": transaction_id,
        "transaction": {
            "merchant": body.merchant,
            "amount": body.amount,
            "category": body.category,
            "entity": body.entity,
            "date": today,
        },
        # Frontend treats this as "a skeleton card might appear in the feed
        # within ~30s". SSE delivers the real card when the agent is done.
        "agent_pending": True,
    }


# (The old `_demo_event_caused_by` filter was removed when detection
#  moved to the LLM agent — context judgement is now the agent's job.)


@app.post("/demo/reset/{customer_id}")
async def reset_demo(customer_id: str) -> dict:
    """Return the demo to its post-boot "ready" state for one customer.

    Drops insight cards, injected demo transactions (``TX-DEMO-*``), savings
    goals, and the learning artefacts (lessons, reflections, interactions)
    accumulated across prior demo runs. The seeded baseline transaction
    history and the cohort_insights aggregate are preserved so the rule
    sensors still have a realistic pattern to reason against on the next
    simulation.
    """
    from lodestar.learning.journal import delete_lessons_for_customer
    from lodestar.learning.reflection import delete_reflections_for_customer

    # Order matters — interactions.insight_id FK references insight_cards,
    # so we have to drop the child rows (reflections + interactions) before
    # the insight_cards they point at.
    reflections_deleted = await delete_reflections_for_customer(customer_id)

    db = await get_db()
    try:
        cursor = await db.execute(
            "DELETE FROM insight_cards WHERE customer_id = ?", (customer_id,)
        )
        cards_deleted = cursor.rowcount
        cursor = await db.execute(
            "DELETE FROM transactions WHERE customer_id = ? AND transaction_id LIKE 'TX-DEMO-%'",
            (customer_id,),
        )
        tx_deleted = cursor.rowcount
        cursor = await db.execute(
            "DELETE FROM goals WHERE customer_id = ?", (customer_id,)
        )
        goals_deleted = cursor.rowcount
        await db.commit()
    finally:
        await db.close()

    lessons_deleted = await delete_lessons_for_customer(customer_id)

    logger.info(
        "Demo reset for %s — %d cards, %d demo tx, %d goals, %d lessons, %d reflections dropped",
        customer_id,
        cards_deleted,
        tx_deleted,
        goals_deleted,
        lessons_deleted,
        reflections_deleted,
    )
    return {
        "customer_id": customer_id,
        "cards_deleted": cards_deleted,
        "demo_transactions_deleted": tx_deleted,
        "goals_deleted": goals_deleted,
        "lessons_deleted": lessons_deleted,
        "reflections_deleted": reflections_deleted,
    }


@app.get("/memory/{customer_id}")
async def get_memory(customer_id: str) -> dict:
    """Expose the learning state the agent holds for one customer.

    Returns the stored lessons (evolved from prior reflections), the
    reflection history grouped by quadrant, and the cohort aggregates
    the customer's bucket participates in. Used for demo narration and
    operational inspection — not a user-facing endpoint.
    """
    from lodestar.learning.cohort import get_cohort_insights
    from lodestar.learning.journal import (
        cohort_key_for_customer,
        get_relevant_lessons,
    )
    from lodestar.learning.reflection import list_reflections_for_customer

    lessons = await get_relevant_lessons(customer_id, query="", top_k=50)
    reflections = await list_reflections_for_customer(customer_id)

    cohort_key = await cohort_key_for_customer(customer_id)
    cohort_rows: list = []
    if cohort_key:
        cohort_rows = [
            {
                "cohort_key": c.cohort_key,
                "pattern_type": c.pattern_type,
                "category": c.category,
                "insight": c.insight,
                "confidence": c.confidence,
                "supporting_count": c.supporting_count,
            }
            for c in await get_cohort_insights(cohort_key)
        ]

    return {
        "customer_id": customer_id,
        "cohort_key": cohort_key,
        "lessons": [
            {
                "lesson_id": L.lesson_id,
                "conditions": L.conditions,
                "insight": L.insight,
                "error_type": L.error_type,
                "confidence": L.confidence,
                "importance": L.importance,
                "times_evolved": L.times_evolved,
            }
            for L in lessons
        ],
        "reflections": reflections,
        "cohort_insights": cohort_rows,
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
            "customers": row[0] if row else 0,
        }
    finally:
        await db.close()
