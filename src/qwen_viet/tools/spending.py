"""Deterministic spending analysis tools — no LLM involvement."""

from datetime import date, timedelta

from qwen_viet.database import get_db
from qwen_viet.models import (
    IncomePattern,
    MoMChange,
    RecurringCharge,
    SpendingAnomaly,
    SpendingSummary,
    Transaction,
)

CATEGORY_RULES: dict[str, list[str]] = {
    "food": ["grab food", "shopeefood", "pho", "bún", "circle k", "highland", "phúc long", "lotteria", "pizza", "nhà hàng"],
    "transport": ["grab", "be", "xăng", "petrolimex", "vietjet", "vietnam airlines", "taxi", "xe buýt"],
    "shopping": ["shopee", "lazada", "thế giới di động", "uniqlo", "fpt shop", "bách hoá", "vinmart", "zara"],
    "bills": ["evn", "viettel", "vnpt", "nước sạch", "fpt telecom", "mobifone", "vtvcab"],
    "health": ["bệnh viện", "nhà thuốc", "medicare", "vinmec", "pharmacity"],
    "entertainment": ["cgv", "netflix", "spotify", "galaxy cinema"],
    "education": ["ielts", "coursera", "udemy", "đào tạo"],
}


def categorise_transaction(description: str, merchant: str | None = None) -> str:
    """Categorise a transaction using rule-based matching.

    Args:
        description: Transaction description text.
        merchant: Optional merchant name for higher accuracy.

    Returns:
        Category string or ``'other'`` if no match found.
    """
    text = (f"{description} {merchant or ''}").lower()
    for category, keywords in CATEGORY_RULES.items():
        for kw in keywords:
            if kw in text:
                return category
    return "other"


async def get_transactions(
    customer_id: str,
    start_date: str,
    end_date: str,
    category: str | None = None,
) -> list[Transaction]:
    """Fetch transactions from the database.

    Args:
        customer_id: Customer identifier.
        start_date: Start date (YYYY-MM-DD).
        end_date: End date (YYYY-MM-DD).
        category: Optional category filter.

    Returns:
        List of Transaction models.
    """
    db = await get_db()
    try:
        query = "SELECT * FROM transactions WHERE customer_id = ? AND date >= ? AND date <= ?"
        params: list = [customer_id, start_date, end_date]
        if category:
            query += " AND category = ?"
            params.append(category)
        query += " ORDER BY date DESC"

        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        return [
            Transaction(
                transaction_id=r["transaction_id"],
                customer_id=r["customer_id"],
                account_id=r["account_id"],
                date=r["date"],
                amount=r["amount"],
                category=r["category"],
                merchant=r["merchant"],
                description=r["description"],
                entity=r["entity"],
            )
            for r in rows
        ]
    finally:
        await db.close()


async def compute_spending_summary(customer_id: str, period: str) -> SpendingSummary:
    """Compute spending breakdown for a customer over a given month.

    Args:
        customer_id: Customer identifier.
        period: Month in YYYY-MM format.

    Returns:
        SpendingSummary with per-category totals and percentages.
    """
    start = f"{period}-01"
    year, month = int(period[:4]), int(period[5:7])
    if month == 12:
        end = f"{year + 1}-01-01"
    else:
        end = f"{year}-{month + 1:02d}-01"

    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT category, SUM(ABS(amount)) as total
               FROM transactions
               WHERE customer_id = ? AND date >= ? AND date < ? AND amount < 0
               GROUP BY category""",
            (customer_id, start, end),
        )
        rows = await cursor.fetchall()

        by_category: dict[str, float] = {}
        grand_total = 0.0
        for r in rows:
            cat = r["category"] or "other"
            by_category[cat] = r["total"]
            grand_total += r["total"]

        by_category_pct: dict[str, float] = {}
        if grand_total > 0:
            by_category_pct = {k: round(v / grand_total * 100, 1) for k, v in by_category.items()}

        return SpendingSummary(
            customer_id=customer_id,
            period=period,
            total=grand_total,
            by_category=by_category,
            by_category_pct=by_category_pct,
        )
    finally:
        await db.close()


async def compute_income_pattern(customer_id: str) -> IncomePattern:
    """Detect income regularity from transaction history.

    Args:
        customer_id: Customer identifier.

    Returns:
        IncomePattern with detected payday and regularity score.
    """
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT date, amount FROM transactions
               WHERE customer_id = ? AND category = 'salary'
               ORDER BY date""",
            (customer_id,),
        )
        rows = await cursor.fetchall()

        if not rows:
            return IncomePattern(customer_id=customer_id)

        days = [int(r["date"].split("-")[2]) for r in rows]
        amounts = [r["amount"] for r in rows]

        avg_day = round(sum(days) / len(days))
        day_variance = sum((d - avg_day) ** 2 for d in days) / len(days)
        regularity = max(0, 1.0 - day_variance / 25.0)

        return IncomePattern(
            customer_id=customer_id,
            detected_payday=avg_day,
            regularity_score=round(regularity, 2),
            average_income=round(sum(amounts) / len(amounts)),
            income_trend="stable",
        )
    finally:
        await db.close()


