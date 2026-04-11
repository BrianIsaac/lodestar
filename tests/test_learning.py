"""Tests for the learning loop — journal, reflection, cohort."""

import pytest

from qwen_viet.database import get_db
from qwen_viet.models import CustomerLesson


@pytest.fixture(autouse=True)
async def clean_learning_tables():
    """Clear learning-related tables before each test."""
    db = await get_db()
    await db.execute("DELETE FROM lessons")
    await db.execute("DELETE FROM reflections")
    await db.execute("DELETE FROM cohort_insights")
    await db.commit()
    await db.close()
    yield


class TestJournal:
    """Test customer learning journal CRUD and deduplication."""

    async def test_add_new_lesson(self) -> None:
        from qwen_viet.learning.journal import add_or_evolve_lesson

        lesson = CustomerLesson(
            lesson_id="L-test-001",
            customer_id="C001",
            conditions="Weekend dining in holiday months",
            insight="Customer overspends on food Fri-Sun by 40%",
            confidence=0.85,
            importance=7.0,
        )

        stored = await add_or_evolve_lesson(lesson)
        assert stored.lesson_id == "L-test-001"
        assert stored.times_evolved == 0

    async def test_retrieve_lessons(self) -> None:
        from qwen_viet.learning.journal import add_or_evolve_lesson, get_relevant_lessons

        await add_or_evolve_lesson(CustomerLesson(
            lesson_id="L-ret-001",
            customer_id="C001",
            conditions="Holiday spending pattern",
            insight="Food spending spikes during Tet",
            confidence=0.80,
            importance=8.0,
        ))

        lessons = await get_relevant_lessons("C001", "food spending analysis")
        assert len(lessons) >= 1
        assert any("food" in l.insight.lower() or "Tet" in l.insight for l in lessons)

    async def test_semantic_dedup_merges_similar(self) -> None:
        from qwen_viet.learning.journal import add_or_evolve_lesson

        lesson1 = CustomerLesson(
            lesson_id="L-dup-001",
            customer_id="C001",
            conditions="Weekend food overspending",
            insight="Customer spends 40% more on food during weekends",
            confidence=0.80,
            importance=6.0,
        )
        await add_or_evolve_lesson(lesson1)

        lesson2 = CustomerLesson(
            lesson_id="L-dup-002",
            customer_id="C001",
            conditions="Weekend dining overspend pattern",
            insight="Customer overspends on dining every weekend by 35-45%",
            confidence=0.82,
            importance=6.5,
        )
        result = await add_or_evolve_lesson(lesson2)

        assert result.times_evolved >= 1
        assert result.confidence >= 0.85

        db = await get_db()
        cursor = await db.execute("SELECT COUNT(*) FROM lessons WHERE customer_id = 'C001'")
        row = await cursor.fetchone()
        await db.close()
        assert row[0] == 1, f"Expected 1 merged lesson, got {row[0]}"

    async def test_importance_boost(self) -> None:
        from qwen_viet.learning.journal import add_or_evolve_lesson, update_importance_post_outcome

        lesson = CustomerLesson(
            lesson_id="L-imp-001",
            customer_id="C001",
            conditions="Test",
            insight="Test lesson for importance",
            importance=5.0,
        )
        await add_or_evolve_lesson(lesson)

        await update_importance_post_outcome("L-imp-001", helped=True)
        db = await get_db()
        cursor = await db.execute("SELECT importance FROM lessons WHERE lesson_id = 'L-imp-001'")
        row = await cursor.fetchone()
        await db.close()
        assert row["importance"] == 5.5

    async def test_importance_decay(self) -> None:
        from qwen_viet.learning.journal import add_or_evolve_lesson, update_importance_post_outcome

        lesson = CustomerLesson(
            lesson_id="L-dec-001",
            customer_id="C001",
            conditions="Test",
            insight="Test lesson for decay",
            importance=5.0,
        )
        await add_or_evolve_lesson(lesson)

        await update_importance_post_outcome("L-dec-001", helped=False)
        db = await get_db()
        cursor = await db.execute("SELECT importance FROM lessons WHERE lesson_id = 'L-dec-001'")
        row = await cursor.fetchone()
        await db.close()
        assert row["importance"] == 4.7


