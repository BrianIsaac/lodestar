"""Cross-entity financial scenario simulation — deterministic projections.

Output text for all user-facing summaries is produced in the requested
`language` using static templates (no runtime LLM translation). All three
locales — Vietnamese, English, Korean — are authored inline so /simulate
responses are already in the right language before they reach the
frontend or the orchestrator tool-call boundary.
"""

import numpy_financial as npf

from lodestar.agents.compliance import apply_compliance
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
    # career_change scenario
    "career_bank": {
        "vi": (
            "Thu nhập thay đổi: {before} → {after} VND/tháng "
            "(Δ {delta}). Tiết kiệm còn {savings} VND."
        ),
        "en": (
            "Income shift: {before} → {after} VND/month (Δ {delta}). "
            "Savings buffer: {savings} VND."
        ),
        "ko": (
            "소득 변동: 월 {before} → {after} VND (Δ {delta}). "
            "저축 잔액: {savings} VND."
        ),
    },
    "career_finance": {
        "vi": "Dư nợ hiện tại: {debt} VND — cần duy trì thanh toán dù thu nhập thay đổi.",
        "en": "Existing debt: {debt} VND — must be serviced even during the transition.",
        "ko": "현재 부채: {debt} VND — 전환기에도 상환 계획을 유지해야 합니다.",
    },
    "career_life": {
        "vi": "Bảo hiểm hiện tại: {coverage} VND. Xem xét giữ nguyên trong thời gian chuyển việc.",
        "en": "Current coverage: {coverage} VND. Consider maintaining it through the transition.",
        "ko": "현재 보장액: {coverage} VND. 전환기 동안 유지하는 것을 고려하세요.",
    },
    # new_baby scenario
    "baby_bank": {
        "vi": (
            "Chi phí em bé ước tính {cost} VND/tháng. "
            "Tiết kiệm hiện tại {savings} VND — quỹ dự phòng cần bổ sung {buffer_gap}."
        ),
        "en": (
            "Estimated baby costs: {cost} VND/month. "
            "Current savings: {savings} VND — emergency buffer gap: {buffer_gap}."
        ),
        "ko": (
            "예상 육아 비용: 월 {cost} VND. "
            "현재 저축: {savings} VND — 비상금 부족분: {buffer_gap}."
        ),
    },
    "baby_life": {
        "vi": "Bảo hiểm hiện tại: {coverage} VND. Khuyến nghị sau khi có con: {recommended} VND.",
        "en": "Current coverage: {coverage} VND. Recommended once baby arrives: {recommended} VND.",
        "ko": "현재 보장액: {coverage} VND. 출산 후 권장 보장액: {recommended} VND.",
    },
    "baby_securities": {
        "vi": "Danh mục đầu tư: {portfolio} VND. Giữ thanh khoản cho giai đoạn đầu.",
        "en": "Portfolio: {portfolio} VND. Keep liquid during the first year.",
        "ko": "포트폴리오: {portfolio} VND. 첫 해에는 유동성을 유지하세요.",
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

    if scenario_type == "career_change":
        new_income = float(parameters.get("new_income", monthly_income))
        delta = new_income - monthly_income
        additional_monthly = -delta  # negative delta becomes positive "extra" outflow pressure

        savings_balance = sum(
            a["balance"] for a in account_map.get("bank", [])
            if a["account_type"] == "savings" and a["balance"] > 0
        )
        entity_impacts.append(EntityImpact(
            entity="bank",
            summary=_line(
                "career_bank", language,
                before=_fmt(monthly_income),
                after=_fmt(new_income),
                delta=_fmt(delta),
                savings=_fmt(savings_balance),
            ),
            metrics={
                "income_before": monthly_income,
                "income_after": new_income,
                "income_delta": delta,
                "savings_balance": savings_balance,
            },
        ))

        finance_debt = sum(
            abs(a["balance"]) for a in account_map.get("finance", [])
            if a["balance"] < 0
        )
        entity_impacts.append(EntityImpact(
            entity="finance",
            summary=_line("career_finance", language, debt=_fmt(finance_debt)),
            metrics={"existing_debt": finance_debt},
        ))

        insurance_coverage = sum(
            a["balance"] for a in account_map.get("life", [])
            if a["balance"] > 0
        )
        entity_impacts.append(EntityImpact(
            entity="life",
            summary=_line("career_life", language, coverage=_fmt(insurance_coverage)),
            metrics={"current_coverage": insurance_coverage},
        ))

    elif scenario_type == "new_baby":
        # Representative baseline for a newborn's first-year cost in VND
        # (formula, medical, childcare) — overridable via parameters.
        monthly_baby_cost = float(parameters.get("monthly_cost", 8_000_000))
        additional_monthly = monthly_baby_cost

        savings_balance = sum(
            a["balance"] for a in account_map.get("bank", [])
            if a["account_type"] == "savings" and a["balance"] > 0
        )
        # Emergency buffer target: 6× monthly outflow (existing + baby cost).
        buffer_target = 6 * (existing_monthly_debt + monthly_baby_cost)
        buffer_gap = max(0.0, buffer_target - savings_balance)
        entity_impacts.append(EntityImpact(
            entity="bank",
            summary=_line(
                "baby_bank", language,
                cost=_fmt(monthly_baby_cost),
                savings=_fmt(savings_balance),
                buffer_gap=_fmt(buffer_gap),
            ),
            metrics={
                "monthly_cost": monthly_baby_cost,
                "savings_balance": savings_balance,
                "buffer_target": buffer_target,
                "buffer_gap": buffer_gap,
            },
        ))

        insurance_coverage = sum(
            a["balance"] for a in account_map.get("life", [])
            if a["balance"] > 0
        )
        recommended_coverage = max(monthly_income * 60, 500_000_000)
        entity_impacts.append(EntityImpact(
            entity="life",
            summary=_line(
                "baby_life", language,
                coverage=_fmt(insurance_coverage),
                recommended=_fmt(recommended_coverage),
            ),
            metrics={
                "current_coverage": insurance_coverage,
                "recommended_coverage": recommended_coverage,
            },
        ))

        portfolio_value = sum(
            a["balance"] for a in account_map.get("securities", [])
            if a["balance"] > 0
        )
        entity_impacts.append(EntityImpact(
            entity="securities",
            summary=_line("baby_securities", language, portfolio=_fmt(portfolio_value)),
            metrics={"portfolio_value": portfolio_value},
        ))

    elif scenario_type == "home_purchase":
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

    combined_summary = _line(
        "combined", language,
        before=_fmt(cashflow_before), after=_fmt(cashflow_after),
    )

    # Gate every user-facing line through compliance so a template edit
    # can't leak advice-shaped copy past the filter. Templates here are
    # authored as INFORMATION; the gate is a defence-in-depth pass.
    gated_combined, _ = apply_compliance(combined_summary, language=language)
    gated_flags = [apply_compliance(f, language=language)[0] for f in risk_flags]
    for impact in entity_impacts:
        impact.summary, _ = apply_compliance(impact.summary, language=language)

    return ScenarioResult(
        customer_id=customer_id,
        scenario_type=scenario_type,
        entity_impacts=entity_impacts,
        combined_summary=gated_combined,
        monthly_cashflow_before=round(cashflow_before),
        monthly_cashflow_after=round(cashflow_after),
        risk_flags=gated_flags,
    )
