"""Synthetic Vietnamese banking transaction generator."""

import random
import string
import uuid
from datetime import date, timedelta

import numpy as np
import pandas as pd
from faker import Faker

fake = Faker("vi_VN")

BANK_CODES = ["VCB", "TCB", "ACB", "BIDV", "MB", "TPB", "VPB", "STB", "SHB"]

MERCHANTS: dict[str, list[str]] = {
    "food": [
        "Grab Food", "ShopeeFood", "Pho 24", "Bún Chả Hương Liên",
        "Circle K", "Highland Coffee", "Phúc Long", "Lotteria",
        "Pizza 4P's", "Bún Đậu Mắm Tôm Hà Nội",
    ],
    "transport": [
        "Grab", "Be", "Xăng dầu Petrolimex", "VietJet Air",
        "Vietnam Airlines", "Xe buýt Hà Nội", "Mai Linh Taxi",
    ],
    "shopping": [
        "Shopee", "Lazada", "Thế Giới Di Động", "Uniqlo VN",
        "FPT Shop", "Bách Hoá Xanh", "Vinmart", "Zara VN",
    ],
    "bills": [
        "EVN Hà Nội", "Viettel", "VNPT", "Nước sạch Hà Nội",
        "FPT Telecom", "Mobifone", "VTVcab",
    ],
    "health": [
        "Bệnh viện Bạch Mai", "Nhà thuốc Long Châu", "Medicare VN",
        "Bệnh viện Vinmec", "Pharmacity",
    ],
    "entertainment": [
        "CGV Cinemas", "Netflix VN", "Spotify", "Galaxy Cinema",
    ],
    "education": [
        "Trung tâm Anh ngữ IELTS", "Coursera", "Udemy",
    ],
}

CATEGORY_WEIGHTS = {
    "food": 0.30,
    "transport": 0.12,
    "shopping": 0.20,
    "bills": 0.15,
    "health": 0.08,
    "entertainment": 0.08,
    "education": 0.07,
}

LIFE_EVENT_PATTERNS: dict[str, list[tuple[str, str, int]]] = {
    "baby": [
        ("health", "Bệnh viện Phụ sản Hà Nội", 5_000_000),
        ("shopping", "Kids Plaza", 2_000_000),
        ("shopping", "Con Cưng", 1_500_000),
        ("shopping", "Bibo Mart", 800_000),
    ],
    "home_purchase": [
        ("bills", "Công ty BĐS Vinhomes", 50_000_000),
        ("bills", "Nội thất IKEA VN", 15_000_000),
        ("shopping", "Điện máy XANH", 8_000_000),
    ],
    "career_change": [
        ("education", "Trung tâm Đào tạo Nghề", 3_000_000),
        ("food", "Coworking Space Up", 1_200_000),
    ],
}


def _generate_napas_description(merchant: str) -> str:
    """Generate a NAPAS-style transaction description.

    Args:
        merchant: Merchant name.

    Returns:
        Formatted NAPAS transfer description.
    """
    ref = "".join(random.choices(string.digits, k=10))
    bank = random.choice(BANK_CODES)
    return f"CT DEN {merchant} {bank} REF{ref}"


def _generate_amount(category: str) -> float:
    """Generate a realistic VND amount for a spending category.

    Args:
        category: Spending category key.

    Returns:
        Transaction amount in VND, rounded to nearest 1000.
    """
    distributions = {
        "food": (11.9, 1.1),
        "transport": (11.5, 0.8),
        "shopping": (12.5, 1.3),
        "bills": (12.0, 0.5),
        "health": (12.8, 1.0),
        "entertainment": (11.0, 0.7),
        "education": (13.0, 0.8),
    }
    mean, sigma = distributions.get(category, (12.0, 1.0))
    raw = np.random.lognormal(mean=mean, sigma=sigma)
    return round(raw / 1000) * 1000


def generate_salary(income_monthly: float, payday: int = 25) -> dict:
    """Generate a salary credit transaction template.

    Args:
        income_monthly: Monthly salary in VND.
        payday: Day of month salary is received.

    Returns:
        Transaction dict template (without date).
    """
    jitter = np.random.normal(0, income_monthly * 0.02)
    return {
        "amount": round(income_monthly + jitter),
        "category": "salary",
        "merchant": "Shinhan Bank Payroll",
        "description": f"CT DEN LUONG THANG {fake.bothify('##/####')}",
    }


def generate_transactions_for_customer(
    customer_id: str,
    account_id: str,
    income_monthly: float,
    months: int = 12,
    start_date: date | None = None,
) -> pd.DataFrame:
    """Generate synthetic transactions for a single customer.

    Args:
        customer_id: Customer identifier.
        account_id: Primary bank account ID.
        income_monthly: Monthly income in VND.
        months: Number of months of history to generate.
        start_date: First month start date; defaults to N months ago.

    Returns:
        DataFrame of transactions.
    """
    if start_date is None:
        start_date = date.today().replace(day=1) - timedelta(days=months * 30)

    rows = []
    categories = list(CATEGORY_WEIGHTS.keys())
    weights = list(CATEGORY_WEIGHTS.values())

    for m in range(months):
        month_start = start_date + timedelta(days=m * 30)

        salary = generate_salary(income_monthly)
        salary_day = min(25 + random.randint(-2, 2), 28)
        salary_date = month_start.replace(day=salary_day)
        rows.append({
            "transaction_id": str(uuid.uuid4()),
            "customer_id": customer_id,
            "account_id": account_id,
            "date": salary_date.isoformat(),
            "amount": salary["amount"],
            "category": "salary",
            "merchant": salary["merchant"],
            "description": salary["description"],
            "entity": "bank",
        })

        num_txns = random.randint(25, 45)
        for _ in range(num_txns):
            cat = random.choices(categories, weights=weights, k=1)[0]
            merchant = random.choice(MERCHANTS[cat])
            amount = _generate_amount(cat)
            day = random.randint(1, 28)
            txn_date = month_start.replace(day=day)

            rows.append({
                "transaction_id": str(uuid.uuid4()),
                "customer_id": customer_id,
                "account_id": account_id,
                "date": txn_date.isoformat(),
                "amount": -amount,
                "category": cat,
                "merchant": merchant,
                "description": _generate_napas_description(merchant),
                "entity": "bank",
            })

    return pd.DataFrame(rows)


def plant_life_event(
    df: pd.DataFrame,
    customer_id: str,
    account_id: str,
    event: str,
    month: str,
) -> pd.DataFrame:
    """Insert life event transaction patterns into synthetic data.

    Args:
        df: Existing transactions DataFrame.
        customer_id: Target customer.
        account_id: Customer's bank account.
        event: Event type key from LIFE_EVENT_PATTERNS.
        month: Target month as YYYY-MM.

    Returns:
        DataFrame with life event transactions appended.
    """
    patterns = LIFE_EVENT_PATTERNS.get(event, [])
    rows = []
    for cat, merchant, base_amount in patterns:
        amount = base_amount + np.random.randint(-500_000, 500_000)
        rows.append({
            "transaction_id": str(uuid.uuid4()),
            "customer_id": customer_id,
            "account_id": account_id,
            "date": f"{month}-15",
            "amount": -abs(amount),
            "category": cat,
            "merchant": merchant,
            "description": _generate_napas_description(merchant),
            "entity": "bank",
        })
    return pd.concat([df, pd.DataFrame(rows)], ignore_index=True)
