"""Backend-side translation dictionaries for chart and label strings.

Charts produced by deterministic Python tools (``tools/charts.py``,
``agents/workflows/scenario.py``) need their titles, summaries, axis
labels, and data labels rendered in all three supported locales so the
client can swap captions on language toggle without a round-trip. This
module holds the fixed-vocabulary translations so tools never need to
hit the LLM for routine strings.
"""

from __future__ import annotations

LANGS: tuple[str, str, str] = ("vi", "en", "ko")


# --- category labels ------------------------------------------------------

CATEGORY_LABELS: dict[str, dict[str, str]] = {
    "food": {"vi": "Ăn uống", "en": "Food", "ko": "식비"},
    "transport": {"vi": "Đi lại", "en": "Transport", "ko": "교통"},
    "shopping": {"vi": "Mua sắm", "en": "Shopping", "ko": "쇼핑"},
    "health": {"vi": "Sức khoẻ", "en": "Health", "ko": "건강"},
    "bills": {"vi": "Hoá đơn", "en": "Bills", "ko": "공과금"},
    "education": {"vi": "Giáo dục", "en": "Education", "ko": "교육"},
    "entertainment": {"vi": "Giải trí", "en": "Entertainment", "ko": "오락"},
    "salary": {"vi": "Lương", "en": "Salary", "ko": "급여"},
    "utilities": {"vi": "Tiện ích", "en": "Utilities", "ko": "공공요금"},
    "travel": {"vi": "Du lịch", "en": "Travel", "ko": "여행"},
    "other": {"vi": "Khác", "en": "Other", "ko": "기타"},
}


def localise_category(key: str, lang: str) -> str:
    """Translate a canonical category key (e.g. ``"food"``) to ``lang``.

    Unknown keys are returned unchanged — the LLM sometimes invents
    categories outside the canonical set, and echoing the raw token is
    better than substituting a confusing fallback.

    Args:
        key: Canonical category identifier, lower-case with underscores.
        lang: Target language code (``vi`` / ``en`` / ``ko``).

    Returns:
        Localised category label.
    """
    bundle = CATEGORY_LABELS.get(key.lower().strip())
    if not bundle:
        return key
    return bundle.get(lang, bundle["vi"])


def localise_categories(keys: list[str], lang: str) -> list[str]:
    """Translate a list of canonical category keys to ``lang``."""
    return [localise_category(k, lang) for k in keys]


# --- chart-specific strings ----------------------------------------------

CHART_STRINGS: dict[str, dict[str, str]] = {
    # Spending chart
    "chart.spending_title": {
        "vi": "Chi tiêu tháng {period}",
        "en": "Spending for {period}",
        "ko": "{period} 지출",
    },
    "chart.spending_summary": {
        "vi": "Tổng chi tiêu: {total:,.0f} {currency}",
        "en": "Total spending: {total:,.0f} {currency}",
        "ko": "총 지출: {total:,.0f} {currency}",
    },
    # Goal progress
    "chart.goal_summary": {
        "vi": "{pct:.0f}% hoàn thành — cần {need:,.0f} VND/tháng",
        "en": "{pct:.0f}% complete — need {need:,.0f} VND/month",
        "ko": "{pct:.0f}% 완료 — 월 {need:,.0f} VND 필요",
    },
    # Trend line chart
    "chart.trend_title": {
        "vi": "Xu hướng chi tiêu",
        "en": "Spending trend",
        "ko": "지출 추세",
    },
    "chart.axis_month": {"vi": "Tháng", "en": "Month", "ko": "월"},
    "chart.axis_amount_vnd": {
        "vi": "Số tiền (VND)",
        "en": "Amount (VND)",
        "ko": "금액 (VND)",
    },
    # Waterfall (cashflow)
    "chart.cashflow_title": {
        "vi": "Dòng tiền tháng này",
        "en": "Monthly cashflow",
        "ko": "월 현금흐름",
    },
    "chart.cashflow_summary": {
        "vi": "Thu nhập {income:,.0f} - Chi tiêu {spend:,.0f} = Còn lại {net:,.0f} {currency}",
        "en": "Income {income:,.0f} - Spending {spend:,.0f} = Remaining {net:,.0f} {currency}",
        "ko": "수입 {income:,.0f} - 지출 {spend:,.0f} = 잔액 {net:,.0f} {currency}",
    },
    # Scenario waterfall
    "chart.scenario_title": {
        "vi": "Kịch bản: {t}",
        "en": "Scenario: {t}",
        "ko": "시나리오: {t}",
    },
    "chart.scenario_summary": {
        "vi": "Dòng tiền: {b:,.0f} → {a:,.0f} VND",
        "en": "Cashflow: {b:,.0f} → {a:,.0f} VND",
        "ko": "현금흐름: {b:,.0f} → {a:,.0f} VND",
    },
    # Waterfall step labels
    "step.income": {"vi": "Thu nhập", "en": "Income", "ko": "수입"},
    "step.current_income": {
        "vi": "Thu nhập hiện tại",
        "en": "Current income",
        "ko": "현재 수입",
    },
    "step.remaining": {"vi": "Còn lại", "en": "Remaining", "ko": "잔액"},
    "step.entity_payment": {
        "vi": "{entity} trả hàng tháng",
        "en": "{entity} payment",
        "ko": "{entity} 월 지급액",
    },
}


def localise(key: str, lang: str, **kwargs: object) -> str:
    """Render a canonical chart string key in ``lang`` with the given kwargs.

    Args:
        key: Dotted key (e.g. ``"chart.spending_title"``).
        lang: Target language code.
        **kwargs: Format arguments applied via ``str.format_map``.

    Returns:
        Localised, formatted string. Falls back to Vietnamese when the
        target locale is missing.
    """
    bundle = CHART_STRINGS.get(key)
    if not bundle:
        return key
    template = bundle.get(lang) or bundle["vi"]
    try:
        return template.format(**kwargs)
    except (KeyError, IndexError):
        return template


def localise_triple(key: str, **kwargs: object) -> dict[str, str]:
    """Render a chart string into all three supported locales.

    Args:
        key: Dotted key.
        **kwargs: Format arguments.

    Returns:
        Dict with the ``vi``, ``en``, ``ko`` keys populated.
    """
    return {lang: localise(key, lang, **kwargs) for lang in LANGS}
