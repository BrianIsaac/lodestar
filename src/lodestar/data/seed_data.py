"""Generate and seed all synthetic data into SQLite."""

import asyncio

from lodestar.data.synthetic import (
    generate_transactions_for_customer,
    plant_life_event,
)
from lodestar.database import get_db, init_db

CUSTOMERS = [
    {
        "customer_id": "C001",
        "full_name": "Nguyễn Thị Hương",
        "date_of_birth": "1995-03-15",
        "gender": "F",
        "city": "Hà Nội",
        "income_monthly": 12_000_000,
        "segment": "mass",
        "life_events": [("baby", "2026-01")],
    },
    {
        "customer_id": "C002",
        "full_name": "Trần Văn Nam",
        "date_of_birth": "1990-07-22",
        "gender": "M",
        "city": "TP. Hồ Chí Minh",
        "income_monthly": 18_000_000,
        "segment": "mass_affluent",
        "life_events": [("home_purchase", "2025-11")],
    },
    {
        "customer_id": "C003",
        "full_name": "Lê Minh Tuấn",
        "date_of_birth": "1998-11-05",
        "gender": "M",
        "city": "Đà Nẵng",
        "income_monthly": 8_000_000,
        "segment": "mass",
        "life_events": [],
    },
    {
        "customer_id": "C004",
        "full_name": "Phạm Thị Mai",
        "date_of_birth": "1988-01-30",
        "gender": "F",
        "city": "Hà Nội",
        "income_monthly": 25_000_000,
        "segment": "affluent",
        "life_events": [("career_change", "2026-02")],
    },
    {
        "customer_id": "C005",
        "full_name": "Võ Đức Anh",
        "date_of_birth": "1993-09-12",
        "gender": "M",
        "city": "TP. Hồ Chí Minh",
        "income_monthly": 15_000_000,
        "segment": "mass_affluent",
        "life_events": [],
    },
]

ACCOUNTS_TEMPLATE = [
    {"entity": "bank", "account_type": "current", "balance_factor": 2.5},
    {"entity": "bank", "account_type": "savings", "balance_factor": 8.0},
    {"entity": "finance", "account_type": "credit_card", "balance_factor": -0.5},
    {"entity": "securities", "account_type": "portfolio", "balance_factor": 5.0},
    {"entity": "life", "account_type": "policy", "balance_factor": 1.0},
]


async def seed() -> None:
    """Generate all synthetic data and insert into the database."""
    await init_db()
    db = await get_db()

    try:
        for cust in CUSTOMERS:
            life_events = cust.pop("life_events")
            await db.execute(
                """INSERT OR REPLACE INTO customers
                   (customer_id, full_name, date_of_birth, gender, city,
                    income_monthly, segment)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    cust["customer_id"],
                    cust["full_name"],
                    cust["date_of_birth"],
                    cust["gender"],
                    cust["city"],
                    cust["income_monthly"],
                    cust["segment"],
                ),
            )

            primary_account_id = f"ACC-{cust['customer_id']}-001"
            for i, acct in enumerate(ACCOUNTS_TEMPLATE):
                account_id = f"ACC-{cust['customer_id']}-{i + 1:03d}"
                balance = cust["income_monthly"] * acct["balance_factor"]
                await db.execute(
                    """INSERT OR REPLACE INTO accounts
                       (account_id, customer_id, entity, account_type, balance)
                       VALUES (?, ?, ?, ?, ?)""",
                    (
                        account_id,
                        cust["customer_id"],
                        acct["entity"],
                        acct["account_type"],
                        balance,
                    ),
                )

            txns_df = generate_transactions_for_customer(
                customer_id=cust["customer_id"],
                account_id=primary_account_id,
                income_monthly=cust["income_monthly"],
                months=12,
            )

            for event_type, month in life_events:
                txns_df = plant_life_event(
                    txns_df,
                    customer_id=cust["customer_id"],
                    account_id=primary_account_id,
                    event=event_type,
                    month=month,
                )

            for _, row in txns_df.iterrows():
                await db.execute(
                    """INSERT OR REPLACE INTO transactions
                       (transaction_id, customer_id, account_id, date, amount,
                        category, merchant, description, entity)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        row["transaction_id"],
                        row["customer_id"],
                        row["account_id"],
                        row["date"],
                        row["amount"],
                        row.get("category"),
                        row.get("merchant"),
                        row.get("description", ""),
                        row.get("entity", "bank"),
                    ),
                )

        await db.commit()

        count = await db.execute("SELECT COUNT(*) FROM transactions")
        row = await count.fetchone()
        cust_count = await db.execute("SELECT COUNT(*) FROM customers")
        cust_row = await cust_count.fetchone()
        print(f"Seeded {cust_row[0]} customers with {row[0]} transactions")

    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(seed())
