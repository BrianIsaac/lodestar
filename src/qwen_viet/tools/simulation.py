"""Cross-entity financial scenario simulation — deterministic projections."""

import numpy_financial as npf

from qwen_viet.database import get_db
from qwen_viet.models import EntityImpact, ScenarioResult
from qwen_viet.tools.spending import compute_income_pattern


async def simulate_scenario(
    customer_id: str,
    scenario_type: str,
    parameters: dict,
) -> ScenarioResult:
    """Simulate a financial scenario across all Shinhan entities.

    Args:
        customer_id: Customer identifier.
        scenario_type: Type of scenario (e.g. ``home_purchase``).
        parameters: Scenario-specific parameters.

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
    entity_impacts = []
    risk_flags = []
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

        entity_impacts.append(EntityImpact(
            entity="bank",
            summary=f"Mortgage {loan_amount:,.0f} VND at {rate}% = {monthly_mortgage:,.0f}/month. Savings after down payment: {max(0, savings_balance - down_payment):,.0f}",
            metrics={
                "loan_amount": loan_amount,
                "monthly_payment": monthly_mortgage,
                "savings_remaining": max(0, savings_balance - down_payment),
            },
        ))

        finance_debt = sum(
            abs(a["balance"]) for a in account_map.get("finance", [])
            if a["balance"] < 0
        )
        entity_impacts.append(EntityImpact(
            entity="finance",
            summary=f"Existing consumer debt: {finance_debt:,.0f} VND. Consider clearing personal loan before mortgage.",
            metrics={"existing_debt": finance_debt},
        ))

        portfolio_value = sum(
            a["balance"] for a in account_map.get("securities", [])
            if a["balance"] > 0
        )
        liquidation_needed = max(0, down_payment - savings_balance)
        entity_impacts.append(EntityImpact(
            entity="securities",
            summary=f"Portfolio: {portfolio_value:,.0f} VND. Liquidation needed: {liquidation_needed:,.0f}",
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
            summary=f"Current coverage: {insurance_coverage:,.0f}. Recommended with mortgage: {recommended_coverage:,.0f}",
            metrics={
                "current_coverage": insurance_coverage,
                "recommended_coverage": recommended_coverage,
            },
        ))

    cashflow_after = cashflow_before - additional_monthly
    new_dti = (existing_monthly_debt + additional_monthly) / monthly_income if monthly_income > 0 else 1.0

    if new_dti > 0.50:
        risk_flags.append(f"DTI ratio at {new_dti:.0%} — above 50% comfort zone")
    if cashflow_after < monthly_income * 0.10:
        risk_flags.append("Remaining cashflow below 10% of income")

    return ScenarioResult(
        customer_id=customer_id,
        scenario_type=scenario_type,
        entity_impacts=entity_impacts,
        combined_summary=f"Monthly cashflow: {cashflow_before:,.0f} → {cashflow_after:,.0f} VND",
        monthly_cashflow_before=round(cashflow_before),
        monthly_cashflow_after=round(cashflow_after),
        risk_flags=risk_flags,
    )
