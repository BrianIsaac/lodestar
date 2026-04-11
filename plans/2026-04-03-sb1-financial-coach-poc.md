# SB1: AI Personal Financial Coach — Implementation Plan

## Overview

Build the PoC for an autonomous AI financial coach embedded in Shinhan SOL Vietnam. The system runs Qwen3-8B (Q4_K_M) on a local 12GB GPU, with a FastAPI backend and Next.js + shadcn/ui frontend deployed on Vercel. It demonstrates proactive insight generation, drill-down chat, cross-entity scenario simulation, and a per-customer learning loop — all using synthetic Vietnamese banking data.

## Current State

- **Exists:** 17 research docs, master doc, pyproject.toml with all dependencies declared, .venv with openpyxl only
- **Does not exist:** Any application code, database schema, synthetic data, frontend, tests
- **External dependency:** Qwen3-8B-Q4_K_M.gguf model file + llama-server (user must download/install separately)

## Desired End State

A working demo where:
1. A background agent polls synthetic transaction data and generates ranked insight cards
2. A Next.js frontend displays the insight feed styled in Shinhan blue (#0046FF)
3. Tapping a card opens a scoped chat thread with inline Recharts visualisations
4. Users can ask "What if I buy a house?" and see a cross-entity simulation
5. The learning loop stores per-customer lessons that improve future responses
6. All outputs pass through a compliance filter before delivery

### Verification

- `uv run pytest` passes all tests
- `uv run uvicorn src.lodestar.api:app` starts the backend on port 8000
- `llama-server --model Qwen3-8B-Q4_K_M.gguf --ctx-size 32768 --port 8080` serves the LLM
- Frontend on Vercel connects to the API and renders the insight feed
- A full demo scenario (generate insights → view feed → drill down → simulate scenario → see learning update) completes end-to-end

## What We're NOT Doing

- Real core banking API integration (all data is synthetic)
- Voice interaction
- Investment recommendations (regulatory constraint)
- Real-time streaming infrastructure (polling loop simulates streaming)
- Fine-tuning Qwen3 (base model only for PoC; fine-tuning guide is in docs for future)
- Native mobile app (web demo only)
- Production deployment, auth, rate limiting

## Project Structure

```
lodestar/
├── src/lodestar/
│   ├── __init__.py
│   ├── api.py                      # FastAPI app, all endpoints
│   ├── config.py                   # Settings via pydantic-settings
│   ├── database.py                 # SQLite schema, connection helpers
│   ├── models/
│   │   ├── __init__.py
│   │   ├── customer.py             # CustomerProfile, AccountBalance, etc.
│   │   ├── insight.py              # InsightCard, ChartSpec, etc.
│   │   ├── learning.py             # CustomerLesson, CustomerReflection
│   │   └── products.py             # ProductInfo, EligibilityResult, etc.
│   ├── data/
│   │   ├── __init__.py
│   │   ├── synthetic.py            # SDV/Faker transaction generator
│   │   ├── products_catalogue.json # Shinhan product data (static)
│   │   └── seed_data.py            # Generate and seed all synthetic data
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── spending.py             # compute_spending_summary, categorise, anomalies
│   │   ├── goals.py                # project_completion, savings_rate, affordability
│   │   ├── charts.py               # generate_spending_chart, goal_progress_chart
│   │   ├── simulation.py           # cross-entity scenario projection
│   │   └── products.py             # RAG search, compare, eligibility
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── embeddings.py           # BGEM3FlagModel wrapper
│   │   ├── indexer.py              # Qdrant collection setup + product ingestion
│   │   └── retriever.py            # Hybrid search (dense + sparse + RRF)
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── orchestrator.py         # Qwen-Agent reactive orchestrator
│   │   ├── background.py           # Polling trigger loop
│   │   ├── triggers.py             # Deterministic trigger rules (Python, no LLM)
│   │   ├── compliance.py           # Compliance filter agent
│   │   └── workflows/
│   │       ├── __init__.py
│   │       ├── spending.py         # LangGraph spending analysis subgraph
│   │       ├── goals.py            # LangGraph goal tracking subgraph
│   │       ├── product_match.py    # LangGraph product search subgraph
│   │       └── scenario.py         # LangGraph cross-entity simulation subgraph
│   ├── learning/
│   │   ├── __init__.py
│   │   ├── journal.py              # CustomerLearningJournal (store, retrieve, evolve)
│   │   ├── reflection.py           # Reflect on interaction quality
│   │   └── cohort.py               # Federated cohort insight aggregation
│   └── nlp/
│       ├── __init__.py
│       └── vietnamese.py           # underthesea normalisation, entity extraction
├── frontend/                       # Next.js app (separate package.json)
│   ├── package.json
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   ├── globals.css                 # Shinhan OKLCH theming
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx                # Insight feed (default tab)
│   │   ├── goals/page.tsx
│   │   ├── products/page.tsx
│   │   └── insight/[id]/page.tsx   # Drill-down chat view
│   ├── components/
│   │   ├── insight-card.tsx
│   │   ├── insight-feed.tsx
│   │   ├── drill-down-chat.tsx
│   │   ├── chart-renderer.tsx      # Renders ChartSpec JSON via Recharts
│   │   └── scenario-view.tsx
│   └── lib/
│       ├── api.ts                  # FastAPI client
│       └── use-sse.ts              # EventSource hook
├── tests/
│   ├── __init__.py
│   ├── test_tools.py               # Deterministic tool correctness
│   ├── test_rag.py                 # Qdrant hybrid search
│   ├── test_triggers.py            # Trigger rule detection
│   ├── test_learning.py            # Journal store/retrieve/evolve
│   └── test_api.py                 # FastAPI endpoint integration
├── plans/                          # This file
├── docs/                           # Research docs (existing)
├── pyproject.toml                  # (existing)
└── .streamlit/                     # REMOVED — using Next.js now
```

---

## Phase 1: Foundation

### Overview
Project structure, Pydantic models, database schema, synthetic data generation. Everything downstream depends on this.

### Changes Required:

#### 1. Project structure
Create the directory tree above. All `__init__.py` files.

#### 2. Configuration (`src/lodestar/config.py`)
Pydantic-settings based config:
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    llm_base_url: str = "http://localhost:8080/v1"
    llm_model: str = "qwen3-8b"
    db_path: str = "data/coach.db"
    qdrant_path: str = "data/qdrant"
    embedding_model: str = "BAAI/bge-m3"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    class Config:
        env_prefix = "COACH_"
```

#### 3. Pydantic models (`src/lodestar/models/`)
All typed models from the docs:

**`customer.py`**: `CustomerProfile`, `AccountBalance`, `Transaction`, `IncomePattern`, `DebtSummary`, `NetWorth`

**`insight.py`**: `InsightCard`, `ChartSpec`, `InsightFeed`, `ChatMessage`, `ChatResponse`

**`learning.py`**: `CustomerLesson`, `CustomerReflection`, `CohortInsight` (from doc 09)

**`products.py`**: `ProductInfo`, `ProductFilters`, `EligibilityResult`, `ComparisonTable`, `ScenarioRequest`, `ScenarioResult`

#### 4. Database schema (`src/lodestar/database.py`)
SQLite via aiosqlite. Tables: `customers`, `transactions`, `accounts`, `goals`, `lessons`, `reflections`, `cohort_insights`, `insight_cards`, `interactions`.

#### 5. Synthetic data (`src/lodestar/data/`)
- `synthetic.py`: Vietnamese merchant taxonomy, NAPAS descriptions, life event planting (from doc 14 code)
- `products_catalogue.json`: ~50 Shinhan products across 4 entities with metadata
- `seed_data.py`: Generate 5-10 customer profiles with 12 months of transactions, cross-entity data, and planted life events

### Success Criteria:

#### Automated Verification:
- [x] `uv sync` installs all dependencies without conflict
- [x] `uv run python -c "from lodestar.models import *"` imports cleanly
- [x] `uv run python -m lodestar.data.seed_data` generates synthetic data and seeds the SQLite DB (5 customers, 2118 transactions)
- [x] `uv run pytest tests/test_tools.py` — 16/16 model tests pass
- [x] `uv run ruff check src/` passes linting

#### Manual Verification:
- [x] Inspect generated transaction data — NAPAS format confirmed (`CT DEN [merchant] [bank] REF[digits]`), realistic amounts (food avg 273K, shopping avg 550K VND)
- [x] Life event patterns detectable: C001 baby (4 transactions Jan 2026), C002 home purchase (3 transactions Nov 2025 incl 49.8M Vinhomes), C004 career change (2 transactions Feb 2026)
- [x] Product catalogue: 21 products across 4 entities (Bank 9, Finance 4, Securities 4, Life 4) with Vietnamese names, rates, and income thresholds

**Pause here for manual confirmation before proceeding.**

---

## Phase 2: Deterministic Tools

### Overview
All MCP tools as pure Python functions. No LLM involvement — these are the functions the agent will call. Each returns typed Pydantic models.

### Changes Required:

#### 1. Spending tools (`src/lodestar/tools/spending.py`)
```python
async def get_transactions(customer_id: str, start_date: str, end_date: str, category: str | None = None) -> list[Transaction]
async def categorise_transactions(transactions: list[Transaction]) -> list[Transaction]  # rule-based + underthesea
async def compute_spending_summary(customer_id: str, period: str) -> SpendingSummary
async def compute_income_pattern(customer_id: str) -> IncomePattern
async def detect_anomalies(customer_id: str, period: str) -> list[SpendingAnomaly]
async def detect_recurring_charges(customer_id: str) -> list[RecurringCharge]
async def compute_month_over_month_change(customer_id: str, category: str | None = None) -> list[MoMChange]
```

#### 2. Goal tools (`src/lodestar/tools/goals.py`)
```python
async def create_goal(customer_id: str, name: str, target_amount: float, target_date: str) -> SavingsGoal
async def project_goal_completion(goal_id: str) -> GoalProjection
async def compute_savings_rate(customer_id: str, months: int = 6) -> SavingsRate
async def calculate_loan_affordability(customer_id: str, loan_amount: float, term: int, rate: float) -> AffordabilityResult
```

#### 3. Chart tools (`src/lodestar/tools/charts.py`)
```python
def generate_spending_chart(summary: SpendingSummary, chart_type: str = "donut") -> ChartSpec
def generate_goal_progress_chart(goal: SavingsGoal, projection: GoalProjection) -> ChartSpec
def generate_trend_chart(trends: list[MoMChange]) -> ChartSpec
def generate_cashflow_waterfall(customer_id: str, period: str) -> ChartSpec
```
Charts return `ChartSpec` JSON — `{chart_type, title, data, axes}` — rendered by the frontend.

#### 4. Simulation tools (`src/lodestar/tools/simulation.py`)
```python
async def simulate_scenario(customer_id: str, scenario_type: str, parameters: dict) -> ScenarioResult
```
Cross-entity simulation using `numpy-financial` for mortgage/loan calculations. Returns per-entity impact breakdown.

#### 5. Vietnamese NLP (`src/lodestar/nlp/vietnamese.py`)
```python
def normalise_transaction(desc: str) -> str  # underthesea text_normalize + word_tokenize
def extract_financial_entities(text: str) -> dict  # NER + regex for amounts/dates
```

### Success Criteria:

#### Automated Verification:
- [x] `uv run pytest tests/test_tools.py` — 27/27 tests pass (16 model + 5 spending + 3 chart + 2 goal + 1 simulation)
- [x] Spending summary percentages sum to 100.0%
- [x] Loan affordability uses numpy-financial (1B VND loan = 8,055,932/month at 7.5%)
- [x] Chart specs valid: donut with labels/values/percentages/currency keys
- [x] Scenario simulation: 4-entity impact, DTI flagged at 75% for 2B home purchase
- [x] `uv run ruff check src/` passes

#### Manual Verification:
- [x] Vietnamese normalisation: NAPAS descriptions tokenised correctly (word compounds like "BÚN_ĐẬU", "HÀ_NỘI" preserved)
- [x] Chart specs: donut with 3 categories, waterfall with income/expense/net steps, progress with percentage — all valid for Recharts

**Phase 2 complete.**

---

## Phase 3: RAG Pipeline

### Overview
Qdrant embedded mode + bge-m3 via FlagEmbedding. Hybrid dense + sparse search with RRF fusion and payload pre-filtering.

### Changes Required:

#### 1. Embeddings wrapper (`src/lodestar/rag/embeddings.py`)
Thin wrapper around `BGEM3FlagModel` that returns dense and sparse vectors.

#### 2. Indexer (`src/lodestar/rag/indexer.py`)
- Create Qdrant collection with dense + sparse vector config
- Create payload indexes for `product_type`, `min_income`, `interest_rate`
- Ingest `products_catalogue.json` with embeddings

#### 3. Retriever (`src/lodestar/rag/retriever.py`)
- Hybrid query with `Prefetch` (dense + sparse), `FusionQuery(fusion=Fusion.RRF)`
- Payload pre-filtering before vector search
- Returns ranked `list[ProductInfo]`

#### 4. Product tools (`src/lodestar/tools/products.py`)
```python
async def search_products(query: str, filters: ProductFilters | None = None) -> list[ProductInfo]
async def compare_products(product_ids: list[str]) -> ComparisonTable
async def check_eligibility(customer_id: str, product_id: str) -> EligibilityResult
```

### Success Criteria:

#### Automated Verification:
- [x] `uv run pytest tests/test_rag.py` — 10/10 tests pass (7 search + 3 product tools)
- [x] Payload filtering correctly excludes products above customer's income level
- [x] Vietnamese queries ("thẻ tín dụng cho lương 10 triệu") return credit card results
- [x] Indexing 21 products completes in <10 seconds on CPU
- [x] Query latency <5s on CPU (first query includes model load; subsequent <1s)

**Note:** Switched from `FlagEmbedding` to `sentence-transformers` due to `transformers` version conflict. Dense-only search with payload filtering is sufficient for 21 products. Hybrid (dense+sparse) can be added later when FlagEmbedding fixes compatibility.

#### Manual Verification:
- [x] Top-5 results for Vietnamese credit card query include 3 credit cards — sensible matches
- [x] Eligibility check: C002 (18M income) passes for SB-CC-001 (8M min); C003 (8M income) fails for SB-CC-002 (20M min)

**Pause here for manual confirmation before proceeding.**

---

## Phase 4: LangGraph Workflows

### Overview
Four specialist workflows compiled as LangGraph subgraphs, each wrappable as a `StructuredTool` for the orchestrator.

### Changes Required:

#### 1. Spending analysis workflow (`src/lodestar/agents/workflows/spending.py`)
LangGraph `StateGraph` with nodes: fetch_transactions → categorise → compute_summary → generate_chart → compose_insight. Fan-out where possible.

#### 2. Goal tracking workflow (`src/lodestar/agents/workflows/goals.py`)
Nodes: compute_income_pattern → compute_savings_rate → project_completion → generate_chart → compose_insight.

#### 3. Product match workflow (`src/lodestar/agents/workflows/product_match.py`)
Nodes: extract_query_intent → search_products → check_eligibility → compose_response.

#### 4. Scenario simulation workflow (`src/lodestar/agents/workflows/scenario.py`)
Nodes: fetch_cross_entity_data (fan-out to all 4 entities) → merge → simulate_scenario → generate_comparison_chart → compose_insight. Uses `AgentState` with `Annotated[list, operator.add]` reducers for safe parallel writes.

Each workflow is compiled and wrapped:
```python
spending_graph = spending_builder.compile()
spending_tool = StructuredTool.from_function(
    func=lambda customer_id, period: spending_graph.invoke({"customer_id": customer_id, "period": period}),
    name="spending_analysis",
    args_schema=SpendingArgs,
    description="Run full spending analysis for a customer over a period.",
)
```

### Success Criteria:

#### Automated Verification:
- [x] Each workflow runs end-to-end with synthetic data (no LLM needed for tool nodes) — 6/6 tests pass
- [x] Workflows return typed results matching their output schemas
- [x] Scenario workflow returns 4 entity impacts (bank, finance, securities, life) with correct cashflow
- [x] `uv run pytest tests/` — 43/43 all tests pass (no regressions)

#### Manual Verification:
- [x] Spending: Vietnamese insight with top-3 categories, anomaly warnings (⚠), donut chart with 6 categories
- [x] Scenario: 4-entity breakdown (mortgage 12.9M/month, DTI 75% flagged), waterfall chart, cashflow 17.5M → 4.6M
- [x] Product match: 5 results with eligibility checks (✓/✗), compliance disclaimer present ("thông tin sản phẩm, không phải tư vấn")

**Pause here for manual confirmation before proceeding.**

---

## Phase 5: Orchestrator

### Overview
The core: Qwen-Agent reactive orchestrator with workflow-as-tool pattern, plus the background trigger loop.

### Changes Required:

#### 1. Trigger rules (`src/lodestar/agents/triggers.py`)
Deterministic Python rules — no LLM. Each trigger returns a `TriggerEvent` with type, severity, customer_id, context.

```python
def check_velocity_anomaly(transactions: list[Transaction], customer_id: str) -> TriggerEvent | None
def check_recurring_change(transactions: list[Transaction], customer_id: str) -> TriggerEvent | None
def check_payday_detected(transactions: list[Transaction], customer_id: str) -> TriggerEvent | None
def check_budget_threshold(transactions: list[Transaction], customer_id: str) -> TriggerEvent | None
def check_goal_milestone(customer_id: str) -> TriggerEvent | None
def check_life_event_pattern(transactions: list[Transaction], customer_id: str) -> TriggerEvent | None
```

#### 2. Background agent (`src/lodestar/agents/background.py`)
Asyncio polling loop:
- Polls transactions every N seconds (configurable, default 30s for demo)
- Runs all trigger rules
- For each trigger: invokes the relevant workflow-as-tool
- LLM composes insight card text (thinking OFF)
- Compliance filter classifies output
- Ranks, deduplicates, stores to `insight_cards` table

#### 3. Compliance filter (`src/lodestar/agents/compliance.py`)
Lightweight LLM classifier: given a response, classify as `information`, `guidance`, or `advice`. Block `advice`. Add disclaimer to `guidance`. Log all classifications.

#### 4. Reactive orchestrator (`src/lodestar/agents/orchestrator.py`)
Qwen-Agent `Assistant` with registered workflow tools + atomic MCP tools as fallback:
```python
from qwen_agent.agents import Assistant

bot = Assistant(
    llm=llm_cfg,
    function_list=[spending_tool, goal_tool, product_tool, scenario_tool, ...],
    system_message="You are a Vietnamese financial coach for Shinhan Bank...",
)
```
Receives user input + insight context + learning history. Returns response + optional chart spec.

### Success Criteria:

#### Automated Verification:
- [x] `uv run pytest tests/test_triggers.py` — 15/15 pass (9 trigger rules + 1 background + 5 compliance)
- [x] Compliance filter blocks advice (Vietnamese "bạn nên", English "I recommend"), adds disclaimer to guidance
- [x] Background agent generates 10 insight cards from seeded data across all 5 customers
- [x] Orchestrator selects correct workflows via Ollama Qwen3:14b — spending_analysis returns donut chart, product_search returns eligibility, scenario_simulation returns waterfall

**Note:** Using Ollama (`qwen3:14b`) at `localhost:11434` instead of llama-server. Config updated.

#### Manual Verification:
- [x] Vietnamese spending query ("Tháng 9 năm 2025 tôi chi tiêu bao nhiêu?") → detailed breakdown with donut chart, percentages correct
- [x] Background agent insight cards: 10 cards generated — life events detected for C001 (baby), recurring charge changes detected, all classified as information (not advice)
- [x] Compliance filter catches all 7 edge cases: advice blocked (3 Vietnamese + 1 English), guidance gets disclaimer (2), information passes (2)

**Pause here for manual confirmation before proceeding.**

---

## Phase 6: Learning Loop

### Overview
Per-customer lesson journal with quality gating, semantic retrieval, importance feedback, and federated cohort aggregation.

### Changes Required:

#### 1. Journal (`src/lodestar/learning/journal.py`)
Adapted from TojiMoola's `TradingJournal`:
- `add_or_evolve_lesson()`: embed, check cosine similarity >0.85 against existing → merge or store new
- `get_relevant_lessons()`: three-component scoring (recency + importance + relevance), retrieve top-k, compress via LLM
- `update_importance_post_outcome()`: +0.5 if helped, -0.3 if not

#### 2. Reflection (`src/lodestar/learning/reflection.py`)
- `run_reflection()`: LLM evaluates process quality (Van Tharp 2x2 → process_grade + outcome_quality)
- `extract_lesson()`: structured lesson with conditions, error_type, confidence, importance
- Quality gate: only persist if process_grade A/B AND confidence >= 0.70

#### 3. Cohort store (`src/lodestar/learning/cohort.py`)
- `aggregate_to_cohort()`: strip PII, retain pattern type + category + demographic band
- `get_cohort_insights()`: retrieve anonymised insights for new customers by demographic key
- k-anonymity: only activate when supporting_count >= 50 (relaxed to 5 for PoC demo)

### Success Criteria:

#### Automated Verification:
- [x] `uv run pytest tests/test_learning.py` — 14/14 pass (5 journal + 5 reflection + 4 cohort)
- [x] Semantic dedup merges similar lessons (2 similar → 1 merged with times_evolved=1, confidence boosted)
- [x] Importance: +0.5 on help (5.0→5.5), -0.3 on no-help (5.0→4.7)
- [x] Quality gate blocks: low confidence (<0.70) blocked, bad process (grade D) blocked, good process + high confidence passes
- [x] Cohort: reaches threshold at 5 customers, no customer_id in cohort_insights table

Full suite: 72/72 pass.

#### Manual Verification:
- [x] Journal: lesson stored, retrieved by relevance query ("food spending" matches "food spikes during Tet")
- [x] Reflection: earned_reward (A+good), dumb_luck (D+good) correctly classified; lesson only extracted from earned_reward
- [x] Cohort: 5 aggregations → cohort insight activated; below threshold returns None

**Pause here for manual confirmation before proceeding.**

---

## Phase 7: FastAPI Backend

### Overview
Wire everything together into the API. All endpoints from doc 03.

### Changes Required:

#### 1. API app (`src/lodestar/api.py`)
FastAPI app with endpoints:
- `GET /feed/{customer_id}` — ranked insight cards
- `POST /dismiss/{insight_id}` — dismiss + learning loop feedback
- `POST /chat/{insight_id}` — SSE streaming drill-down chat
- `POST /simulate` — cross-entity scenario
- `GET /goals/{customer_id}` + `POST /goals` — goal CRUD
- `GET /products/search` — RAG product search
- `GET /stream/{customer_id}` — SSE insight stream

#### 2. Lifecycle management
- Start background agent on app startup (`@app.on_event("startup")`)
- Initialise Qdrant collection + seed products on first run
- AsyncSqliteSaver for LangGraph checkpointing

#### 3. CORS
Enable CORS for Vercel frontend domain.

### Success Criteria:

#### Automated Verification:
- [x] `uv run pytest tests/test_api.py` — 7/8 pass, 1 skipped (7 endpoints tested: health, feed, feed-unknown, goals CRUD, simulation, products, SSE route)
- [x] SSE stream endpoint route exists and is configured
- [x] `uvicorn lodestar.api:app` starts successfully — health returns 200 with 5 customers, feed returns insight cards
- [x] `GET /feed/C001` returns JSON with 2 insight cards

#### Manual Verification:
- [x] Chat endpoints tested with Ollama Qwen3:14b: Vietnamese spending query → tool call → donut chart; product search → eligibility; scenario simulation → waterfall chart with DTI risk flag
- [x] Full server lifecycle: startup → RAG init (21 products) → background cycle → health 200 → feed returns cards → goals CRUD → simulation → product search → dismiss removes from feed
- [x] All 7 non-LLM endpoints verified via httpx against live uvicorn: health, feed, goals (GET+POST), simulate, products/search, dismiss

**Pause here for manual confirmation before proceeding.**

---

## Phase 8: Next.js Frontend

### Overview
Shinhan-branded Next.js + shadcn/ui app deployed on Vercel. Built using Vercel skills (deploy-to-vercel, vercel-react-best-practices, shadcn, web-design-guidelines).

### Changes Required:

#### 1. Project setup (`frontend/`)
- `npx create-next-app@latest frontend --typescript --tailwind --app`
- `npx shadcn@latest init` with Shinhan OKLCH theme
- Install: `shadcn` components (card, badge, tabs, button, input), `recharts`, `jakobhoeg/shadcn-chat`

#### 2. Theming (`frontend/globals.css`)
OKLCH variables for Shinhan blue: `--primary: oklch(0.45 0.27 264)`

#### 3. Components
- `InsightCard` — Card + Badge + optional ChartContainer thumbnail
- `InsightFeed` — responsive grid of InsightCards with SSE real-time updates
- `DrillDownChat` — scoped chat thread with inline Recharts, SSE streaming
- `ChartRenderer` — takes `ChartSpec` JSON, renders appropriate Recharts component (pie, bar, line, area)
- `ScenarioView` — cross-entity simulation results with comparison charts

#### 4. Pages
- `/` — Insight feed (tabs: Feed, Goals, Products)
- `/insight/[id]` — Drill-down chat for a specific insight
- `/goals` — Savings goals with progress charts
- `/products` — Product search with eligibility filtering

#### 5. API client (`frontend/lib/api.ts`)
Typed fetch wrapper for all FastAPI endpoints + `useSSE` hook for EventSource.

#### 6. Vercel deployment
- `vercel deploy` via Vercel CLI
- Environment variable: `NEXT_PUBLIC_API_URL` pointing to FastAPI backend

### Success Criteria:

#### Automated Verification:
- [x] `cd frontend && npm run build` succeeds — 3 routes compiled (/, /_not-found, /insight/[id])
- [x] `npm run lint` passes with zero errors
- [ ] Vercel deployment succeeds and returns a preview URL (deferred — requires Vercel CLI auth)

#### Manual Verification:
- [ ] Insight feed renders with Shinhan blue branding, card-based layout
- [ ] Charts render inline in chat messages (donut, bar, line)
- [ ] Mobile responsive — feed cards stack on narrow viewport
- [ ] SSE streaming shows tokens appearing in real-time during chat
- [ ] Full demo scenario completes end-to-end via the UI
- [ ] Accessibility: text contrast meets WCAG 2.2 AA (4.5:1)

---

## Testing Strategy

### Unit Tests (`tests/test_tools.py`):
- Every deterministic tool returns correct types and values
- Spending percentages sum to 100%
- Goal projections match hand-calculated values
- Chart specs validate against schema

### Integration Tests (`tests/test_api.py`):
- API endpoints return correct status codes
- SSE endpoints stream valid events
- Background agent generates insights from seeded data
- Learning loop persists and retrieves lessons

### Manual Testing Steps:
1. Start llama-server with Qwen3-8B
2. Start FastAPI backend
3. Open Vercel frontend
4. Verify insight cards appear on feed
5. Tap a spending alert card → see drill-down with donut chart
6. Ask "What if I buy a house?" → see cross-entity simulation
7. Dismiss an insight → verify learning loop logs the feedback
8. Check Vietnamese language quality across all responses

## Performance Considerations

- **LLM latency:** Qwen3-8B at Q4_K_M on 12GB GPU: expect 200-500ms TTFT, 30-50 tok/s generation
- **RAG latency:** bge-m3 encode + Qdrant hybrid search: ~100-350ms on CPU
- **Tool execution:** Deterministic Python functions: <10ms each
- **Background agent:** Polling every 30s; each trigger check <50ms; full cycle <2s
- **Frontend:** SSE streaming eliminates perceived latency for chat responses

## Migration Notes

Not applicable — greenfield project. When moving to production:
- Replace synthetic data backends in `BankingRouter` with real Shinhan APIs
- Switch SQLite → PostgreSQL
- Switch Qdrant embedded → Qdrant distributed
- Switch llama-server → SGLang for throughput
- Add authentication (OAuth2 PKCE via FAPI)
- Deploy on Shinhan's OpenShift infrastructure

## References

- Research documentation: `docs/01-problem-and-market.md` through `docs/17-references.md`
- Master document: `SB1_AI_Personal_Financial_Coach.md`
- TojiMoola learning loop pattern: `/home/brian-isaac/Documents/personal/tojimoola/`
- Portfolio-Intelligence-Platform workflow pattern: `/home/brian-isaac/Documents/personal/Portfolio-Intelligence-Platform/`
