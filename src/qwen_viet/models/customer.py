"""Customer-related data models."""

from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class CustomerSegment(StrEnum):
    """Shinhan customer segments."""

    MASS = "mass"
    MASS_AFFLUENT = "mass_affluent"
    AFFLUENT = "affluent"
    SOHO = "soho"


class CustomerProfile(BaseModel):
    """Demographics and segment information."""

    customer_id: str
    full_name: str
    date_of_birth: date
    gender: str
    city: str
    income_monthly: float = Field(description="Monthly income in VND")
    segment: CustomerSegment = CustomerSegment.MASS
    language: str = "vi"
    created_at: datetime | None = None


class AccountBalance(BaseModel):
    """Single account balance snapshot."""

    account_id: str
    customer_id: str
    entity: str = Field(description="bank | finance | securities | life")
    account_type: str = Field(description="savings | current | fixed_deposit | loan | credit_card | portfolio | policy")
    balance: float
    currency: str = "VND"
    as_of: datetime | None = None


class Transaction(BaseModel):
    """A single banking transaction."""

    transaction_id: str
    customer_id: str
    account_id: str
    date: date
    amount: float = Field(description="Positive=credit, negative=debit")
    currency: str = "VND"
    category: str | None = None
    merchant: str | None = None
    description: str = ""
    entity: str = "bank"


class IncomePattern(BaseModel):
    """Detected income regularity for a customer."""

    customer_id: str
    detected_payday: int | None = Field(None, description="Day of month (1-31)")
    regularity_score: float = Field(0.0, ge=0, le=1)
    average_income: float = 0.0
    income_trend: str = "stable"


class DebtSummary(BaseModel):
    """Aggregated debt position across entities."""

    customer_id: str
    total_debt: float = 0.0
    monthly_repayment: float = 0.0
    dti_ratio: float = Field(0.0, description="Debt-to-income ratio")
    loans: list[dict] = Field(default_factory=list)


class NetWorth(BaseModel):
    """Assets minus liabilities across all entities."""

    customer_id: str
    total_assets: float = 0.0
    total_liabilities: float = 0.0
    net_worth: float = 0.0
    breakdown: dict[str, float] = Field(default_factory=dict)
