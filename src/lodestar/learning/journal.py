"""Customer learning journal — store, retrieve, and evolve lessons.

Adapted from TojiMoola's TradingJournal pattern: per-customer lessons
are quality-gated, semantically deduplicated, and scored for retrieval.
"""

import json
import struct
import uuid
from datetime import datetime

import numpy as np

from lodestar.database import get_db
from lodestar.models import CustomerLesson
from lodestar.rag.embeddings import embed_texts

SIMILARITY_THRESHOLD = 0.85


def _pack_embedding(embedding: list[float]) -> bytes:
    """Pack a float list into bytes for SQLite BLOB storage.

    Args:
        embedding: List of floats.

    Returns:
        Packed bytes.
    """
    return struct.pack(f"{len(embedding)}f", *embedding)


def _unpack_embedding(data: bytes, dim: int = 1024) -> list[float]:
    """Unpack bytes back into a float list.

    Args:
        data: Packed bytes.
        dim: Expected embedding dimension.

    Returns:
        List of floats.
    """
    return list(struct.unpack(f"{dim}f", data))


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors.

    Args:
        a: First vector.
        b: Second vector.

    Returns:
        Cosine similarity score (0 to 1 for normalised vectors).
    """
    a_arr = np.array(a)
    b_arr = np.array(b)
    dot = np.dot(a_arr, b_arr)
    norm = np.linalg.norm(a_arr) * np.linalg.norm(b_arr)
    if norm == 0:
        return 0.0
    return float(dot / norm)


async def add_or_evolve_lesson(lesson: CustomerLesson) -> CustomerLesson:
    """Add a new lesson or merge with an existing similar one.

    If cosine similarity > SIMILARITY_THRESHOLD with an existing lesson,
    the lessons are merged (conditions combined, confidence boosted).
    Otherwise stored as new.

    Args:
        lesson: The lesson to add.

    Returns:
        The stored or evolved lesson.
    """
    embedding = embed_texts([f"{lesson.conditions} {lesson.insight}"])[0]
    packed = _pack_embedding(embedding)

    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT lesson_id, conditions, insight, confidence, importance, "
            "times_evolved, supporting_months, embedding FROM lessons WHERE customer_id = ?",
            (lesson.customer_id,),
        )
        existing = await cursor.fetchall()

        best_match = None
        best_sim = 0.0

        for row in existing:
            if row["embedding"]:
                existing_emb = _unpack_embedding(row["embedding"])
                sim = _cosine_similarity(embedding, existing_emb)
                if sim > best_sim:
                    best_sim = sim
                    best_match = row

        if best_match and best_sim >= SIMILARITY_THRESHOLD:
            merged_conditions = f"{best_match['conditions']}; {lesson.conditions}"
            merged_insight = f"{best_match['insight']}. {lesson.insight}"
            new_confidence = min(1.0, best_match["confidence"] + 0.1)
            new_evolved = best_match["times_evolved"] + 1

            existing_months = json.loads(best_match["supporting_months"] or "[]")
            merged_months = list(set(existing_months + lesson.supporting_months))

            merged_embedding = embed_texts([f"{merged_conditions} {merged_insight}"])[0]
            merged_packed = _pack_embedding(merged_embedding)

            await db.execute(
                """UPDATE lessons SET conditions = ?, insight = ?, confidence = ?,
                   times_evolved = ?, supporting_months = ?, embedding = ?
                   WHERE lesson_id = ?""",
                (
                    merged_conditions, merged_insight, new_confidence,
                    new_evolved, json.dumps(merged_months), merged_packed,
                    best_match["lesson_id"],
                ),
            )
            await db.commit()

            lesson.lesson_id = best_match["lesson_id"]
            lesson.conditions = merged_conditions
            lesson.insight = merged_insight
            lesson.confidence = new_confidence
            lesson.times_evolved = new_evolved
            return lesson

        lesson.lesson_id = lesson.lesson_id or f"L-{uuid.uuid4().hex[:8]}"
        lesson.embedding = packed

        await db.execute(
            """INSERT INTO lessons
               (lesson_id, customer_id, conditions, insight, error_type,
                confidence, importance, times_evolved, supporting_months, embedding)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                lesson.lesson_id, lesson.customer_id, lesson.conditions,
                lesson.insight, lesson.error_type, lesson.confidence,
                lesson.importance, lesson.times_evolved,
                json.dumps(lesson.supporting_months), packed,
            ),
        )
        await db.commit()
        return lesson

    finally:
        await db.close()


