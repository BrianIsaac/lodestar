"""Interaction ledger — binds a detector-produced card to the event that
triggered it, and to every downstream customer engagement (chat, dismiss).

Each row in `interactions` holds a JSON `messages` timeline for one insight.
The reflection/lesson pipeline reads that timeline to grade process and
outcome so the learning loop can evolve.
"""

import json
import uuid

from lodestar.database import get_db


async def record_interaction(
    customer_id: str,
    insight_id: str,
    messages: list[dict],
) -> str:
    """Create a new interaction row for a freshly-emitted insight card.

    Args:
        customer_id: Customer the card was produced for.
        insight_id: The card's id, used as the foreign key.
        messages: Initial timeline (event + agent reasoning + card summary).

    Returns:
        The generated interaction_id.
    """
    interaction_id = f"I-{uuid.uuid4().hex[:8]}"
    db = await get_db()
    try:
        await db.execute(
            """INSERT INTO interactions (interaction_id, customer_id, insight_id, messages)
               VALUES (?, ?, ?, ?)""",
            (
                interaction_id,
                customer_id,
                insight_id,
                json.dumps(messages, ensure_ascii=False),
            ),
        )
        await db.commit()
    finally:
        await db.close()
    return interaction_id


async def append_to_interaction(insight_id: str, message: dict) -> str | None:
    """Append a single timeline entry to the interaction bound to an insight.

    Args:
        insight_id: The card being discussed.
        message: One entry, e.g. {"role": "user", "content": "..."}.

    Returns:
        The interaction_id that was updated, or None if no interaction
        existed yet (shouldn't happen in the normal flow).
    """
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT interaction_id, messages FROM interactions WHERE insight_id = ? ORDER BY created_at LIMIT 1",
            (insight_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        existing = json.loads(row["messages"] or "[]")
        existing.append(message)
        await db.execute(
            "UPDATE interactions SET messages = ? WHERE interaction_id = ?",
            (json.dumps(existing, ensure_ascii=False), row["interaction_id"]),
        )
        await db.commit()
        return row["interaction_id"]
    finally:
        await db.close()


async def get_interaction_for_insight(insight_id: str) -> dict | None:
    """Return the interaction row bound to an insight, or None.

    A corrupt ``messages`` JSON column is treated as an empty timeline
    rather than raising: callers generally use the messages for demo
    narration or history replay, neither of which should 500 because
    one row on disk was hand-edited or partially written.
    """
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM interactions WHERE insight_id = ? ORDER BY created_at LIMIT 1",
            (insight_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        raw = row["messages"] or "[]"
        try:
            messages = json.loads(raw)
        except json.JSONDecodeError:
            messages = []
        if not isinstance(messages, list):
            messages = []
        return {
            "interaction_id": row["interaction_id"],
            "customer_id": row["customer_id"],
            "insight_id": row["insight_id"],
            "messages": messages,
            "created_at": row["created_at"],
        }
    finally:
        await db.close()
