# Lodestar — AI Personal Financial Coach

**An autonomous AI financial coach PoC for Shinhan Bank Vietnam's SOL app, built for Innoboost 2026.**

The name reflects the product's role: a guiding star for customers navigating their financial lives — surfacing the right signals at the right time, grounded in Shinhan's product catalogue, compliant with Vietnamese advisory regulations, and learning from every interaction.

---

## The Problem

Shinhan Bank Vietnam's SOL app serves ~2M customers with standard mobile banking features — no AI advisory, no personalised insights, no proactive guidance. This is true across the whole Vietnamese market: no consumer-grade AI financial coach exists there.

- Vietnam scores **12 / 21** on the OECD financial literacy index (bottom quartile globally)
- **33%** of Vietnamese consumers cite inability to save as their top financial anxiety
- Only **~20%** of Gen Z proactively save for retirement despite being 25% of the labour force
- **68%** of digital interactions on SOL are limited to balance checks — cross-sell conversion is minimal
- **~50%** of customers split their finances across three or more banks because no single bank delivers personalised value

Customers need something that sees what's happening in their financial life, explains it in their language, and nudges them towards the right Shinhan product at the right moment — without pretending to be a licensed financial advisor.

## The Solution

Lodestar is **not a chatbot**. It's an **autonomous agent** that:

1. Watches customer transactions in real time.
2. Reasons with an LLM about whether each new transaction is worth surfacing — using 10 rule-based sensors as callable tools rather than auto-firing thresholds.
3. Composes insight cards in Vietnamese, English, and Korean at write time (zero-latency language toggle).
4. Routes each card to concrete actions in Shinhan's own catalogue — savings goals, product recommendations, drill-down coaching chat.
5. **Learns from every customer engagement** — dismissals, chats, and goal creations feed a per-customer journal that the next agent run reads back as memory.

The whole stack runs on **Qwen** (local Ollama for dev, Alibaba DashScope `qwen-plus` for cloud) behind a one-line env var, FastAPI + Next.js for the app, Qdrant + bge-m3 for multilingual product retrieval, and SQLite for persistent state.

## Hero Moments

**1. The agent stays silent when nothing happened.**
Inject a Highland Coffee 85K transaction → backend log reads *"Detector stayed silent: single coffee purchase with no detectable anomaly."* No notification, no noise. That judgement call is the thing templates can't do.

**2. It synthesises across signals instead of spamming.**
Three baby-related transactions (Kids Plaza 2.1M, Con Cưng 1.8M, Hanoi Obstetrics Hospital 3.5M) produce one richer card — *"Large medical expense and baby event signal — 3.5M VND at Hanoi Obstetrics Hospital combined with 7 recent transactions indicating a baby event."* The agent called the life-event sensor, the large-outflow sensor, and the transaction-summary helper, then wrote the card itself.

**3. Cross-entity financial simulation across all four Shinhan subsidiaries.**
One click on "What if I buy a 2B VND home" computes the impact across Bank (mortgage at 7.5%), Consumer Finance (existing debt that should be cleared first), Securities (liquidation needed from portfolio), and Life Insurance (coverage gap vs. recommended). This is the differentiator vs. any single-entity competitor.

**4. The agent remembers.**
Engage with a card via the chat chip → the reflection pipeline runs, the engagement is recorded as an `earned_reward` quadrant outcome, a lesson crystallises into the learning journal with bge-m3 embeddings. Inject a different transaction on the same customer later → backend log reads `lessons_applied=1`, and the new card's title references the remembered context ("Large Purchase and Childbirth Expense Goal"). This is Van Tharp's process/outcome separation running live.

**5. Tri-lingual from the first authored token.**
Toggle Vi → En → Ko in the header; every card, hint, chip, nav label, and disclaimer flips instantly because the detector writes all three locales in a single structured-output call. Works for on-card content AND UI chrome AND chat replies.

---

## Architecture

### Request paths

```
Customer event (transaction)
        │
        ▼
┌───────────────────────────────────────────────────────┐
│  POST /demo/transaction                               │
│   • insert transaction row                            │
│   • return 200 immediately (agent_pending: true)      │
│   • fire analyze_transaction in the background        │
└───────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────┐
│  LodestarDetector — agents/detector.py                │
│                                                       │
│  1. fetch top-3 relevant CustomerLessons for this     │
│     customer (semantic similarity against the new tx) │
│     → inject as "Prior learnings" memory block        │
│                                                       │
│  2. tool-call loop (up to 4 turns, 120s per turn):    │
│     - 10 rule sensors (velocity_anomaly, life_event,  │
│       large_outflow, first_time_merchant, …)          │
│     - 2 context helpers (profile, recent summary)     │
│     LLM picks which tools to call, when, and how many │
│                                                       │
│  3. final turn forces JSON response_format — one      │
│     structured object with title/summary/hints/chips  │
│     in Vi+En+Ko                                       │
│                                                       │
│  4. compliance filter per locale → insight stored +   │
│     interactions row recorded with full reasoning     │
│     trace (tools_used, lessons_applied)               │
└───────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────┐
│  SSE /stream/{customer_id}                            │
│   • diff-only delivery (per-connection seen set)      │
│   • carries title_i18n, summary_i18n, action_hint_i18n│
│     quick_prompts_i18n                                │
│   • frontend flash-pulses new cards as they arrive    │
└───────────────────────────────────────────────────────┘
```