class TestReflection:
    """Test process/outcome separation and quality gating."""

    async def test_earned_reward_quadrant(self) -> None:
        from qwen_viet.learning.reflection import run_reflection

        reflection = await run_reflection(
            customer_id="C001",
            interaction_id="INT-001",
            process_grade="A",
            outcome_quality="good",
        )
        assert reflection.quadrant == "earned_reward"

    async def test_dumb_luck_quadrant(self) -> None:
        from qwen_viet.learning.reflection import run_reflection

        reflection = await run_reflection(
            customer_id="C001",
            interaction_id="INT-002",
            process_grade="D",
            outcome_quality="good",
        )
        assert reflection.quadrant == "dumb_luck"

    async def test_quality_gate_passes(self) -> None:
        from qwen_viet.learning.reflection import extract_and_store_lesson, run_reflection

        reflection = await run_reflection("C001", "INT-003", "A", "good")
        lesson = await extract_and_store_lesson(
            reflection,
            conditions="Good process test",
            insight="This lesson should be stored",
            confidence=0.85,
            importance=7.0,
        )
        assert lesson is not None
        assert lesson.lesson_id.startswith("L-")

    async def test_quality_gate_blocks_low_confidence(self) -> None:
        from qwen_viet.learning.reflection import extract_and_store_lesson, run_reflection

        reflection = await run_reflection("C001", "INT-004", "A", "good")
        lesson = await extract_and_store_lesson(
            reflection,
            conditions="Low confidence test",
            insight="This should be blocked",
            confidence=0.50,
            importance=7.0,
        )
        assert lesson is None

    async def test_quality_gate_blocks_bad_process(self) -> None:
        from qwen_viet.learning.reflection import extract_and_store_lesson, run_reflection

        reflection = await run_reflection("C001", "INT-005", "D", "good")
        lesson = await extract_and_store_lesson(
            reflection,
            conditions="Bad process test",
            insight="This should be blocked (dumb luck)",
            confidence=0.90,
            importance=8.0,
        )
        assert lesson is None


class TestCohort:
    """Test federated cohort insight aggregation."""

    async def test_aggregate_below_threshold(self) -> None:
        from qwen_viet.learning.cohort import aggregate_to_cohort

        result = await aggregate_to_cohort(
            lesson_conditions="Holiday spending",
            lesson_insight="Overspend during Tet",
            pattern_type="seasonal_overspend",
            category="food",
            cohort_key="hanoi_young_pro",
            confidence=0.80,
        )
        assert result is None

    async def test_aggregate_reaches_threshold(self) -> None:
        from qwen_viet.learning.cohort import aggregate_to_cohort

        for i in range(5):
            result = await aggregate_to_cohort(
                lesson_conditions=f"Pattern from customer {i}",
                lesson_insight="Overspend on dining during holidays",
                pattern_type="holiday_dining",
                category="food",
                cohort_key="hcmc_mid_income",
                confidence=0.75 + i * 0.02,
            )

        assert result is not None
        assert result.supporting_count == 5
        assert result.cohort_key == "hcmc_mid_income"

    async def test_get_cohort_insights(self) -> None:
        from qwen_viet.learning.cohort import aggregate_to_cohort, get_cohort_insights

        for i in range(6):
            await aggregate_to_cohort(
                lesson_conditions=f"Pattern {i}",
                lesson_insight="Transport spending rises in rain season",
                pattern_type="seasonal_transport",
                category="transport",
                cohort_key="danang_mass",
                confidence=0.80,
            )

        insights = await get_cohort_insights("danang_mass")
        assert len(insights) >= 1
        assert insights[0].pattern_type == "seasonal_transport"

    async def test_cohort_strips_customer_id(self) -> None:
        from qwen_viet.learning.cohort import aggregate_to_cohort

        for i in range(5):
            await aggregate_to_cohort(
                lesson_conditions="No customer ID here",
                lesson_insight="Generic pattern without PII",
                pattern_type="generic_pattern",
                category="bills",
                cohort_key="test_cohort",
                confidence=0.80,
            )

        db = await get_db()
        cursor = await db.execute(
            "SELECT * FROM cohort_insights WHERE cohort_key = 'test_cohort'"
        )
        row = await cursor.fetchone()
        await db.close()

        assert "customer_id" not in dict(row).keys() or row.get("customer_id") is None
