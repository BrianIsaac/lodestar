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
    """Types of proactive triggers.

    All of these are implemented as pure-Python sensors. The agentic layer
    (`agents/detector.py`) calls them as tools during reasoning rather
    than auto-firing cards off them.
    """

    VELOCITY_ANOMALY = "velocity_anomaly"
    RECURRING_CHANGE = "recurring_change"
    PAYDAY_DETECTED = "payday_detected"
    BUDGET_THRESHOLD = "budget_threshold"
    GOAL_MILESTONE = "goal_milestone"
    LIFE_EVENT = "life_event"
    LARGE_OUTFLOW = "large_outflow"
    FIRST_TIME_MERCHANT = "first_time_merchant"
    CATEGORY_CONCENTRATION = "category_concentration"
    SUBSCRIPTION_BLOAT = "subscription_bloat"
    WEEKEND_SPIKE = "weekend_spike"


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


def check_large_outflow(
    transactions: list[Transaction], customer_id: str, pct_of_income: float = 0.15
) -> TriggerEvent | None:
    """Detect a single outflow larger than a fraction of monthly income.

    Complements velocity_anomaly (which is category-level) by catching
    one-off chunky payments that wouldn't move a category ratio much
    but are still notable on their own.

    Args:
        transactions: Recent transactions (should include salary credits).
        customer_id: Customer identifier.
        pct_of_income: Threshold as a fraction of most recent salary.

    Returns:
        TriggerEvent if a single outflow crosses the threshold, else None.
    """
    salaries = [t.amount for t in transactions if t.category == "salary" and t.amount > 0]
    if not salaries:
        return None
    monthly_income = salaries[-1]
    threshold = monthly_income * pct_of_income

    for t in sorted(transactions, key=lambda x: str(x.date), reverse=True)[:60]:
        if t.amount < 0 and abs(t.amount) >= threshold:
            return TriggerEvent(
                trigger_type=TriggerType.LARGE_OUTFLOW,
                customer_id=customer_id,
                severity=0.7,
                context={
                    "merchant": t.merchant,
                    "category": t.category,
                    "amount": abs(t.amount),
                    "pct_of_income": abs(t.amount) / monthly_income,
                },
                description=(
                    f"Giao dịch lớn {abs(t.amount):,.0f} VND tại {t.merchant} — "
                    f"{abs(t.amount) / monthly_income:.0%} thu nhập tháng."
                ),
            )
    return None


def check_first_time_merchant(
    transactions: list[Transaction], customer_id: str
) -> TriggerEvent | None:
    """Flag the most recent transaction's merchant if never seen before
    in the historical window. A first-time merchant is a weak but
    useful signal of a new behaviour — can cluster with other signals.

    Args:
        transactions: Recent transactions (sorted by date ascending).
        customer_id: Customer identifier.

    Returns:
        TriggerEvent if the latest merchant is novel, else None.
    """
    if not transactions:
        return None
    # Sort to find the most recent
    ordered = sorted(transactions, key=lambda x: str(x.date))
    latest = ordered[-1]
    if not latest.merchant or latest.amount >= 0:
        return None
    merchant = latest.merchant.strip().lower()
    for t in ordered[:-1]:
        if (t.merchant or "").strip().lower() == merchant:
            return None
    return TriggerEvent(
        trigger_type=TriggerType.FIRST_TIME_MERCHANT,
        customer_id=customer_id,
        severity=0.3,
        context={
            "merchant": latest.merchant,
            "amount": abs(latest.amount),
            "category": latest.category,
        },
        description=f"Giao dịch đầu tiên tại {latest.merchant}.",
    )


