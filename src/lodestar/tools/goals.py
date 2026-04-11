"""Deterministic goal tracking and financial projection tools."""

import uuid
from datetime import date, datetime

import numpy_financial as npf

from lodestar.database import get_db
from lodestar.models import (
    AffordabilityResult,
    GoalProjection,
    SavingsGoal,
    SavingsRate,
)
from lodestar.tools.spending import compute_income_pattern, compute_spending_summary


async def create_goal(
    customer_id: str,
    name: str,
    target_amount: float,
    target_date: str,
) -> SavingsGoal:
    """Create a new savings goal for a customer.

    Args:
        customer_id: Customer identifier.
        name: Goal name (e.g. "Holiday Fund").
        target_amount: Target amount in VND.
        target_date: Target completion date (YYYY-MM-DD).

    Returns:
        The created SavingsGoal.
    """
    goal_id = f"G-{uuid.uuid4().hex[:8]}"
    db = await get_db()
    try:
        await db.execute(
            "INSERT INTO goals (goal_id, customer_id, name, target_amount, target_date) VALUES (?, ?, ?, ?, ?)",
            (goal_id, customer_id, name, target_amount, target_date),
        )
        await db.commit()
        return SavingsGoal(
            goal_id=goal_id,
            customer_id=customer_id,
            name=name,
            target_amount=target_amount,
            target_date=target_date,
            created_at=datetime.now().isoformat(),
        )
    finally:
        await db.close()


async def project_goal_completion(goal_id: str) -> GoalProjection:
    """Project when a savings goal will be completed.

    Args:
        goal_id: Goal identifier.

    Returns:
        GoalProjection with estimated completion date and monthly required amount.
    """
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM goals WHERE goal_id = ?", (goal_id,))
        row = await cursor.fetchone()
        if not row:
            return GoalProjection(goal_id=goal_id)

        customer_id = row["customer_id"]
        target = row["target_amount"]
        current = row["current_amount"]
        remaining = target - current

        savings_rate = await compute_savings_rate(customer_id)
        monthly_savings = savings_rate.average_monthly_savings

        if monthly_savings <= 0:
            return GoalProjection(
                goal_id=goal_id,
                monthly_required=remaining,
                on_track=False,
                confidence=0.2,
            )

        months_needed = remaining / monthly_savings
        today = date.today()
        projected_month = today.month + int(months_needed)
        projected_year = today.year + (projected_month - 1) // 12
        projected_month = ((projected_month - 1) % 12) + 1
        projected_date = f"{projected_year}-{projected_month:02d}"

        target_date = row["target_date"] or "2099-12"
        on_track = projected_date <= target_date[:7]

        return GoalProjection(
            goal_id=goal_id,
            projected_date=projected_date,
            monthly_required=round(remaining / max(1, months_needed)),
            on_track=on_track,
            confidence=min(0.95, savings_rate.rate / 100 + 0.3),
        )
    finally:
        await db.close()


async def compute_savings_rate(customer_id: str, months: int = 6) -> SavingsRate:
    """Compute average savings rate over recent months.

    Args:
        customer_id: Customer identifier.
        months: Number of months to look back.

    Returns:
        SavingsRate with percentage and trend.
    """
    income = await compute_income_pattern(customer_id)
    if income.average_income <= 0:
        return SavingsRate(customer_id=customer_id)

    today = date.today()
    total_spending = 0.0
    periods_counted = 0

    for i in range(months):
        m = today.month - i
        y = today.year
        if m <= 0:
            m += 12
            y -= 1
        summary = await compute_spending_summary(customer_id, f"{y}-{m:02d}")
        if summary.total > 0:
            total_spending += summary.total
            periods_counted += 1

    if periods_counted == 0:
        return SavingsRate(customer_id=customer_id)

    avg_monthly_spending = total_spending / periods_counted
    avg_monthly_savings = income.average_income - avg_monthly_spending
    rate = (avg_monthly_savings / income.average_income) * 100

    return SavingsRate(
        customer_id=customer_id,
        rate=round(rate, 1),
        trend="stable",
        average_monthly_savings=round(avg_monthly_savings),
    )


async def calculate_loan_affordability(
    customer_id: str,
    loan_amount: float,
    term: int,
    rate: float,
) -> AffordabilityResult:
    """Assess whether a customer can afford a given loan.

    Args:
        customer_id: Customer identifier.
        loan_amount: Desired loan amount in VND.
        term: Loan term in months.
        rate: Annual interest rate (e.g. 7.5 for 7.5%).

    Returns:
        AffordabilityResult with monthly payment, DTI ratio, and max affordable amount.
    """
    monthly_rate = rate / 100 / 12
    monthly_payment = float(-npf.pmt(monthly_rate, term, loan_amount))

    income = await compute_income_pattern(customer_id)
    if income.average_income <= 0:
        return AffordabilityResult(
            customer_id=customer_id,
            loan_amount=loan_amount,
            monthly_payment=round(monthly_payment),
            dti_after=1.0,
            affordable=False,
            max_affordable_amount=0,
        )

    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT SUM(ABS(balance)) FROM accounts WHERE customer_id = ? AND account_type IN ('loan', 'credit_card') AND balance < 0",
            (customer_id,),
        )
        row = await cursor.fetchone()
        existing_debt_monthly = (row[0] or 0) / 12
    finally:
        await db.close()

    total_monthly_debt = existing_debt_monthly + monthly_payment
    dti = total_monthly_debt / income.average_income

    max_monthly = income.average_income * 0.40 - existing_debt_monthly
    max_affordable = float(-npf.pv(monthly_rate, term, max_monthly)) if max_monthly > 0 else 0

    return AffordabilityResult(
        customer_id=customer_id,
        loan_amount=loan_amount,
        monthly_payment=round(monthly_payment),
        dti_after=round(dti, 3),
        affordable=dti <= 0.50,
        max_affordable_amount=round(max(0, max_affordable)),
    )