### Learning loop

```
Insight card shown
        │
        ├── customer dismisses ────────▶ reflection(process=good, outcome=bad)
        │                                    │
        │                                    ▼ "bad_luck" quadrant
        │                                 dampening lesson stored
        │
        └── customer chats about it ──▶ reflection(process=good, outcome=good)
                                             │
                                             ▼ "earned_reward" quadrant
                                          reinforcing lesson stored
                                             │
                                             ▼
                                      aggregate_to_cohort()
                                      {city}_{segment} bucket
                                      (PII-stripped, k=5 threshold)
                                             │
                                             ▼
                              next analyze_transaction()
                              reads the lesson back via
                              bge-m3 semantic retrieval
```

### Orchestrator (drill-down chat)

`agents/orchestrator.py` handles the `/chat/{insight_id}` and `/chat` endpoints. It's a separate Qwen tool-calling loop with three workflow tools:

- `spending_analysis` → `tools/spending.py` + `agents/workflows/spending.py`
- `product_search` → `tools/products.py` (Qdrant + bge-m3 RAG) + `agents/workflows/product_match.py`
- `scenario_simulation` → `tools/simulation.py` (cross-entity math) + `agents/workflows/scenario.py`

Every response passes through `agents/compliance.py` which classifies the output and appends the required Vi/En/Ko disclaimer for anything that could be read as advice.

### Data layer (SQLite)

Nine tables, all in one file `data/coach.db`:

| Table | Role |
|---|---|
| `customers` / `accounts` / `transactions` | Seeded synthetic 5-customer dataset, 12 months |
| `insight_cards` | Agent-produced cards with per-locale JSON blobs |
| `goals` | Savings goals created via the `plan` chip |
| `interactions` | Each card's event + reasoning + card timeline, appended by chat/dismiss |
| `reflections` | Van Tharp process/outcome grading per interaction |
| `lessons` | Per-customer learnings with bge-m3 embedding, confidence, evolution counter |
| `cohort_insights` | Anonymised patterns keyed by `{city}_{segment}` |

---

## Key Features

### 1. Agentic detector (not rules + LLM-pretty-print)
Rules are tools the LLM *chooses* to call, not triggers that auto-emit cards. The LLM decides whether to surface anything, which sensors to consult, and writes the entire card itself — title, summary, hint bullets, and quick-prompt chips — in a single structured-output call in three languages. No hand-authored templates in the hot path.

### 2. Tri-lingual by construction
All card content is written in Vi/En/Ko at detection time and stored as per-locale JSON on the card row. UI toggle is an instant client-side flip. The i18n is also applied to:
- Every UI string (navigation, dialog, hero, compliance banner)
- Chat replies (orchestrator is locale-aware)
- Product catalogue (Shinhan products carry name/description in all three)
- RAG embeddings (Vi+En+Ko concatenated into a single indexed document so Korean queries still rank Shinhan products correctly)

### 3. Cross-entity scenario simulator
`POST /simulate` runs a closed-form math model (not an LLM guess) across all four Shinhan subsidiaries. Example output for "buy a 2B VND home":
- **Bank**: Mortgage 1.6B @ 7.5% = 12.9M/month; savings after down payment: 0
- **Consumer Finance**: Existing consumer debt 6M VND — consider clearing before mortgage
- **Securities**: Portfolio 60M VND — liquidation needed: 304M
- **Life Insurance**: Current coverage 12M — recommended with mortgage: 2.4B
- Risk flags: DTI 111% (above 50% comfort zone), remaining cashflow < 10% of income

### 4. Quick-prompt action chips
Three chip types per card, each typed and routed:

| Action | Frontend behaviour | Backend |
|---|---|---|
| `chat` | Opens `/insight/{id}` drill-down, auto-sends the prompt | Orchestrator with `insight_context` |
| `plan` | `?tab=plan&goal_name=…&goal_amount=…&goal_months=…` pre-fills new-goal dialog | `POST /goals` on save |
| `products` | `?tab=products&q=…` pre-fills search | `GET /products/search` with multilingual RAG |

