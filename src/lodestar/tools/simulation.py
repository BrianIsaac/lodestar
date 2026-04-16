"""Cross-entity financial scenario simulation — deterministic projections.

Output text for all user-facing summaries is produced in the requested
`language` using static templates (no runtime LLM translation). All three
locales — Vietnamese, English, Korean — are authored inline so /simulate
responses are already in the right language before they reach the
frontend or the orchestrator tool-call boundary.
"""

import numpy_financial as npf

from lodestar.database import get_db
from lodestar.models import EntityImpact, ScenarioResult
from lodestar.tools.spending import compute_income_pattern


def _fmt(n: float) -> str:
    """Format a number as a thousands-separated integer — lang-neutral."""
    return f"{n:,.0f}"


# Text templates per language. Positional kwargs per call site below.
_T: dict[str, dict[str, str]] = {
    "bank": {
        "vi": "Khoản vay mua nhà {loan} VND với lãi suất {rate}% = {monthly}/tháng. Tiết kiệm còn lại sau đặt cọc: {remaining}.",
        "en": "Mortgage {loan} VND at {rate}% = {monthly}/month. Savings after down payment: {remaining}.",
        "ko": "주택담보대출 {loan} VND (금리 {rate}%) = 월 {monthly}원. 계약금 이후 잔여 저축: {remaining}.",
    },
    "finance": {
        "vi": "Nợ tiêu dùng hiện tại: {debt} VND. Nên thanh toán khoản vay cá nhân trước khi vay mua nhà.",
        "en": "Existing consumer debt: {debt} VND. Consider clearing the personal loan before the mortgage.",
        "ko": "현재 소비자 부채: {debt} VND. 주택담보대출 전에 개인대출을 상환하는 것이 좋습니다.",
    },
    "securities": {
        "vi": "Danh mục đầu tư: {portfolio} VND. Cần thanh lý thêm: {liquidation}.",
        "en": "Portfolio: {portfolio} VND. Liquidation needed: {liquidation}.",
        "ko": "포트폴리오: {portfolio} VND. 필요 청산액: {liquidation}.",
    },
    "life": {
        "vi": "Bảo hiểm hiện tại: {coverage} VND. Khuyến nghị kèm khoản vay mua nhà: {recommended} VND.",
        "en": "Current coverage: {coverage} VND. Recommended with mortgage: {recommended} VND.",
        "ko": "현재 보장액: {coverage} VND. 주택담보대출 시 권장 보장액: {recommended} VND.",
    },
    "combined": {
        "vi": "Dòng tiền hàng tháng: {before} → {after} VND",
        "en": "Monthly cashflow: {before} → {after} VND",
        "ko": "월 현금흐름: {before} → {after} VND",
    },
    "risk_dti": {
        "vi": "Tỷ lệ DTI ở mức {pct:.0%} — vượt ngưỡng an toàn 50%",
        "en": "DTI ratio at {pct:.0%} — above 50% comfort zone",
        "ko": "DTI 비율 {pct:.0%} — 안전 기준 50% 초과",
    },
    "risk_cashflow": {
        "vi": "Dòng tiền còn lại dưới 10% thu nhập",
        "en": "Remaining cashflow below 10% of income",
        "ko": "잔여 현금흐름이 소득의 10% 미만",
    },
}


def _line(key: str, language: str, /, **kwargs) -> str:
    """Resolve a template in the requested language with positional fallback."""
    lang = language if language in ("vi", "en", "ko") else "vi"
    return _T[key][lang].format(**kwargs)


