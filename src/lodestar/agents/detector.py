"""LodestarDetector — the agentic reasoning layer over transaction signals.

A new transaction arrives. Instead of any single deterministic rule
auto-firing a card, this agent runs an LLM tool-call loop:

1. The LLM sees the new transaction.
2. It decides which rule-checker tools to invoke (all 10 rules from
   `triggers.py` plus a few context helpers).
3. It reasons across the gathered evidence.
4. It either stays silent (no card in the feed) or emits a structured
   JSON card with title / summary / action hints / quick prompts in
   Vietnamese, English, and Korean — everything pre-rendered so the
   frontend's language toggle stays instant.

Rules exist only as tools. They are never the thing that creates a
card; only the agent is.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import date, timedelta
from typing import Any

from openai import AsyncOpenAI

from lodestar.agents.compliance import apply_compliance
from lodestar.agents.triggers import (
    TriggerEvent,
    TriggerType,
    check_budget_threshold,
    check_category_concentration,
    check_first_time_merchant,
    check_large_outflow,
    check_life_event_pattern,
    check_payday_detected,
    check_recurring_change,
    check_subscription_bloat,
    check_velocity_anomaly,
    check_weekend_spike,
)
from lodestar.config import settings
from lodestar.database import get_db
from lodestar.models import ComplianceClass, InsightCard, InsightSeverity, QuickPrompt, Transaction

logger = logging.getLogger(__name__)

# Max tool-call turns before we force the agent to produce a final answer.
MAX_TURNS = 4

# Per-call timeout for each LLM round-trip. Qwen3:14b on consumer GPUs can
# take 30-60s for the first tool-calling turn when the model isn't hot; DashScope
# qwen-plus responds in 2-5s. We bias for the slower local case.
LLM_TIMEOUT = 120


SYSTEM_PROMPT = """You are Lodestar — the autonomous financial coach inside Shinhan Bank Vietnam's SOL app.

A NEW transaction has just hit a customer's account. Your job: decide whether the transaction (in context of their recent history) is worth surfacing as a feed card. If yes, write the card. If nothing notable happened, stay silent.

You have sensor tools that can check specific patterns. Call whichever feel relevant — don't exhaustively run all of them; pick the ones that could reasonably be tripped by this transaction. Combine signals across 1-3 tool calls.

Guardrails:
- Only surface a card if the customer would genuinely want to know. Noise erodes trust.
- Never give imperative financial advice. Action hints must be phrased as "có thể cân nhắc" / "you could consider" / "고려할 만한 사항" — information and guidance only, never "you should".
- Keep titles under 6 words. Summaries under 2 sentences. Action hints: 2-3 bullets max.
- Do not invent transactions or numbers. Only reason from what the tools and the transaction data show you.

Output format (plain JSON, no markdown fences, no preamble):

If no card is warranted:
{"emit_card": false, "reasoning": "<one-sentence reason for staying silent>"}

If a card is warranted:
{
  "emit_card": true,
  "reasoning": "<your internal reasoning chain, 1-3 sentences>",
  "severity": "life_event" | "anomaly" | "milestone" | "info" | "product",
  "trigger_type": "<one of the trigger type names: velocity_anomaly, recurring_change, payday_detected, budget_threshold, life_event, large_outflow, first_time_merchant, category_concentration, subscription_bloat, weekend_spike, goal_milestone>",
  "priority_score": <float 0.0-1.0>,
  "title_i18n": {"vi": "...", "en": "...", "ko": "..."},
  "summary_i18n": {"vi": "...", "en": "...", "ko": "..."},
  "action_hint_i18n": {
    "vi": ["...", "...", "..."],
    "en": ["...", "...", "..."],
    "ko": ["...", "...", "..."]
  },
  "quick_prompts_i18n": {
    "vi": [
      {"text": "<cross-tab chip, typically action=plan or products>", "action": "plan"|"products"|"chat", "params": {}},
      {"text": "<chat chip>", "action": "chat"},
      {"text": "<chat chip>", "action": "chat"}
    ],
    "en": [...same shape...],
    "ko": [...same shape...]
  }
}

Quick-prompt actions:
- "chat" — prompt is sent as a question into the drill-down chat. Default.
- "plan" — jumps to the Plan tab with a goal form pre-filled. Use params: {"name": "<goal name>", "target_amount": <int VND>, "months": <int>}.
- "products" — jumps to Products tab with a search pre-filled. Use params: {"query": "<search phrase>"}.

Always produce three chips per language. The first one should be the strongest actionable suggestion (often a "plan" or "products" cross-link if relevant); the others are chat prompts the customer might tap.