The detector agent is given a Shinhan product map in its system prompt so `products` chips always route to real catalogue items (education insurance → Shinhan Edu Care, cashback → Shinhan Cashback Card, etc.).

### 5. Per-customer learning journal
- **Lessons** carry bge-m3 embeddings (1024-dim), confidence ∈ [0,1], importance ∈ [1,10], supporting months, and an evolution counter that increments when a new lesson's embedding is cosine-similar (>0.85) to an existing one.
- **Reflections** grade every interaction on Van Tharp's process × outcome axes. Only `earned_reward` and `just_desserts` quadrants extract lessons — a lucky good outcome doesn't teach the system false patterns.
- **Cohort aggregation** rolls anonymised lessons into a `{city}_{segment}` bucket with a 5-customer threshold before a cohort insight becomes retrievable. No names, DOBs, or account IDs leave the per-customer layer.

### 6. Demo controls
- **Simulate panel** with preset transactions (everyday / life event / anomaly / income+home) and a custom form
- **Reset demo** button wipes cards, demo transactions, goals, lessons, reflections for one customer — baseline history preserved
- **`GET /memory/{customer_id}`** exposes the live learning state for demo narration and operational inspection

### 7. Compliance layer
`agents/compliance.py` classifies every outbound text as `information`, `generic_advice`, or `personalised_advice` and gates the last two behind the regulated disclaimer in each locale. Refusal patterns catch anything that looks like personalised investment instructions. Banner rendered on the feed is load-bearing, not decorative.

---

## Stack

**Backend**
- Python 3.11+, FastAPI, aiosqlite
- Qwen via OpenAI-compatible API — local Ollama (`qwen3:14b`) for dev, Alibaba DashScope (`qwen-plus`) for cloud. One env var switch.
- Qdrant (embedded) + `bge-m3` sentence-transformers for multilingual RAG over the Shinhan product catalogue
- SDV + Faker for synthetic 12-month transaction generation per customer

**Frontend**
- Next.js 16 (App Router) + React 19
- shadcn/ui v4 on the `base-nova` style with `@base-ui` primitives
- Tailwind v4 with OKLCH tokens; Shinhan Blue `#0046FF` as the primary
- SSE (diff-only) for live insight streaming
- Custom i18n provider with localStorage persistence

**LLM inference**
- Local: Ollama on GPU (`qwen3:14b`), ~5-15s per card
- Cloud: DashScope `qwen-plus`, ~2-5s per card
- Env-driven: `COACH_LLM_BASE_URL`, `COACH_LLM_MODEL`, `COACH_LLM_API_KEY`

**Deployment**
- Alibaba Cloud ECS (Ubuntu 22.04) via Docker Compose — see [DEPLOY.md](DEPLOY.md)

---

## Quick Start

### Prerequisites
- `uv` for Python package management
- Node 20+ and `npm`
- Either Ollama running locally with `qwen3:14b` pulled, OR a DashScope API key

### 1. Install

```bash
uv sync
uv sync --extra dev
cd frontend && npm install && cd ..
```

### 2. Seed synthetic data (first run only)

```bash
uv run python -m lodestar.data.seed_data
```

Creates 5 Vietnamese customers in Hanoi / HCMC / Da Nang across mass / mass_affluent / affluent segments, 12 months of transactions each, with planted life events (baby, home purchase, career change).

### 3. Configure the LLM

```bash
cp .env.example .env
# Edit .env — defaults work for local Ollama.
# For DashScope, uncomment the three DashScope lines.
```

### 4. Run tests

```bash
uv run pytest
```

78 tests across detector, triggers, compliance, RAG, learning journal, cohort aggregation, and API endpoints.

### 5. Start backend

```bash
CUDA_VISIBLE_DEVICES=0 uv run uvicorn lodestar.api:app --port 8000
```

Feed is empty on every boot — the agent only produces cards in response to live events.

### 6. Start frontend

```bash
cd frontend
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

Open `http://localhost:3000/?demo=1` — the `demo=1` flag surfaces the Simulate button.

---

## API Reference