def check_category_concentration(
    transactions: list[Transaction],
    customer_id: str,
    window_days: int = 7,
    threshold_pct: float = 0.50,
) -> TriggerEvent | None:
    """Detect single-category concentration in the last N days.

    Useful for catching lifestyle shifts (e.g. 60% of the week went to
    health) that wouldn't register as a velocity anomaly yet.

    Args:
        transactions: Recent transactions.
        customer_id: Customer identifier.
        window_days: Window size for concentration check.
        threshold_pct: Min fraction for a category to count as concentrated.

    Returns:
        TriggerEvent if a single category exceeds the threshold, else None.
    """
    cutoff = date.today() - timedelta(days=window_days)
    window = [
        t
        for t in transactions
        if t.amount < 0
        and (
            t.date if isinstance(t.date, date) else date.fromisoformat(str(t.date))
        )
        >= cutoff
    ]
    if not window:
        return None

    total = sum(abs(t.amount) for t in window)
    if total <= 0:
        return None

    by_cat: dict[str, float] = defaultdict(float)
    for t in window:
        by_cat[t.category or "other"] += abs(t.amount)

    top_cat, top_amount = max(by_cat.items(), key=lambda kv: kv[1])
    pct = top_amount / total
    if pct >= threshold_pct:
        return TriggerEvent(
            trigger_type=TriggerType.CATEGORY_CONCENTRATION,
            customer_id=customer_id,
            severity=0.5,
            context={
                "category": top_cat,
                "pct": pct,
                "window_days": window_days,
                "amount": top_amount,
            },
            description=(
                f"Trong {window_days} ngày qua, {top_cat} chiếm "
                f"{pct:.0%} chi tiêu."
            ),
        )
    return None


def check_subscription_bloat(
    transactions: list[Transaction], customer_id: str, min_count: int = 5
) -> TriggerEvent | None:
    """Count small recurring charges (monthly subscriptions under 500K).

    Args:
        transactions: Recent transactions (4+ months).
        customer_id: Customer identifier.
        min_count: Minimum number of distinct recurring merchants to flag.

    Returns:
        TriggerEvent if subscription bloat is detected, else None.
    """
    by_merchant: dict[str, list[float]] = defaultdict(list)
    for t in transactions:
        if t.amount >= 0 or not t.merchant or abs(t.amount) > 500_000:
            continue
        by_merchant[t.merchant].append(abs(t.amount))

    recurring = [m for m, amts in by_merchant.items() if len(amts) >= 3]
    if len(recurring) < min_count:
        return None
    total_monthly = sum(sum(by_merchant[m]) / len(by_merchant[m]) for m in recurring)
    return TriggerEvent(
        trigger_type=TriggerType.SUBSCRIPTION_BLOAT,
        customer_id=customer_id,
        severity=0.4,
        context={
            "merchants": recurring,
            "count": len(recurring),
            "monthly_total": total_monthly,
        },
        description=(
            f"Đang có {len(recurring)} khoản trả góp/đăng ký nhỏ "
            f"(~{total_monthly:,.0f} VND/tháng)."
        ),
    )


def check_weekend_spike(
    transactions: list[Transaction], customer_id: str
) -> TriggerEvent | None:
    """Detect a weekend category whose spend is 2x+ the weekday average.

    Args:
        transactions: Recent transactions.
        customer_id: Customer identifier.

    Returns:
        TriggerEvent if a weekend category spikes, else None.
    """
    weekend_by_cat: dict[str, float] = defaultdict(float)
    weekday_by_cat: dict[str, float] = defaultdict(float)
    weekday_days = 0
    weekend_days = 0
    seen_days: set[str] = set()

    for t in transactions:
        if t.amount >= 0:
            continue
        d = t.date if isinstance(t.date, date) else date.fromisoformat(str(t.date))
        cat = t.category or "other"
        day_key = d.isoformat()
        is_weekend = d.weekday() >= 5
        if is_weekend:
            weekend_by_cat[cat] += abs(t.amount)
        else:
            weekday_by_cat[cat] += abs(t.amount)
        if day_key not in seen_days:
            seen_days.add(day_key)
            if is_weekend:
                weekend_days += 1
            else:
                weekday_days += 1

    if weekend_days == 0 or weekday_days == 0:
        return None

    for cat, weekend_total in weekend_by_cat.items():
        weekend_avg = weekend_total / max(weekend_days, 1)
        weekday_avg = weekday_by_cat.get(cat, 0) / max(weekday_days, 1)
        if weekday_avg > 0 and weekend_avg / weekday_avg >= 2.0:
            return TriggerEvent(
                trigger_type=TriggerType.WEEKEND_SPIKE,
                customer_id=customer_id,
                severity=0.4,
                context={
                    "category": cat,
                    "weekend_avg": weekend_avg,
                    "weekday_avg": weekday_avg,
                    "ratio": weekend_avg / weekday_avg,
                },
                description=(
                    f"Chi tiêu cho {cat} cuối tuần gấp "
                    f"{weekend_avg / weekday_avg:.1f} lần trung bình ngày thường."
                ),
            )
    return None


