"""Federated cohort insight aggregation — privacy-preserving cross-customer learning."""

from lodestar.config import settings
from lodestar.database import get_db
from lodestar.models import CohortInsight


def _min_customers() -> int:
    """Minimum distinct customers required before a cohort insight surfaces.

    Driven by ``settings.cohort_min_customers`` so a demo can lower the
    threshold without code edits.
    """
    return max(1, settings.cohort_min_customers)


async def aggregate_to_cohort(
    lesson_conditions: str,
    lesson_insight: str,
    pattern_type: str,
    category: str,
    cohort_key: str,
    confidence: float,
) -> CohortInsight | None:
    """Aggregate a lesson into a cohort insight (PII stripped).

    Only updates if the cohort has reached the minimum customer threshold.

    Args:
        lesson_conditions: Conditions from the lesson (PII already stripped).
        lesson_insight: Insight text (PII already stripped).
        pattern_type: Type of pattern.
        category: Spending/financial category.
        cohort_key: Demographic cohort key.
        confidence: Lesson confidence.

    Returns:
        Updated CohortInsight if threshold met, None otherwise.
    """
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM cohort_insights WHERE cohort_key = ? AND pattern_type = ?",
            (cohort_key, pattern_type),
        )
        existing = await cursor.fetchone()

        if existing:
            new_count = existing["supporting_count"] + 1
            new_confidence = (existing["confidence"] * existing["supporting_count"] + confidence) / new_count

            await db.execute(
                """UPDATE cohort_insights
                   SET supporting_count = ?, confidence = ?, insight = ?
                   WHERE cohort_key = ? AND pattern_type = ?""",
                (new_count, new_confidence, lesson_insight, cohort_key, pattern_type),
            )
            await db.commit()

            if new_count >= _min_customers():
                return CohortInsight(
                    cohort_key=cohort_key,
                    pattern_type=pattern_type,
                    category=category,
                    insight=lesson_insight,
                    confidence=new_confidence,
                    supporting_count=new_count,
                )
            return None
        else:
            await db.execute(
                """INSERT INTO cohort_insights
                   (cohort_key, pattern_type, category, insight, confidence, supporting_count)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (cohort_key, pattern_type, category, lesson_insight, confidence, 1),
            )
            await db.commit()
            return None

    finally:
        await db.close()


async def get_cohort_insights(cohort_key: str) -> list[CohortInsight]:
    """Retrieve active cohort insights for a demographic key.

    Args:
        cohort_key: Demographic cohort identifier.

    Returns:
        List of cohort insights that have reached the minimum threshold.
    """
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM cohort_insights WHERE cohort_key = ? AND supporting_count >= ?",
            (cohort_key, _min_customers()),
        )
        rows = await cursor.fetchall()
        return [
            CohortInsight(
                cohort_key=row["cohort_key"],
                pattern_type=row["pattern_type"],
                category=row["category"] or "",
                insight=row["insight"],
                confidence=row["confidence"],
                supporting_count=row["supporting_count"],
            )
            for row in rows
        ]
    finally:
        await db.close()
