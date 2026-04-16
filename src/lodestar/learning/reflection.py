"""Reflection on interaction quality — Van Tharp process/outcome separation.

For the PoC, reflection uses rule-based heuristics rather than an LLM.
In production, the LLM would evaluate process quality more nuancedly.
"""

import uuid

from lodestar.database import get_db
from lodestar.learning.journal import add_or_evolve_lesson
from lodestar.models import CustomerLesson, CustomerReflection

QUADRANT_MAP = {
    ("good", "good"): "earned_reward",
    ("good", "bad"): "bad_luck",
    ("bad", "good"): "dumb_luck",
    ("bad", "bad"): "just_desserts",
}


async def run_reflection(
    customer_id: str,
    interaction_id: str,
    process_grade: str,
    outcome_quality: str,
) -> CustomerReflection:
    """Evaluate an interaction using the process/outcome matrix.

    Args:
        customer_id: Customer identifier.
        interaction_id: Interaction that generated the advice.
        process_grade: Grade of the analytical process (A-F).
        outcome_quality: Whether the outcome was good or bad.

    Returns:
        CustomerReflection with quadrant classification.
    """
    process_quality = "good" if process_grade.upper() in ("A", "B") else "bad"
    quadrant = QUADRANT_MAP.get((process_quality, outcome_quality), "just_desserts")

    reflection = CustomerReflection(
        reflection_id=f"R-{uuid.uuid4().hex[:8]}",
        customer_id=customer_id,
        interaction_id=interaction_id,
        process_grade=process_grade,
        outcome_quality=outcome_quality,
        quadrant=quadrant,
        lesson_extracted=False,
    )

    db = await get_db()
    try:
        await db.execute(
            """INSERT INTO reflections
               (reflection_id, customer_id, interaction_id, process_grade,
                outcome_quality, quadrant, lesson_extracted)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                reflection.reflection_id, customer_id, interaction_id,
                process_grade, outcome_quality, quadrant, 0,
            ),
        )
        await db.commit()
    finally:
        await db.close()

    return reflection


async def extract_and_store_lesson(
    reflection: CustomerReflection,
    conditions: str,
    insight: str,
    confidence: float,
    importance: float,
    error_type: str = "missed_factor",
) -> CustomerLesson | None:
    """Extract a lesson from a reflection if quality gate passes.

    Quality gate: process_grade must be A or B, AND confidence >= 0.70.
    This prevents storing lessons from lucky outcomes (dumb_luck quadrant).

    Args:
        reflection: The reflection to extract from.
        conditions: When this lesson applies.
        insight: What was learned.
        confidence: How generalisable the lesson is (0-1).
        importance: How important the lesson is (0-10).
        error_type: Type of error the lesson addresses.

    Returns:
        Stored CustomerLesson if quality gate passes, None otherwise.
    """
    good_process = reflection.process_grade.upper() in ("A", "B")
    high_confidence = confidence >= 0.70

    if not (good_process and high_confidence):
        return None

    lesson = CustomerLesson(
        lesson_id=f"L-{uuid.uuid4().hex[:8]}",
        customer_id=reflection.customer_id,
        conditions=conditions,
        insight=insight,
        error_type=error_type,
        confidence=confidence,
        importance=importance,
    )

    stored = await add_or_evolve_lesson(lesson)

    db = await get_db()
    try:
        await db.execute(
            "UPDATE reflections SET lesson_extracted = 1 WHERE reflection_id = ?",
            (reflection.reflection_id,),
        )
        await db.commit()
    finally:
        await db.close()

    return stored


async def delete_reflections_for_customer(customer_id: str) -> int:
    """Drop all reflections + owned interactions for one customer."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "DELETE FROM reflections WHERE customer_id = ?", (customer_id,)
        )
        refl_count = cursor.rowcount
        await db.execute(
            "DELETE FROM interactions WHERE customer_id = ?", (customer_id,)
        )
        await db.commit()
        return refl_count
    finally:
        await db.close()


async def list_reflections_for_customer(customer_id: str) -> list[dict]:
    """Return every reflection row for a customer, most recent first."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT reflection_id, interaction_id, process_grade,
                      outcome_quality, quadrant, lesson_extracted, created_at
               FROM reflections
               WHERE customer_id = ?
               ORDER BY created_at DESC""",
            (customer_id,),
        )
        rows = await cursor.fetchall()
        return [
            {
                "reflection_id": r["reflection_id"],
                "interaction_id": r["interaction_id"],
                "process_grade": r["process_grade"],
                "outcome_quality": r["outcome_quality"],
                "quadrant": r["quadrant"],
                "lesson_extracted": bool(r["lesson_extracted"]),
                "created_at": r["created_at"],
            }
            for r in rows
        ]
    finally:
        await db.close()