async def simulate_scenario(
    customer_id: str,
    scenario_type: str,
    parameters: dict,
    language: str = "vi",
) -> ScenarioResult:
    """Simulate a financial scenario across all Shinhan entities.

    Args:
        customer_id: Customer identifier.
        scenario_type: Type of scenario (e.g. ``home_purchase``).
        parameters: Scenario-specific parameters.
        language: Display language for all summary strings.

    Returns:
        ScenarioResult with per-entity impact and combined cashflow analysis.
    """
    income = await compute_income_pattern(customer_id)
    monthly_income = income.average_income

    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT entity, account_type, balance FROM accounts WHERE customer_id = ?",
            (customer_id,),
        )
        accounts = await cursor.fetchall()
    finally:
        await db.close()

    account_map: dict[str, list[dict]] = {}
    for a in accounts:
        account_map.setdefault(a["entity"], []).append(dict(a))

    existing_monthly_debt = sum(
        abs(a["balance"]) / 12
        for accts in account_map.values()
        for a in accts
        if a["account_type"] in ("loan", "credit_card") and a["balance"] < 0
    )

    cashflow_before = monthly_income - existing_monthly_debt
    entity_impacts: list[EntityImpact] = []
    risk_flags: list[str] = []
    additional_monthly = 0.0

    if scenario_type == "home_purchase":
        property_value = float(parameters.get("property_value", 2_000_000_000))
        down_payment_pct = float(parameters.get("down_payment_pct", 0.20))
        rate = float(parameters.get("interest_rate", 7.5))
        term = int(parameters.get("term_months", 240))

        loan_amount = property_value * (1 - down_payment_pct)
        down_payment = property_value * down_payment_pct
        monthly_rate = rate / 100 / 12
        monthly_mortgage = float(-npf.pmt(monthly_rate, term, loan_amount))
        additional_monthly = monthly_mortgage

        savings_balance = sum(
            a["balance"] for a in account_map.get("bank", [])
            if a["account_type"] == "savings" and a["balance"] > 0
        )
        remaining = max(0.0, savings_balance - down_payment)

        entity_impacts.append(EntityImpact(
            entity="bank",
            summary=_line(
                "bank", language,
                loan=_fmt(loan_amount), rate=rate,
                monthly=_fmt(monthly_mortgage), remaining=_fmt(remaining),
            ),
            metrics={
                "loan_amount": loan_amount,
                "monthly_payment": monthly_mortgage,
                "savings_remaining": remaining,
            },
        ))

        finance_debt = sum(
            abs(a["balance"]) for a in account_map.get("finance", [])
            if a["balance"] < 0
        )
        entity_impacts.append(EntityImpact(
            entity="finance",
            summary=_line("finance", language, debt=_fmt(finance_debt)),
            metrics={"existing_debt": finance_debt},
        ))

        portfolio_value = sum(
            a["balance"] for a in account_map.get("securities", [])
            if a["balance"] > 0
        )
        liquidation_needed = max(0.0, down_payment - savings_balance)
        entity_impacts.append(EntityImpact(
            entity="securities",
            summary=_line(
                "securities", language,
                portfolio=_fmt(portfolio_value),
                liquidation=_fmt(liquidation_needed),
            ),
            metrics={
                "portfolio_value": portfolio_value,
                "liquidation_needed": liquidation_needed,
            },
        ))

        insurance_coverage = sum(
            a["balance"] for a in account_map.get("life", [])
            if a["balance"] > 0
        )
        recommended_coverage = property_value * 1.2
        entity_impacts.append(EntityImpact(
            entity="life",
            summary=_line(
                "life", language,
                coverage=_fmt(insurance_coverage),
                recommended=_fmt(recommended_coverage),
            ),
            metrics={
                "current_coverage": insurance_coverage,
                "recommended_coverage": recommended_coverage,
            },
        ))

    cashflow_after = cashflow_before - additional_monthly
    new_dti = (
        (existing_monthly_debt + additional_monthly) / monthly_income
        if monthly_income > 0
        else 1.0
    )

    if new_dti > 0.50:
        risk_flags.append(_line("risk_dti", language, pct=new_dti))
    if cashflow_after < monthly_income * 0.10:
        risk_flags.append(_line("risk_cashflow", language))

    return ScenarioResult(
        customer_id=customer_id,
        scenario_type=scenario_type,
        entity_impacts=entity_impacts,
        combined_summary=_line(
            "combined", language,
            before=_fmt(cashflow_before), after=_fmt(cashflow_after),
        ),
        monthly_cashflow_before=round(cashflow_before),
        monthly_cashflow_after=round(cashflow_after),
        risk_flags=risk_flags,
    )
