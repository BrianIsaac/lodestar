"""Product catalogue and scenario simulation models."""

from pydantic import BaseModel, Field


class ProductInfo(BaseModel):
    """A single Shinhan financial product.

    All name/description variants are authored upfront in the catalogue JSON
    so the API can return the correct language without runtime translation.
    """

    product_id: str
    entity: str = Field(description="bank | finance | securities | life")
    product_type: str = Field(description="credit_card | savings | loan | insurance | investment | etc.")
    name_vi: str = ""
    name_en: str = ""
    name_ko: str = ""
    description_vi: str = ""
    description_en: str = ""
    description_ko: str = ""
    interest_rate: float | None = None
    min_income: float | None = None
    currency: str = "VND"
    eligibility_criteria: dict = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)


class ProductFilters(BaseModel):
    """Filters for product search."""

    product_type: str | None = None
    entity: str | None = None
    max_interest_rate: float | None = None
    min_income_lte: float | None = None


class EligibilityResult(BaseModel):
    """Result of checking a customer's eligibility for a product."""

    product_id: str
    customer_id: str
    eligible: bool = False
    reasons: list[str] = Field(default_factory=list)


class ComparisonTable(BaseModel):
    """Side-by-side product comparison."""

    product_ids: list[str]
    columns: list[str] = Field(default_factory=list)
    rows: list[dict] = Field(default_factory=list)


class EntityImpact(BaseModel):
    """Impact of a scenario on a single Shinhan entity."""

    entity: str
    summary: str
    metrics: dict[str, float] = Field(default_factory=dict)


class ScenarioRequest(BaseModel):
    """Request to simulate a financial scenario."""

    customer_id: str
    scenario_type: str = Field(description="home_purchase | career_change | new_baby | marriage")
    parameters: dict = Field(default_factory=dict)
    language: str = Field(default="vi", description="Display language: vi | en | ko")


class ScenarioResult(BaseModel):
    """Cross-entity scenario simulation output."""

    customer_id: str
    scenario_type: str
    entity_impacts: list[EntityImpact] = Field(default_factory=list)
    combined_summary: str = ""
    monthly_cashflow_before: float = 0.0
    monthly_cashflow_after: float = 0.0
    risk_flags: list[str] = Field(default_factory=list)


class SavingsGoal(BaseModel):
    """A customer's savings goal."""

    goal_id: str
    customer_id: str
    name: str
    target_amount: float
    current_amount: float = 0.0
    target_date: str = ""
    created_at: str = ""


class GoalProjection(BaseModel):
    """Projected completion of a savings goal."""

    goal_id: str
    projected_date: str | None = None
    monthly_required: float = 0.0
    on_track: bool = False
    confidence: float = 0.0


class SpendingSummary(BaseModel):
    """Aggregated spending breakdown for a period."""

    customer_id: str
    period: str
    total: float = 0.0
    by_category: dict[str, float] = Field(default_factory=dict)
    by_category_pct: dict[str, float] = Field(default_factory=dict)
    currency: str = "VND"


class SpendingAnomaly(BaseModel):
    """An unusual spending pattern detected."""

    category: str
    current_amount: float
    average_amount: float
    deviation_pct: float
    description: str = ""


class RecurringCharge(BaseModel):
    """A detected recurring transaction."""

    merchant: str
    category: str
    average_amount: float
    frequency: str = "monthly"
    last_seen: str = ""


class MoMChange(BaseModel):
    """Month-over-month spending change."""

    period: str
    category: str
    amount: float
    previous_amount: float
    change_pct: float


class SavingsRate(BaseModel):
    """Customer savings rate over a period."""

    customer_id: str
    rate: float = Field(description="Percentage of income saved")
    trend: str = "stable"
    average_monthly_savings: float = 0.0


class AffordabilityResult(BaseModel):
    """Loan affordability assessment."""

    customer_id: str
    loan_amount: float
    monthly_payment: float
    dti_after: float
    affordable: bool = False
    max_affordable_amount: float = 0.0