async def get_relevant_lessons(
    customer_id: str,
    query: str,
    top_k: int = 5,
) -> list[CustomerLesson]:
    """Retrieve lessons ranked by recency + importance + relevance.

    Args:
        customer_id: Customer identifier.
        query: Current context query for relevance scoring.
        top_k: Maximum number of lessons to return.

    Returns:
        Ranked list of relevant lessons.
    """
    query_embedding = embed_texts([query])[0]

    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM lessons WHERE customer_id = ?",
            (customer_id,),
        )
        rows = await cursor.fetchall()

        if not rows:
            return []

        scored = []
        now = datetime.utcnow()

        for row in rows:
            days_since = max(1, (now - datetime.fromisoformat(row["created_at"])).days)
            recency = 0.99 ** days_since

            importance = row["importance"] / 10.0

            relevance = 0.0
            if row["embedding"]:
                existing_emb = _unpack_embedding(row["embedding"])
                relevance = _cosine_similarity(query_embedding, existing_emb)

            score = recency + importance + relevance

            scored.append((score, row))

        scored.sort(key=lambda x: -x[0])

        lessons = []
        for _, row in scored[:top_k]:
            lessons.append(CustomerLesson(
                lesson_id=row["lesson_id"],
                customer_id=row["customer_id"],
                conditions=row["conditions"],
                insight=row["insight"],
                error_type=row["error_type"],
                confidence=row["confidence"],
                importance=row["importance"],
                times_evolved=row["times_evolved"],
                supporting_months=json.loads(row["supporting_months"] or "[]"),
            ))

        return lessons

    finally:
        await db.close()


async def update_importance_post_outcome(
    lesson_id: str, helped: bool
) -> None:
    """Adjust lesson importance based on whether it helped.

    Args:
        lesson_id: Lesson identifier.
        helped: True if the lesson contributed to a good outcome.
    """
    db = await get_db()
    try:
        delta = 0.5 if helped else -0.3
        await db.execute(
            "UPDATE lessons SET importance = MAX(1.0, MIN(10.0, importance + ?)) WHERE lesson_id = ?",
            (delta, lesson_id),
        )
        await db.commit()
    finally:
        await db.close()


def format_lessons_for_prompt(lessons: list[CustomerLesson]) -> str:
    """Render retrieved lessons as a compact block the detector can paste
    into its user message. Returns an empty string when the list is empty
    so the caller can safely prepend without a conditional.

    Args:
        lessons: Lessons returned by ``get_relevant_lessons``.

    Returns:
        Multi-line memory block or empty string.
    """
    if not lessons:
        return ""
    lines = ["Prior learnings about this customer (agent memory):"]
    for L in lessons:
        conf_pct = int(round(L.confidence * 100))
        if L.times_evolved:
            evolved = f", evolved {L.times_evolved}×"
        else:
            evolved = ""
        lines.append(
            f"- When {L.conditions} — {L.insight} "
            f"(confidence {conf_pct}%{evolved})"
        )
    return "\n".join(lines)


async def delete_lessons_for_customer(customer_id: str) -> int:
    """Drop all stored lessons for one customer. Used by the demo reset."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "DELETE FROM lessons WHERE customer_id = ?", (customer_id,)
        )
        count = cursor.rowcount
        await db.commit()
        return count
    finally:
        await db.close()


async def cohort_key_for_customer(customer_id: str) -> str | None:
    """Derive a non-PII cohort key from the customer profile.

    Format: ``{city}_{segment}`` lower-cased with spaces collapsed.
    Used by the cohort aggregator to bucket lessons across customers
    without exposing identifying details.
    """
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT city, segment FROM customers WHERE customer_id = ?",
            (customer_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        city = (row["city"] or "unknown").lower().replace(" ", "_")
        segment = (row["segment"] or "unknown").lower().replace(" ", "_")
        return f"{city}_{segment}"
    finally:
        await db.close()
