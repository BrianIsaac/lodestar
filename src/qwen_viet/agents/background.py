"""Background agent — polls transactions and generates insight cards.

Runs as an asyncio task alongside the FastAPI server. Triggers are
deterministic Python rules; the LLM is only used to compose the
insight card text (when available).
"""

import asyncio
import json
import logging
import uuid
from datetime import date, timedelta

from qwen_viet.agents.compliance import apply_compliance
from qwen_viet.agents.triggers import TriggerEvent, TriggerType, run_all_triggers
from qwen_viet.config import settings
from qwen_viet.database import get_db
from qwen_viet.models import InsightCard, InsightSeverity, Transaction

logger = logging.getLogger(__name__)

TRIGGER_TO_SEVERITY: dict[TriggerType, InsightSeverity] = {
    TriggerType.LIFE_EVENT: InsightSeverity.LIFE_EVENT,
    TriggerType.VELOCITY_ANOMALY: InsightSeverity.ANOMALY,
    TriggerType.BUDGET_THRESHOLD: InsightSeverity.ANOMALY,
    TriggerType.RECURRING_CHANGE: InsightSeverity.INFO,
    TriggerType.PAYDAY_DETECTED: InsightSeverity.INFO,
    TriggerType.GOAL_MILESTONE: InsightSeverity.MILESTONE,
}

TRIGGER_TO_WORKFLOW: dict[TriggerType, str] = {
    TriggerType.VELOCITY_ANOMALY: "spending_analysis",
    TriggerType.BUDGET_THRESHOLD: "spending_analysis",
    TriggerType.RECURRING_CHANGE: "spending_analysis",
    TriggerType.PAYDAY_DETECTED: "spending_analysis",
    TriggerType.LIFE_EVENT: "scenario_simulation",
    TriggerType.GOAL_MILESTONE: "goal_tracking",
}


async def _fetch_recent_transactions(customer_id: str, months: int = 4) -> list[Transaction]:
    """Fetch recent transactions for trigger evaluation.

    Args:
        customer_id: Customer identifier.
        months: Number of months to look back.

    Returns:
        List of transactions.
    """
    db = await get_db()
    try:
        start_date = (date.today() - timedelta(days=months * 30)).isoformat()
        cursor = await db.execute(
            "SELECT * FROM transactions WHERE customer_id = ? AND date >= ? ORDER BY date",
            (customer_id, start_date),
        )
        rows = await cursor.fetchall()
        return [
            Transaction(
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
            for r in rows
        ]
    finally:
        await db.close()


def _compose_insight_card(event: TriggerEvent) -> InsightCard:
    """Create an InsightCard from a trigger event.

    Args:
        event: The detected trigger event.

    Returns:
        InsightCard with compliance-filtered text.
    """
    text, compliance_class = apply_compliance(event.description)

    return InsightCard(
        insight_id=f"INS-{uuid.uuid4().hex[:8]}",
        customer_id=event.customer_id,
        title=event.trigger_type.value.replace("_", " ").title(),
        summary=text,
        severity=TRIGGER_TO_SEVERITY.get(event.trigger_type, InsightSeverity.INFO),
        compliance_class=compliance_class,
        priority_score=event.severity,
        suggested_actions=[TRIGGER_TO_WORKFLOW.get(event.trigger_type, "spending_analysis")],
    )


async def _store_insight(card: InsightCard) -> None:
    """Persist an insight card to the database.

    Args:
        card: InsightCard to store.
    """
    db = await get_db()
    try:
        await db.execute(
            """INSERT OR IGNORE INTO insight_cards
               (insight_id, customer_id, title, summary, severity,
                chart_spec, suggested_actions, compliance_class, priority_score)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                card.insight_id,
                card.customer_id,
                card.title,
                card.summary,
                card.severity,
                card.chart_spec.model_dump_json() if card.chart_spec else None,
                json.dumps(card.suggested_actions),
                card.compliance_class,
                card.priority_score,
            ),
        )
        await db.commit()
    finally:
        await db.close()


async def _is_duplicate(customer_id: str, trigger_type: str) -> bool:
    """Check if a similar insight was already generated recently.

    Args:
        customer_id: Customer identifier.
        trigger_type: Trigger type string.

    Returns:
        True if a similar insight exists from the last 24 hours.
    """
    db = await get_db()
    try:
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        cursor = await db.execute(
            """SELECT COUNT(*) FROM insight_cards
               WHERE customer_id = ? AND title = ? AND created_at >= ? AND dismissed = 0""",
            (customer_id, trigger_type.replace("_", " ").title(), yesterday),
        )
        row = await cursor.fetchone()
        return row[0] > 0
    finally:
        await db.close()


async def run_background_cycle() -> list[InsightCard]:
    """Run one cycle of the background agent for all customers.

    Returns:
        List of newly generated insight cards.
    """
    db = await get_db()
    try:
        cursor = await db.execute("SELECT customer_id FROM customers")
        customers = await cursor.fetchall()
    finally:
        await db.close()

    new_cards = []

    for cust in customers:
        customer_id = cust["customer_id"]
        transactions = await _fetch_recent_transactions(customer_id)

        if not transactions:
            continue

        events = run_all_triggers(transactions, customer_id)

        for event in events:
            if await _is_duplicate(customer_id, event.trigger_type):
                continue

            card = _compose_insight_card(event)
            await _store_insight(card)
            new_cards.append(card)
            logger.info("Generated insight: %s for %s", card.title, customer_id)

    return new_cards


async def background_loop() -> None:
    """Run the background agent continuously at the configured interval."""
    logger.info("Background agent started (interval: %ds)", settings.background_poll_interval)

    while True:
        try:
            cards = await run_background_cycle()
            if cards:
                logger.info("Generated %d new insight cards", len(cards))
        except Exception:
            logger.exception("Background agent error")

        await asyncio.sleep(settings.background_poll_interval)