Now reason carefully and call tools as needed before producing your JSON."""


def _build_tool_definitions() -> list[dict]:
    """OpenAI function-calling schemas for each sensor + context helper.

    The schemas are deliberately parameter-free (or optionally keyed)
    because the customer_id and transaction window are bound by the
    executor closure — the agent shouldn't have to pass them."""
    return [
        {
            "type": "function",
            "function": {
                "name": "check_velocity_anomaly",
                "description": "Check whether current-month spending in any category is ≥3× the prior-months average. Returns the anomaly details or null.",
                "parameters": {"type": "object", "properties": {}},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "check_recurring_change",
                "description": "Check whether a recurring merchant charge has drifted >20% from its average. Returns the merchant + change percentage or null.",
                "parameters": {"type": "object", "properties": {}},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "check_payday_detected",
                "description": "Check whether a salary credit was received in the last 3 days.",
                "parameters": {"type": "object", "properties": {}},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "check_budget_threshold",
                "description": "Check whether current-month spending has exceeded 80% of the most recent monthly salary.",
                "parameters": {"type": "object", "properties": {}},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "check_life_event_pattern",
                "description": "Scan recent merchants for baby / home-purchase / career-change keyword clusters. Returns event type and match count if detected.",
                "parameters": {"type": "object", "properties": {}},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "check_large_outflow",
                "description": "Check whether any recent single outflow exceeds 15% of monthly income.",
                "parameters": {"type": "object", "properties": {}},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "check_first_time_merchant",
                "description": "Check whether the most recent transaction is at a merchant never seen before in the window. Weak-but-useful novelty signal.",
                "parameters": {"type": "object", "properties": {}},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "check_category_concentration",
                "description": "Check whether one category has dominated (>50%) the last 7 days of spending.",
                "parameters": {"type": "object", "properties": {}},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "check_subscription_bloat",
                "description": "Count recurring small charges (<500K VND) to flag subscription accumulation.",
                "parameters": {"type": "object", "properties": {}},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "check_weekend_spike",
                "description": "Check whether any category's weekend spending is ≥2× its weekday average.",
                "parameters": {"type": "object", "properties": {}},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_recent_transactions_summary",
                "description": "Return a compact summary of the customer's recent spending patterns (last 30 days): totals per category, top merchants, month-over-month change.",
                "parameters": {"type": "object", "properties": {}},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_customer_profile",
                "description": "Return the customer's profile (name, age band, income segment, existing savings goals).",
                "parameters": {"type": "object", "properties": {}},
            },
        },
    ]


def _trigger_event_to_dict(event: TriggerEvent | None) -> dict | None:
    if event is None:
        return None
    return {
        "trigger_type": event.trigger_type.value,
        "severity": event.severity,
        "context": event.context,
        "description": event.description,
    }


async def _get_recent_summary(customer_id: str, transactions: list[Transaction]) -> dict:
    """Compact transaction summary a reasoning LLM can skim quickly."""
    if not transactions:
        return {"note": "No transactions in window."}

    cutoff = date.today() - timedelta(days=30)
    window = [
        t
        for t in transactions
        if (t.date if isinstance(t.date, date) else date.fromisoformat(str(t.date))) >= cutoff
    ]
    by_cat: dict[str, float] = {}
    by_merchant: dict[str, int] = {}
    for t in window:
        if t.amount >= 0:
            continue
        by_cat[t.category or "other"] = by_cat.get(t.category or "other", 0) + abs(t.amount)
        if t.merchant:
            by_merchant[t.merchant] = by_merchant.get(t.merchant, 0) + 1

    top_cats = sorted(by_cat.items(), key=lambda kv: -kv[1])[:5]
    top_merchants = sorted(by_merchant.items(), key=lambda kv: -kv[1])[:5]
    total_out = sum(by_cat.values())
    salaries = [t.amount for t in window if t.category == "salary" and t.amount > 0]

    return {
        "window_days": 30,
        "total_outflow": round(total_out),
        "salary_credits": [round(s) for s in salaries],
        "top_categories": [
            {"category": c, "amount": round(a)} for c, a in top_cats
        ],
        "top_merchants": [
            {"merchant": m, "visits": n} for m, n in top_merchants
        ],
    }


