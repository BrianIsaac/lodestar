"""Background agent — polls transactions and generates insight cards.

Runs as an asyncio task alongside the FastAPI server. Triggers are
deterministic Python rules; the LLM is never involved for insight card
text — templates are authored in Vietnamese, English, and Korean and
rendered at write time so the feed toggle is a zero-cost lookup.
"""

import json
import logging
import uuid
from datetime import date, timedelta

from lodestar.agents.compliance import apply_compliance
from lodestar.agents.triggers import TriggerEvent, TriggerType, run_all_triggers
from lodestar.config import settings
from lodestar.database import get_db
from lodestar.models import InsightCard, InsightSeverity, Transaction

logger = logging.getLogger(__name__)

_ = settings  # reserved for future polling-interval use

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

# Card titles per trigger × language.
TITLE_TEMPLATES: dict[TriggerType, dict[str, str]] = {
    TriggerType.VELOCITY_ANOMALY: {
        "vi": "Chi tiêu bất thường",
        "en": "Unusual spending",
        "ko": "이상 지출",
    },
    TriggerType.RECURRING_CHANGE: {
        "vi": "Thay đổi định kỳ",
        "en": "Recurring charge changed",
        "ko": "정기 결제 변경",
    },
    TriggerType.PAYDAY_DETECTED: {
        "vi": "Đã nhận lương",
        "en": "Salary received",
        "ko": "급여 수령",
    },
    TriggerType.BUDGET_THRESHOLD: {
        "vi": "Vượt ngưỡng ngân sách",
        "en": "Budget threshold exceeded",
        "ko": "예산 한도 초과",
    },
    TriggerType.GOAL_MILESTONE: {
        "vi": "Cột mốc mục tiêu",
        "en": "Goal milestone",
        "ko": "목표 마일스톤",
    },
    TriggerType.LIFE_EVENT: {
        "vi": "Sự kiện cuộc sống",
        "en": "Life event",
        "ko": "라이프 이벤트",
    },
}

# Card summaries per trigger × language. Rendered with `.format(**context)`
# — each trigger rule populates `context` with the keys referenced here.
SUMMARY_TEMPLATES: dict[TriggerType, dict[str, str]] = {
    TriggerType.VELOCITY_ANOMALY: {
        "vi": "Chi tiêu cho {category} đang cao gấp {ratio:.1f} lần so với trung bình các tháng trước.",
        "en": "Spending on {category} is {ratio:.1f}× above the previous months' average.",
        "ko": "{category} 지출이 이전 달 평균의 {ratio:.1f}배 수준입니다.",
    },
    TriggerType.RECURRING_CHANGE: {
        "vi": "Giao dịch định kỳ tại {merchant} đã thay đổi {change_pct:+.0f}% so với mức trung bình.",
        "en": "Recurring charge at {merchant} changed by {change_pct:+.0f}% from the average.",
        "ko": "{merchant}의 정기 결제가 평균 대비 {change_pct:+.0f}% 변동되었습니다.",
    },
    TriggerType.PAYDAY_DETECTED: {
        "vi": "Đã nhận lương {amount:,.0f} VND vào tài khoản.",
        "en": "Salary of {amount:,.0f} VND received.",
        "ko": "급여 {amount:,.0f} VND 수령.",
    },
    TriggerType.BUDGET_THRESHOLD: {
        "vi": "Chi tiêu tháng này đang ở mức {pct:.0f}% thu nhập.",
        "en": "This month's spending is at {pct:.0f}% of income.",
        "ko": "이번 달 지출이 소득의 {pct:.0f}%에 달했습니다.",
    },
    TriggerType.LIFE_EVENT: {
        "vi": "Phát hiện dấu hiệu {event_label} qua {match_count} giao dịch gần đây.",
        "en": "Detected signs of {event_label} across {match_count} recent transactions.",
        "ko": "{match_count}건의 최근 거래에서 {event_label} 징후를 감지했습니다.",
    },
}

LIFE_EVENT_LABEL: dict[str, dict[str, str]] = {
    "baby": {
        "vi": "chuẩn bị đón em bé",
        "en": "preparing for a baby",
        "ko": "출산 준비",
    },
    "home_purchase": {
        "vi": "mua nhà",
        "en": "buying a home",
        "ko": "주택 구매",
    },
    "career_change": {
        "vi": "chuyển đổi công việc",
        "en": "changing careers",
        "ko": "경력 전환",
    },
}

LANGS = ("vi", "en", "ko")


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


