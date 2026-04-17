"""Learning loop data models — lessons, reflections, cohort insights."""

from datetime import UTC, datetime

from pydantic import BaseModel, Field


def _utc_naive_now() -> datetime:
    """Timezone-naive UTC timestamp used for schema compatibility.

    SQLite stores datetimes as ISO strings and the journal reader compares
    them to a naive `datetime.now(UTC).replace(tzinfo=None)`. Keeping the
    factory naive preserves that contract without reintroducing the
    deprecated ``datetime.utcnow()``.
    """
    return datetime.now(UTC).replace(tzinfo=None)


class CustomerLesson(BaseModel):
    """A quality-gated insight stored per customer."""

    lesson_id: str
    customer_id: str
    conditions: str = Field(description="When this lesson applies")
    insight: str = Field(description="What was learned")
    error_type: str = Field(
        "missed_factor",
        description="direction | magnitude | confidence | timing | missed_factor",
    )
    confidence: float = Field(0.5, ge=0, le=1)
    importance: float = Field(5.0, ge=0, le=10)
    times_evolved: int = 0
    supporting_months: list[str] = Field(default_factory=list)
    embedding: bytes | None = None
    created_at: datetime = Field(default_factory=_utc_naive_now)


class CustomerReflection(BaseModel):
    """Process/outcome evaluation of an interaction."""

    reflection_id: str
    customer_id: str
    interaction_id: str
    process_grade: str = Field(description="A, B, C, D, F")
    outcome_quality: str = Field(description="good | bad")
    quadrant: str = Field(
        description="earned_reward | bad_luck | dumb_luck | just_desserts"
    )
    lesson_extracted: bool = False
    created_at: datetime = Field(default_factory=_utc_naive_now)


class CohortInsight(BaseModel):
    """Anonymised, aggregated insight from multiple customers.

    The cohort surfacing threshold lives on ``settings.cohort_min_customers``;
    exposing it on the model caused drift because callers never read it back.
    """

    cohort_key: str = Field(description="e.g. hcmc_young_professional_mid_income")
    pattern_type: str
    category: str
    insight: str
    confidence: float = Field(0.5, ge=0, le=1)
    supporting_count: int = 0
