"""Deterministic trigger rules — no LLM involvement.

Each trigger checks transaction patterns and returns a TriggerEvent
if the condition is met, or None if not.
"""

from collections import defaultdict
from datetime import date, timedelta
from enum import StrEnum

from pydantic import BaseModel, Field

from lodestar.models import Transaction


class TriggerType(StrEnum):
    """Types of proactive triggers."""

    VELOCITY_ANOMALY = "velocity_anomaly"
    RECURRING_CHANGE = "recurring_change"
    PAYDAY_DETECTED = "payday_detected"
    BUDGET_THRESHOLD = "budget_threshold"
    GOAL_MILESTONE = "goal_milestone"
    LIFE_EVENT = "life_event"


class TriggerEvent(BaseModel):
    """A detected trigger event to be processed by the background agent."""

    trigger_type: TriggerType
    customer_id: str
    severity: float = Field(0.5, ge=0, le=1)
    context: dict = Field(default_factory=dict)
    description: str = ""


LIFE_EVENT_KEYWORDS: dict[str, list[str]] = {
    "baby": ["kids plaza", "con cưng", "bibo mart", "phụ sản", "mothercare"],
    "home_purchase": ["bđs", "vinhomes", "nội thất", "ikea", "điện máy xanh"],
    "career_change": ["đào tạo", "coworking", "coursera", "udemy"],
}


def check_velocity_anomaly(
    transactions: list[Transaction], customer_id: str
) -> TriggerEvent | None:
    """Detect if current month spending in any category is 3x+ above average.

    Args:
        transactions: Recent transactions (ideally 4+ months).
        customer_id: Customer identifier.

    Returns:
        TriggerEvent if anomaly detected, None otherwise.
    """
    by_month_cat: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))

    for t in transactions:
        if t.amount >= 0:
            continue
        month = t.date if isinstance(t.date, str) else t.date.isoformat()
        month_key = month[:7]
        cat = t.category or "other"
        by_month_cat[month_key][cat] += abs(t.amount)

    if len(by_month_cat) < 2:
        return None

    months_sorted = sorted(by_month_cat.keys())
    current_month = months_sorted[-1]
    previous_months = months_sorted[:-1]

    for cat, current_amount in by_month_cat[current_month].items():
        prev_amounts = [by_month_cat[m].get(cat, 0) for m in previous_months]
        avg = sum(prev_amounts) / len(prev_amounts) if prev_amounts else 0
        if avg > 0 and current_amount / avg >= 3.0:
            return TriggerEvent(
                trigger_type=TriggerType.VELOCITY_ANOMALY,
                customer_id=customer_id,
                severity=0.8,
                context={"category": cat, "current": current_amount, "average": avg},
                description=(
                    f"Chi tiêu cho {cat} đang cao gấp {current_amount / avg:.1f} lần "
                    f"so với trung bình các tháng trước."
                ),
            )

    return None


def check_recurring_change(
    transactions: list[Transaction], customer_id: str
) -> TriggerEvent | None:
    """Detect significant change in a recurring charge amount.

    Args:
        transactions: Recent transactions.
        customer_id: Customer identifier.

    Returns:
        TriggerEvent if a recurring charge changed by >20%, None otherwise.
    """
    by_merchant: dict[str, list[float]] = defaultdict(list)

    for t in transactions:
        if t.amount >= 0 or not t.merchant:
            continue
        by_merchant[t.merchant].append(abs(t.amount))

    for merchant, amounts in by_merchant.items():
        if len(amounts) < 3:
            continue
        recent = amounts[-1]
        avg_prior = sum(amounts[:-1]) / len(amounts[:-1])
        if avg_prior > 0 and abs(recent - avg_prior) / avg_prior > 0.20:
            change_pct = (recent - avg_prior) / avg_prior * 100
            return TriggerEvent(
                trigger_type=TriggerType.RECURRING_CHANGE,
                customer_id=customer_id,
                severity=0.5,
                context={"merchant": merchant, "recent": recent, "average": avg_prior, "change_pct": change_pct},
                description=(
                    f"Giao dịch định kỳ tại {merchant} đã thay đổi "
                    f"{change_pct:+.0f}% so với mức trung bình."
                ),
            )

    return None


