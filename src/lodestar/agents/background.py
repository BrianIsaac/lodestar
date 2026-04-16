"""Persistence helper for insight cards produced by the detector agent.

Historically this module housed a deterministic "background loop" that
polled transactions, ran every rule, and rendered cards from hand-authored
Vi/En/Ko templates. That path has been retired — card generation now
flows through `agents.detector.analyze_transaction`, which uses the LLM
to decide *whether* to surface a card and to compose its text.

The only thing that survived is `_store_insight`: the detector still needs
a single place that knows how to serialise a fully-populated `InsightCard`
into the SQLite row layout the feed endpoint reads back.
"""

import json
import logging

from lodestar.database import get_db
from lodestar.models import InsightCard

logger = logging.getLogger(__name__)


async def _store_insight(card: InsightCard) -> None:
    """Persist an insight card to the database with all per-locale fields."""
    quick_prompts_dump = None
    if card.quick_prompts_i18n:
        quick_prompts_dump = json.dumps(
            {
                lang: [p.model_dump() for p in prompts]
                for lang, prompts in card.quick_prompts_i18n.items()
            },
            ensure_ascii=False,
        )

    db = await get_db()
    try:
        await db.execute(
            """INSERT OR IGNORE INTO insight_cards
               (insight_id, customer_id, title, summary,
                title_i18n, summary_i18n,
                action_hint_i18n, quick_prompts_i18n,
                severity, chart_spec, suggested_actions,
                compliance_class, priority_score)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                card.insight_id,
                card.customer_id,
                card.title,
                card.summary,
                json.dumps(card.title_i18n, ensure_ascii=False) if card.title_i18n else None,
                json.dumps(card.summary_i18n, ensure_ascii=False) if card.summary_i18n else None,
                json.dumps(card.action_hint_i18n, ensure_ascii=False) if card.action_hint_i18n else None,
                quick_prompts_dump,
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