| Method + Path | Purpose |
|---|---|
| `GET /feed/{customer_id}?language=…` | Ranked, non-dismissed insight cards |
| `GET /stream/{customer_id}` | SSE stream, diff-only on new insights |
| `POST /dismiss/{insight_id}` | Dismiss + record bad_luck reflection |
| `POST /chat/{insight_id}` | Scoped drill-down chat + earned_reward reflection |
| `POST /chat` | Unscoped chat |
| `POST /simulate` | Cross-entity scenario math |
| `GET /goals/{customer_id}` / `POST /goals` | Savings goals CRUD |
| `GET /products/search?query=&language=` | Multilingual RAG over the Shinhan catalogue |
| `GET /transactions/{customer_id}?limit=` | Recent-activity strip feed |
| `POST /demo/transaction` | Inject a synthetic transaction, fire the detector |
| `POST /demo/reset/{customer_id}` | Wipe ephemeral state, keep baseline |
| `GET /memory/{customer_id}` | Dump the agent's learning journal (lessons + reflections + cohort aggregates) |
| `GET /health` | Liveness + customer count |

---

## Project Structure

```
lodestar/
├── src/lodestar/
│   ├── api.py                      # FastAPI endpoints
│   ├── config.py                   # Pydantic settings, env-driven
│   ├── database.py                 # SQLite schema
│   ├── models/                     # Pydantic data models (insight, learning, products, customer)
│   ├── data/                       # Synthetic data generators + Shinhan product catalogue JSON
│   ├── tools/                      # Deterministic financial calculators (spending, goals, charts, products, simulation)
│   ├── rag/                        # Qdrant indexer + bge-m3 embeddings
│   ├── agents/
│   │   ├── detector.py             # Agentic insight generator — THE centrepiece
│   │   ├── orchestrator.py         # Chat orchestrator with workflow tools
│   │   ├── compliance.py           # Classification + locale-aware disclaimers
│   │   ├── triggers.py             # 10 deterministic rule sensors (tools, not auto-firing)
│   │   ├── background.py           # Insight persistence helper
│   │   └── workflows/              # Spending / goals / product-match / scenario subgraphs
│   └── learning/
│       ├── journal.py              # Per-customer lessons with semantic dedup/evolution
│       ├── reflection.py           # Van Tharp process/outcome grading
│       ├── cohort.py               # Federated cross-customer aggregation
│       └── interactions.py         # Event → reasoning → card timeline ledger
├── frontend/
│   └── src/
│       ├── app/page.tsx            # Tabs (feed/plan/products) + layout + language + demo mode
│       ├── components/
│       │   ├── insight-feed.tsx    # SSE-driven live feed with "Coach is analysing…" skeleton
│       │   ├── insight-card.tsx    # Card with locale-aware title/summary/hints + typed chips
│       │   ├── demo-panel.tsx      # Preset injections + reset
│       │   ├── goals-view.tsx      # Plan tab: goals + scenario simulator
│       │   ├── product-search.tsx  # Products tab: multilingual RAG search
│       │   ├── drill-down-chat.tsx # /insight/{id} chat with tool-use bubbles
│       │   └── …
│       └── lib/
│           ├── api.ts              # Typed FastAPI client
│           ├── i18n.tsx            # Vi/En/Ko strings + LanguageProvider
│           └── use-sse.ts          # Live insight stream hook
├── tests/                          # 78 tests (pytest async)
├── docs/                           # Screenshots + narration notes
├── plans/                          # Architecture decisions + backlog
├── Dockerfile                      # Multi-stage backend + frontend
├── docker-compose.yml              # ECS deployment
├── DEPLOY.md                       # Alibaba Cloud ECS + DashScope setup
├── .env.example                    # Backend LLM config template
├── pyproject.toml
└── LICENSE                         # Apache 2.0
```

---

## Status & Roadmap

**What's real in this PoC**
- Agentic detector with 10 tool-sensors + 2 context helpers, memory injection, reasoning trace
- Learning loop fully wired: lessons → reflections → cohort, with `/memory` inspection endpoint
- Cross-entity scenario math for the home-purchase case
- Tri-lingual authoring end-to-end
- Multilingual RAG over 21 Shinhan products across 4 entities
- Compliance filter per locale
- Live SSE streaming with diff-only delivery
- Playwright-verified demo flow

**Roadmap for a production deploy**
- Additional scenario templates (retirement, career change, education planning) — calculator modules are in place, needs UI wiring
- Real transaction ingestion from core banking (today we simulate via `/demo/transaction`)
- LLM-driven reflection grading (today's heuristic uses rule-based process/outcome)
- Multi-customer cohort backfill (the aggregator needs ≥5 supporters per pattern before surfacing; needs a data seeding pass)
- Mobile SDK wrap for in-SOL-app embedding

---

## Deployment

Live demo on Alibaba Cloud ECS:

- Frontend: <http://43.98.179.20:3000>
- Backend API: <http://43.98.179.20:8000>

See [DEPLOY.md](DEPLOY.md) for the full setup, DashScope configuration, and update workflow.

---

## License

Apache License 2.0 — see [LICENSE](LICENSE).