def check_payday_detected(
    transactions: list[Transaction], customer_id: str
) -> TriggerEvent | None:
    """Detect a salary credit in the most recent transactions.

    Args:
        transactions: Recent transactions.
        customer_id: Customer identifier.

    Returns:
        TriggerEvent if a salary credit was detected today/recently.
    """
    today = date.today()
    recent_window = today - timedelta(days=3)

    for t in transactions:
        if t.category == "salary" and t.amount > 0:
            t_date = t.date if isinstance(t.date, date) else date.fromisoformat(str(t.date))
            if t_date >= recent_window:
                return TriggerEvent(
                    trigger_type=TriggerType.PAYDAY_DETECTED,
                    customer_id=customer_id,
                    severity=0.4,
                    context={"amount": t.amount, "date": str(t.date)},
                    description=f"Đã nhận lương {t.amount:,.0f} VND vào tài khoản.",
                )

    return None


def check_budget_threshold(
    transactions: list[Transaction], customer_id: str, budget_pct: float = 0.80
) -> TriggerEvent | None:
    """Check if spending has exceeded a percentage of estimated monthly budget.

    Args:
        transactions: Current month transactions.
        customer_id: Customer identifier.
        budget_pct: Threshold percentage (default 80%).

    Returns:
        TriggerEvent if budget threshold breached.
    """
    salary_amounts = [t.amount for t in transactions if t.category == "salary" and t.amount > 0]
    if not salary_amounts:
        return None

    monthly_income = salary_amounts[-1]
    current_month = date.today().strftime("%Y-%m")

    current_spending = sum(
        abs(t.amount) for t in transactions
        if t.amount < 0
        and (t.date if isinstance(t.date, str) else t.date.isoformat())[:7] == current_month
    )

    if current_spending > monthly_income * budget_pct:
        return TriggerEvent(
            trigger_type=TriggerType.BUDGET_THRESHOLD,
            customer_id=customer_id,
            severity=0.7,
            context={"spending": current_spending, "income": monthly_income, "pct": current_spending / monthly_income * 100},
            description=(
                f"Chi tiêu tháng này đang ở mức "
                f"{current_spending / monthly_income * 100:.0f}% thu nhập."
            ),
        )

    return None


def check_life_event_pattern(
    transactions: list[Transaction], customer_id: str
) -> TriggerEvent | None:
    """Detect potential life events from merchant/category patterns.

    Args:
        transactions: Recent transactions (2-3 months).
        customer_id: Customer identifier.

    Returns:
        TriggerEvent if a life event pattern detected.
    """
    recent_merchants = []
    for t in transactions:
        if t.amount < 0 and t.merchant:
            recent_merchants.append(t.merchant.lower())

    event_type_vi = {
        "baby": "chuẩn bị đón em bé",
        "home_purchase": "mua nhà",
        "career_change": "chuyển đổi công việc",
    }

    for event_type, keywords in LIFE_EVENT_KEYWORDS.items():
        matches = sum(1 for m in recent_merchants if any(kw in m for kw in keywords))
        if matches >= 2:
            vi_label = event_type_vi.get(event_type, event_type)
            return TriggerEvent(
                trigger_type=TriggerType.LIFE_EVENT,
                customer_id=customer_id,
                severity=0.9,
                context={"event_type": event_type, "match_count": matches},
                description=(
                    f"Phát hiện dấu hiệu {vi_label} qua {matches} giao dịch gần đây."
                ),
            )

    return None


ALL_TRIGGERS = [
    check_velocity_anomaly,
    check_recurring_change,
    check_payday_detected,
    check_budget_threshold,
    check_life_event_pattern,
]


def run_all_triggers(
    transactions: list[Transaction], customer_id: str
) -> list[TriggerEvent]:
    """Run all trigger rules against a set of transactions.

    Args:
        transactions: Customer's transactions to check.
        customer_id: Customer identifier.

    Returns:
        List of triggered events (may be empty).
    """
    events = []
    for trigger_fn in ALL_TRIGGERS:
        result = trigger_fn(transactions, customer_id)
        if result is not None:
            events.append(result)
    return events
