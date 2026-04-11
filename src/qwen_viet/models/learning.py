"""Learning loop data models — lessons, reflections, cohort insights."""

from datetime import datetime

from pydantic import BaseModel, Field


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
    created_at: datetime = Field(default_factory=datetime.utcnow)


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
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CohortInsight(BaseModel):
    """Anonymised, aggregated insight from multiple customers."""

    cohort_key: str = Field(description="e.g. hcmc_young_professional_mid_income")
    pattern_type: str
    category: str
    insight: str
    confidence: float = Field(0.5, ge=0, le=1)
    supporting_count: int = 0
    effectiveness: float = Field(0.0, ge=0, le=1)
    min_customers: int = 5