async def detect_anomalies(customer_id: str, period: str) -> list[SpendingAnomaly]:
    """Detect spending anomalies by comparing to 3-month averages.

    Args:
        customer_id: Customer identifier.
        period: Month to check (YYYY-MM).

    Returns:
        List of anomalies where current spending deviates >30% from average.
    """
    current = await compute_spending_summary(customer_id, period)

    year, month = int(period[:4]), int(period[5:7])
    prev_summaries = []
    for i in range(1, 4):
        pm = month - i
        py = year
        if pm <= 0:
            pm += 12
            py -= 1
        prev = await compute_spending_summary(customer_id, f"{py}-{pm:02d}")
        prev_summaries.append(prev)

    anomalies = []
    for cat, amount in current.by_category.items():
        prev_amounts = [s.by_category.get(cat, 0) for s in prev_summaries]
        avg = sum(prev_amounts) / len(prev_amounts) if prev_amounts else 0
        if avg > 0:
            deviation = (amount - avg) / avg * 100
            if abs(deviation) > 30:
                anomalies.append(SpendingAnomaly(
                    category=cat,
                    current_amount=amount,
                    average_amount=round(avg),
                    deviation_pct=round(deviation, 1),
                    description=f"{cat} spending {'above' if deviation > 0 else 'below'} 3-month average by {abs(deviation):.0f}%",
                ))

    return anomalies


async def detect_recurring_charges(customer_id: str) -> list[RecurringCharge]:
    """Detect recurring transactions from the last 6 months.

    Args:
        customer_id: Customer identifier.

    Returns:
        List of detected recurring charges.
    """
    db = await get_db()
    try:
        six_months_ago = (date.today() - timedelta(days=180)).isoformat()
        cursor = await db.execute(
            """SELECT merchant, category, COUNT(*) as cnt, AVG(ABS(amount)) as avg_amt,
                      MAX(date) as last_date
               FROM transactions
               WHERE customer_id = ? AND date >= ? AND amount < 0 AND merchant IS NOT NULL
               GROUP BY merchant, category
               HAVING cnt >= 3
               ORDER BY cnt DESC""",
            (customer_id, six_months_ago),
        )
        rows = await cursor.fetchall()
        return [
            RecurringCharge(
                merchant=r["merchant"],
                category=r["category"] or "other",
                average_amount=round(r["avg_amt"]),
                frequency="monthly" if r["cnt"] >= 5 else "occasional",
                last_seen=r["last_date"],
            )
            for r in rows
        ]
    finally:
        await db.close()


async def compute_month_over_month_change(
    customer_id: str, category: str | None = None
) -> list[MoMChange]:
    """Compute month-over-month spending changes.

    Args:
        customer_id: Customer identifier.
        category: Optional category filter; if None, returns all categories.

    Returns:
        List of MoMChange entries for the last 6 months.
    """
    today = date.today()
    changes = []

    for i in range(6):
        m = today.month - i
        y = today.year
        if m <= 0:
            m += 12
            y -= 1
        period = f"{y}-{m:02d}"

        pm = m - 1
        py = y
        if pm <= 0:
            pm += 12
            py -= 1
        prev_period = f"{py}-{pm:02d}"

        current = await compute_spending_summary(customer_id, period)
        previous = await compute_spending_summary(customer_id, prev_period)

        cats = [category] if category else list(current.by_category.keys())
        for cat in cats:
            curr_amt = current.by_category.get(cat, 0)
            prev_amt = previous.by_category.get(cat, 0)
            if prev_amt > 0:
                pct = round((curr_amt - prev_amt) / prev_amt * 100, 1)
            else:
                pct = 0.0

            changes.append(MoMChange(
                period=period,
                category=cat,
                amount=curr_amt,
                previous_amount=prev_amt,
                change_pct=pct,
            ))

    return changes