def _prepare_context(event: TriggerEvent, language: str) -> dict:
    """Flatten the event context and inject derived + localised fields."""
    ctx = dict(event.context)
    if event.trigger_type == TriggerType.VELOCITY_ANOMALY and ctx.get("average"):
        ctx.setdefault("ratio", ctx["current"] / ctx["average"])
    if event.trigger_type == TriggerType.LIFE_EVENT:
        et = ctx.get("event_type", "")
        label_map = LIFE_EVENT_LABEL.get(et, {"vi": et, "en": et, "ko": et})
        ctx["event_label"] = label_map.get(language, et)
    return ctx


def _build_summary_i18n(event: TriggerEvent) -> dict[str, str]:
    """Produce a summary string per supported language using static
    templates. If a trigger type has no template, fall back to the
    Vietnamese text the rule put on the event."""
    templates = SUMMARY_TEMPLATES.get(event.trigger_type)
    if templates is None:
        return {lang: event.description for lang in LANGS}
    out: dict[str, str] = {}
    for lang in LANGS:
        try:
            out[lang] = templates[lang].format(**_prepare_context(event, lang))
        except Exception:
            logger.exception("Template render failed for %s/%s", event.trigger_type, lang)
            out[lang] = event.description
    return out


def _build_title_i18n(trigger_type: TriggerType) -> dict[str, str]:
    titles = TITLE_TEMPLATES.get(trigger_type)
    if titles is None:
        label = trigger_type.value.replace("_", " ").title()
        return {lang: label for lang in LANGS}
    return {lang: titles[lang] for lang in LANGS}


def _compose_insight_card(event: TriggerEvent) -> InsightCard:
    """Create an InsightCard from a trigger event, pre-localised for all
    supported languages so `/feed` can serve any locale without an LLM
    call.

    Args:
        event: The detected trigger event.

    Returns:
        InsightCard with title/summary populated in every locale.
    """
    title_i18n = _build_title_i18n(event.trigger_type)
    raw_summaries = _build_summary_i18n(event)

    summary_i18n: dict[str, str] = {}
    compliance_class = None
    for lang, raw in raw_summaries.items():
        filtered, cls = apply_compliance(raw, language=lang)
        summary_i18n[lang] = filtered
        if compliance_class is None:
            compliance_class = cls

    return InsightCard(
        insight_id=f"INS-{uuid.uuid4().hex[:8]}",
        customer_id=event.customer_id,
        title=title_i18n["vi"],
        summary=summary_i18n["vi"],
        title_i18n=title_i18n,
        summary_i18n=summary_i18n,
        severity=TRIGGER_TO_SEVERITY.get(event.trigger_type, InsightSeverity.INFO),
        compliance_class=compliance_class or InsightSeverity.INFO.value,  # type: ignore[arg-type]
        priority_score=event.severity,
        suggested_actions=[TRIGGER_TO_WORKFLOW.get(event.trigger_type, "spending_analysis")],
    )


async def _store_insight(card: InsightCard) -> None:
    """Persist an insight card to the database, including the per-locale
    title/summary JSON blobs so `/feed?language=X` is a pure SELECT.
    """
    db = await get_db()
    try:
        await db.execute(
            """INSERT OR IGNORE INTO insight_cards
               (insight_id, customer_id, title, summary,
                title_i18n, summary_i18n,
                severity, chart_spec, suggested_actions,
                compliance_class, priority_score)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                card.insight_id,
                card.customer_id,
                card.title,
                card.summary,
                json.dumps(card.title_i18n, ensure_ascii=False) if card.title_i18n else None,
                json.dumps(card.summary_i18n, ensure_ascii=False) if card.summary_i18n else None,
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


async def _is_duplicate(customer_id: str, trigger_type: TriggerType) -> bool:
    """Check if a similar insight was already generated recently. Dedup on
    the Vietnamese title since that is the canonical row value.

    Args:
        customer_id: Customer identifier.
        trigger_type: Trigger type enum.

    Returns:
        True if a similar insight exists from the last 24 hours.
    """
    title = TITLE_TEMPLATES.get(trigger_type, {}).get("vi") or trigger_type.value
    db = await get_db()
    try:
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        cursor = await db.execute(
            """SELECT COUNT(*) FROM insight_cards
               WHERE customer_id = ? AND title = ? AND created_at >= ? AND dismissed = 0""",
            (customer_id, title, yesterday),
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

    new_cards: list[InsightCard] = []

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
    import asyncio

    logger.info("Background agent started (interval: %ds)", settings.background_poll_interval)

    while True:
        try:
            cards = await run_background_cycle()
            if cards:
                logger.info("Generated %d new insight cards", len(cards))
        except Exception:
            logger.exception("Background agent error")

        await asyncio.sleep(settings.background_poll_interval)
