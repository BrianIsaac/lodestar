"""SQLite database schema and connection helpers."""

import aiosqlite

from lodestar.config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    full_name TEXT NOT NULL,
    date_of_birth TEXT,
    gender TEXT,
    city TEXT,
    income_monthly REAL,
    segment TEXT DEFAULT 'mass',
    language TEXT DEFAULT 'vi',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS accounts (
    account_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    entity TEXT NOT NULL,
    account_type TEXT NOT NULL,
    balance REAL DEFAULT 0,
    currency TEXT DEFAULT 'VND',
    as_of TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    account_id TEXT NOT NULL REFERENCES accounts(account_id),
    date TEXT NOT NULL,
    amount REAL NOT NULL,
    currency TEXT DEFAULT 'VND',
    category TEXT,
    merchant TEXT,
    description TEXT DEFAULT '',
    entity TEXT DEFAULT 'bank'
);

CREATE TABLE IF NOT EXISTS goals (
    goal_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    name TEXT NOT NULL,
    target_amount REAL NOT NULL,
    current_amount REAL DEFAULT 0,
    target_date TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS lessons (
    lesson_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    conditions TEXT,
    insight TEXT,
    error_type TEXT DEFAULT 'missed_factor',
    confidence REAL DEFAULT 0.5,
    importance REAL DEFAULT 5.0,
    times_evolved INTEGER DEFAULT 0,
    supporting_months TEXT DEFAULT '[]',
    embedding BLOB,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reflections (
    reflection_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    interaction_id TEXT NOT NULL,
    process_grade TEXT,
    outcome_quality TEXT,
    quadrant TEXT,
    lesson_extracted INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cohort_insights (
    cohort_key TEXT NOT NULL,
    pattern_type TEXT NOT NULL,
    category TEXT,
    insight TEXT,
    confidence REAL DEFAULT 0.5,
    supporting_count INTEGER DEFAULT 0,
    effectiveness REAL DEFAULT 0.0,
    PRIMARY KEY (cohort_key, pattern_type)
);

CREATE TABLE IF NOT EXISTS insight_cards (
    insight_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    title TEXT NOT NULL,
    summary TEXT,
    title_i18n TEXT,            -- JSON {"vi":"...","en":"...","ko":"..."}
    summary_i18n TEXT,          -- JSON {"vi":"...","en":"...","ko":"..."}
    action_hint_i18n TEXT,      -- JSON {"vi":[...],"en":[...],"ko":[...]}
    quick_prompts_i18n TEXT,    -- JSON {"vi":[{text,action,params}], ...}
    severity TEXT DEFAULT 'info',
    chart_spec TEXT,
    suggested_actions TEXT DEFAULT '[]',
    compliance_class TEXT DEFAULT 'information',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    dismissed INTEGER DEFAULT 0,
    priority_score REAL DEFAULT 0.0
);

CREATE TABLE IF NOT EXISTS interactions (
    interaction_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    insight_id TEXT REFERENCES insight_cards(insight_id),
    messages TEXT DEFAULT '[]',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS translation_cache (
    source_text TEXT NOT NULL,
    target_lang TEXT NOT NULL,
    translated_text TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (source_text, target_lang)
);

CREATE INDEX IF NOT EXISTS idx_transactions_customer ON transactions(customer_id, date);
CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(customer_id, category);
CREATE INDEX IF NOT EXISTS idx_insight_cards_customer ON insight_cards(customer_id, dismissed, priority_score DESC);
CREATE INDEX IF NOT EXISTS idx_lessons_customer ON lessons(customer_id);
"""


async def get_db() -> aiosqlite.Connection:
    """Open a connection to the SQLite database.

    Returns:
        An aiosqlite connection with row_factory enabled.
    """
    settings.ensure_dirs()
    db = await aiosqlite.connect(settings.db_path)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    return db


async def init_db() -> None:
    """Create all tables if they do not exist, then run idempotent
    column-level migrations for databases created before multilingual
    support was added."""
    db = await get_db()
    try:
        await db.executescript(SCHEMA)
        for stmt in (
            "ALTER TABLE insight_cards ADD COLUMN title_i18n TEXT",
            "ALTER TABLE insight_cards ADD COLUMN summary_i18n TEXT",
            "ALTER TABLE insight_cards ADD COLUMN action_hint_i18n TEXT",
            "ALTER TABLE insight_cards ADD COLUMN quick_prompts_i18n TEXT",
        ):
            try:
                await db.execute(stmt)
            except Exception:
                # Column already exists — SQLite raises OperationalError.
                pass
        await db.commit()
    finally:
        await db.close()