async def _get_customer_profile(customer_id: str) -> dict:
    """Pull customer name, segment, and active goals from the DB."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT full_name, segment, income_monthly, language FROM customers WHERE customer_id = ?",
            (customer_id,),
        )
        row = await cursor.fetchone()
        profile: dict[str, Any] = (
            {
                "full_name": row["full_name"],
                "segment": row["segment"],
                "income_monthly": row["income_monthly"],
                "language_preference": row["language"],
            }
            if row
            else {}
        )

        cursor = await db.execute(
            "SELECT name, target_amount, current_amount, target_date FROM goals WHERE customer_id = ? LIMIT 5",
            (customer_id,),
        )
        goal_rows = await cursor.fetchall()
        profile["active_goals"] = [
            {
                "name": g["name"],
                "target_amount": g["target_amount"],
                "current_amount": g["current_amount"],
                "target_date": g["target_date"],
            }
            for g in goal_rows
        ]
        return profile
    finally:
        await db.close()


async def _execute_tool(
    name: str,
    arguments: dict,
    customer_id: str,
    transactions: list[Transaction],
) -> str:
    """Dispatcher the agent hits on every tool call. Returns a JSON string."""
    try:
        if name == "check_velocity_anomaly":
            return json.dumps(
                _trigger_event_to_dict(check_velocity_anomaly(transactions, customer_id)),
                ensure_ascii=False,
            )
        if name == "check_recurring_change":
            return json.dumps(
                _trigger_event_to_dict(check_recurring_change(transactions, customer_id)),
                ensure_ascii=False,
            )
        if name == "check_payday_detected":
            return json.dumps(
                _trigger_event_to_dict(check_payday_detected(transactions, customer_id)),
                ensure_ascii=False,
            )
        if name == "check_budget_threshold":
            return json.dumps(
                _trigger_event_to_dict(check_budget_threshold(transactions, customer_id)),
                ensure_ascii=False,
            )
        if name == "check_life_event_pattern":
            return json.dumps(
                _trigger_event_to_dict(check_life_event_pattern(transactions, customer_id)),
                ensure_ascii=False,
            )
        if name == "check_large_outflow":
            return json.dumps(
                _trigger_event_to_dict(check_large_outflow(transactions, customer_id)),
                ensure_ascii=False,
            )
        if name == "check_first_time_merchant":
            return json.dumps(
                _trigger_event_to_dict(check_first_time_merchant(transactions, customer_id)),
                ensure_ascii=False,
            )
        if name == "check_category_concentration":
            return json.dumps(
                _trigger_event_to_dict(check_category_concentration(transactions, customer_id)),
                ensure_ascii=False,
            )
        if name == "check_subscription_bloat":
            return json.dumps(
                _trigger_event_to_dict(check_subscription_bloat(transactions, customer_id)),
                ensure_ascii=False,
            )
        if name == "check_weekend_spike":
            return json.dumps(
                _trigger_event_to_dict(check_weekend_spike(transactions, customer_id)),
                ensure_ascii=False,
            )
        if name == "get_recent_transactions_summary":
            return json.dumps(
                await _get_recent_summary(customer_id, transactions), ensure_ascii=False
            )
        if name == "get_customer_profile":
            return json.dumps(await _get_customer_profile(customer_id), ensure_ascii=False)
        return json.dumps({"error": f"Unknown tool: {name}"})
    except Exception as exc:
        logger.exception("Detector tool %s failed", name)
        return json.dumps({"error": f"{type(exc).__name__}: {exc}"})


def _client() -> AsyncOpenAI:
    return AsyncOpenAI(base_url=settings.llm_base_url, api_key=settings.llm_api_key)


def _valid_trigger_type(name: str) -> TriggerType:
    try:
        return TriggerType(name)
    except ValueError:
        return TriggerType.VELOCITY_ANOMALY


def _valid_severity(name: str) -> InsightSeverity:
    try:
        return InsightSeverity(name)
    except ValueError:
        return InsightSeverity.INFO


def _coerce_card(
    payload: dict, customer_id: str
) -> InsightCard | None:
    """Validate + shape the LLM JSON into an InsightCard. Returns None if
    the agent decided not to emit."""
    if not payload.get("emit_card"):
        return None

    title_i18n = payload.get("title_i18n") or {}
    summary_i18n = payload.get("summary_i18n") or {}
    if not isinstance(title_i18n, dict) or not isinstance(summary_i18n, dict):
        return None
    if not title_i18n.get("vi") or not summary_i18n.get("vi"):
        return None

    action_hint_raw = payload.get("action_hint_i18n") or {}
    action_hint_i18n: dict[str, list[str]] = {}
    if isinstance(action_hint_raw, dict):
        for lang, hints in action_hint_raw.items():
            if isinstance(hints, list):
                action_hint_i18n[lang] = [str(h) for h in hints if isinstance(h, str)]

    quick_prompts_raw = payload.get("quick_prompts_i18n") or {}
    quick_prompts_i18n: dict[str, list[QuickPrompt]] = {}
    if isinstance(quick_prompts_raw, dict):
        for lang, prompts in quick_prompts_raw.items():
            if not isinstance(prompts, list):
                continue
            cleaned: list[QuickPrompt] = []
            for p in prompts:
                if not isinstance(p, dict) or "text" not in p:
                    continue
                action = p.get("action") or "chat"
                if action not in ("chat", "plan", "products"):
                    action = "chat"
                cleaned.append(
                    QuickPrompt(
                        text=str(p["text"]),
                        action=action,
                        params=p.get("params") if isinstance(p.get("params"), dict) else {},
                    )
                )
            if cleaned:
                quick_prompts_i18n[lang] = cleaned

    # Apply compliance per locale so guidance text gets the disclaimer.
    filtered_summary: dict[str, str] = {}
    compliance_class: ComplianceClass | None = None
    for lang, text in summary_i18n.items():
        if not isinstance(text, str):
            continue
        filtered, cls = apply_compliance(text, language=lang if lang in ("vi", "en", "ko") else "vi")
        filtered_summary[lang] = filtered
        if compliance_class is None:
            compliance_class = cls

    import uuid
    return InsightCard(
        insight_id=f"INS-{uuid.uuid4().hex[:8]}",
        customer_id=customer_id,
        title=title_i18n.get("vi") or title_i18n.get("en") or "",
        summary=filtered_summary.get("vi") or filtered_summary.get("en") or "",
        title_i18n=title_i18n,
        summary_i18n=filtered_summary or summary_i18n,
        action_hint_i18n=action_hint_i18n or None,
        quick_prompts_i18n=quick_prompts_i18n or None,
        severity=_valid_severity(payload.get("severity") or "info"),
        compliance_class=compliance_class or ComplianceClass.INFORMATION,
        priority_score=float(payload.get("priority_score", 0.5) or 0.5),
        suggested_actions=[payload.get("trigger_type") or _valid_trigger_type("").value],
    )


async def analyze_transaction(
    new_transaction: Transaction,
    transactions: list[Transaction],
    customer_id: str,
) -> list[InsightCard]:
    """Run the agent loop for a newly-injected transaction.

    Args:
        new_transaction: The transaction that just hit the account.
        transactions: Recent window (last 120 days) including the new one.
        customer_id: Customer identifier.

    Returns:
        List of InsightCards the agent decided to emit. Empty if the
        agent stayed silent (that's the intended behaviour when nothing
        meaningful happened — a coffee purchase shouldn't produce a card).
    """
    client = _client()
    tools = _build_tool_definitions()

    user_msg = (
        f"New transaction: merchant={new_transaction.merchant}, "
        f"amount={new_transaction.amount:,.0f} VND, "
        f"category={new_transaction.category}, "
        f"date={new_transaction.date}. "
        f"Use the sensor tools as needed, then produce the final JSON per the schema "
        f"in the system prompt. Keep each language concise so the response fits in the token budget. "
        f"/no_think"
    )

    messages: list[dict] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_msg},
    ]

    for turn in range(MAX_TURNS):
        is_final_turn = turn == MAX_TURNS - 1
        try:
            kwargs: dict[str, Any] = {
                "model": settings.llm_model,
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 4096,
            }
            if not is_final_turn:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"
            else:
                # Force JSON output on the last turn so the parser doesn't
                # have to wrestle with free-form prose.
                kwargs["response_format"] = {"type": "json_object"}
            response = await asyncio.wait_for(
                client.chat.completions.create(**kwargs),
                timeout=LLM_TIMEOUT,
            )
        except asyncio.TimeoutError:
            logger.warning("Detector LLM timeout at turn %d", turn)
            return []
        except Exception:
            logger.exception("Detector LLM error at turn %d", turn)
            return []

        choice = response.choices[0].message
        tool_calls = choice.tool_calls or []

        if tool_calls:
            messages.append(choice.model_dump())
            for tc in tool_calls:
                fn = tc.function
                try:
                    args = json.loads(fn.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                result = await _execute_tool(fn.name, args, customer_id, transactions)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result,
                    }
                )
            continue

        # No tool call — treat as final JSON output.
        text = (choice.content or "").strip()
        # Strip any leaked thinking tags Qwen3 may emit.
        if "</think>" in text:
            text = text.split("</think>", 1)[1].strip()
        # Strip markdown fences if the model wrapped the JSON.
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text
            if text.endswith("```"):
                text = text.rsplit("```", 1)[0]
            text = text.strip()
            if text.lower().startswith("json"):
                text = text[4:].strip()

        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            logger.warning(
                "Detector produced non-JSON final output (%d chars): %s",
                len(text),
                text[:1000],
            )
            return []

        card = _coerce_card(payload, customer_id)
        if card is None:
            logger.info(
                "Detector stayed silent for tx at %s: %s",
                new_transaction.merchant,
                payload.get("reasoning"),
            )
            return []

        logger.info(
            "Detector emitted card '%s' for tx at %s",
            card.title,
            new_transaction.merchant,
        )
        return [card]

    logger.warning("Detector exceeded MAX_TURNS without final output")
    return []
