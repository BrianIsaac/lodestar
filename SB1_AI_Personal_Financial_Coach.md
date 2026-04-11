# SB1: AI Personal Financial Coach for Shinhan SOL Vietnam

## Table of Contents

1. [Problem Statement](#1-problem-statement)
2. [Market Context](#2-market-context)
3. [Solution Overview](#3-solution-overview)
4. [Architecture](#4-architecture)
5. [Orchestrator: Workflow-as-Tool Pattern](#5-orchestrator-workflow-as-tool-pattern)
6. [Agent Design](#6-agent-design)
7. [Proactive Insight Feed UX](#7-proactive-insight-feed-ux)
8. [Cross-Entity Financial Digital Twin](#8-cross-entity-financial-digital-twin)
9. [Predictive Life Event Detection](#9-predictive-life-event-detection)
10. [Persistent Learning Loop](#10-persistent-learning-loop)
11. [Federated Customer Learning](#11-federated-customer-learning)
12. [Data Sources and Integration](#12-data-sources-and-integration)
13. [Visualisation Strategy](#13-visualisation-strategy)
14. [Technology Stack](#14-technology-stack)
15. [Regulatory Compliance](#15-regulatory-compliance)
16. [PoC Scope](#16-poc-scope)
17. [Scale-Up Path](#17-scale-up-path)
18. [Innovation Differentiators](#18-innovation-differentiators)
19. [References](#19-references)

---
## 1. Problem Statement

### The Gap

Shinhan Bank Vietnam's SOL app serves approximately 2 million customers with standard mobile banking features (transfers, payments, bill pay, QR). There is **no AI-powered financial advisory capability** — no chatbot, no personalised insights, no proactive financial guidance. This is true across the entire Vietnamese banking market: no consumer-grade AI financial coach exists.

### Why It Matters

**Vietnam's financial literacy crisis is measurable:**

- Vietnam scores **12.0 out of 21** on the OECD/INFE financial literacy index — among the lowest globally
- The S&P Global FinLit Survey ranks Vietnam among the **bottom quartile of 148 nations**
- Over **80% of Hanoi survey respondents** admit to little knowledge or interest in personal finance
- Personal finance is not systematically taught in Vietnamese schools
- Financial advisory access is limited to high-net-worth customers at most banks
- Credit card penetration remains low — Vietnam's consumer credit-to-GDP ratio is among the lowest in ASEAN, reflecting both risk aversion and limited access to credit products

**The behavioural consequence:**

- 33% of Vietnamese consumers cite inability to save as their top financial anxiety
- Only ~20% of Gen Z proactively save for retirement despite Gen Z comprising 25% of Vietnam's labour force (15 million people)
- Customers cannot differentiate between savings products, investments, and insurance — leading to poor decisions and fraud vulnerability
- Over 50% of customers use three or more banks — wallet fragmentation driven by lack of personalised value from any single bank
- Financial fraud and scam losses are rising as digital adoption outpaces financial literacy — customers making uninformed decisions are increasingly targeted

**The business consequence for Shinhan:**

- Low cross-sell conversion: 68% of digital interactions are limited to balance checks
- Customer churn driven by absence of personalised engagement
- SOL app's ~2 million users are a fraction of domestic competitors (MBBank: 28.6 million, Vietcombank growing 50%+ YoY)
- Despite being Vietnam's #1 foreign bank, Shinhan must differentiate on experience rather than scale

### Target Users

- Digital Business Unit
- Retail Solution Division (Retail Customer Dept., Retail Lending Dept., Wealth Management Dept.)
- Card Division

### Expected Outcomes (from Shinhan's brief)

- Increase customer engagement (DAU/MAU) on SOL app
- Improve cross-sell conversion rate (cards, loans, insurance)
- Increase customer retention and reduce churn through proactive financial insights
- Enhance customer satisfaction (NPS/CSAT) via personalised financial guidance
- Grow CASA balance through better savings behaviour recommendations

---

## 2. Market Context

### Competitive Landscape

| Product | Market | Model | Key Insight |
|---|---|---|---|
| **Cleo 3.0** | US/UK, 8M+ users | OpenAI-powered, persistent memory, voice | Inline chat + charts is the winning UX pattern |
| **Plum** | UK/EU | Auto-savings via spending pattern analysis | Micro-savings nudges drive high engagement |
| **Monarch Money** | US | Multi-account aggregation, cash flow forecasting | Savings runway projection is high-value |
| **KakaoBank AI** | South Korea | Azure OpenAI, conversational financial calculator | Closest comparable — same Shinhan ecosystem |
| **WeBank** | China | Federated learning for credit scoring | Privacy-preserving personalisation model |
| **RBC NOMI** | Canada | Proactive nudge-based savings | Autonomously set aside ~$6.5 billion for clients via automated savings |
| **Albert Genius** | US | Autonomous micro-savings + debt-swap recommendations | Monitors affordability and moves funds without user initiation |
| **Copilot Money** | US | Bank feeds + calendar + email ingestion | Surfaces lifestyle-inflation signals within 48h of income change |

**No Vietnamese-market AI financial coach exists.** This is a clear first-mover opportunity.

### Vietnam Digital Banking Context

- 87% of Vietnamese adults hold payment accounts (up from 31% in 2015)
- 95%+ of transactions are now digital; ATM usage fell 19.5%
- Mobile payment market projected at USD 47.6 billion in 2025, growing to USD 76 billion by 2030
- Digital banking users are 1.3x more likely to purchase financial products and own 1.6x more products
- Average monthly income per capita: VND 5.4 million (~USD 204); urban: VND 6.9 million (~USD 261)
- Nearly half of Vietnamese consumers save at least 20% of monthly income — savings intent exists, guidance does not

---

## 3. Solution Overview

An autonomous AI financial intelligence system embedded within Shinhan's SOL mobile app — **not a chatbot, but a proactive financial agent** that continuously monitors customer data, detects patterns and life events, simulates future scenarios across all Shinhan entities (Bank, Finance, Securities, Life), and surfaces actionable insights before the customer asks.

### Core Capabilities

1. **Monitors autonomously** — background agent streams customer transaction data, detecting spending anomalies, recurring charge changes, payday patterns, and life events in real-time
2. **Surfaces proactively** — ranked insight cards appear on a dedicated tab, each with a clear action; the customer reviews findings, not prompts an assistant
3. **Simulates across entities** — financial digital twin models the customer's full Shinhan relationship (bank accounts, loans, securities, insurance), enabling "what if" scenario simulation
4. **Learns per-customer** — quality-gated persistent learning loop improves advice over time; anonymised cohort insights improve advice for all customers via federated learning
5. **Drills down conversationally** — tapping any insight card opens a scoped chat thread with full context pre-loaded, charts inline, and follow-up actions available
6. **Multilingual** — Vietnamese, English, Korean (matching SOL's supported languages); Qwen3 covers 119 languages for future expansion

### What This Is NOT

This is not a chatbot waiting for questions. It is an **autonomous financial agent** that:
- Works when the customer is not looking
- Detects what matters before the customer knows to ask
- Presents findings as a curated feed, not a conversation
- Offers conversational drill-down only when the customer wants depth
- Simulates financial futures, not just reports the past

### Why Proactive Beats Reactive

Gartner named **Ambient Invisible Intelligence** a top-10 strategic technology trend for 2025 — AI that senses and acts in the background without explicit user interaction. The evidence from deployed financial products confirms this direction:

- **RBC NOMI**: Proactive nudging autonomously set aside ~$6.5 billion in customer savings — no user prompt required
- **JPMorgan**: AI nudge system produced 10-20% lift in product application completion rates
- **Cleo Autopilot** (July 2025): Three-layer architecture — Roadmap (goal plan), Daily Plan (personalised guidance), Actions (autonomous execution with pre-approved guardrails). A Smart Insights Agent powered by OpenAI o3 reviews six months of history and surfaces findings unprompted

The key insight: proactive financial AI drives measurably higher engagement and conversion than reactive chatbots. However, notification fatigue is a real constraint — 64% of users delete an app after 5+ irrelevant notifications per week (MagicBell). The lever is **relevance, not volume**: banks applying real-time personalisation see 30% higher digital engagement and 20% fewer opt-outs.

Our system manages this through per-customer learning — the more the system knows about what a customer engages with, the more precisely it can rank and surface only the insights that matter.

---

## 4. Architecture

### High-Level System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                       SOL Mobile App                             │
│                  (iOS / Android — Native)                        │
│              Supported: Vietnamese, English, Korean              │
│                                                                  │
│  ┌──────────────────┐  ┌───────────────┐  ┌──────────────────┐  │
│  │  Insight Feed    │  │  Drill-Down   │  │  Push            │  │
│  │  Tab (Cards)     │  │  Chat Thread  │  │  Notifications   │  │
│  └────────┬─────────┘  └───────┬───────┘  └────────┬─────────┘  │
│           │  Shinhan Brand: #0046FF primary          │           │
│           │  Light mode, card-based, sans-serif      │           │
└───────────┼────────────────────┼─────────────────────┼───────────┘
            │                    │                     │
            ▼                    ▼                     ▼
┌──────────────────────────────────────────────────────────────────┐
│                      API Gateway (FastAPI)                       │
│                                                                  │
│  GET /feed          POST /chat/{insight_id}    POST /simulate   │
│  GET /insights      GET /goals                 GET /scenarios   │
│  POST /dismiss      GET /products              WS /stream       │
└─────────────────────────────┬────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
┌───────────────────┐ ┌─────────────┐ ┌────────────────────┐
│  Background Agent │ │ Orchestrator│ │ Simulation Engine  │
│  (Trigger Loop)   │ │ (Reactive)  │ │ (Digital Twin)     │
│                   │ │             │ │                    │
│  Polls/streams    │ │ User taps   │ │ "What if" across   │
│  transaction data │ │ insight or  │ │ Bank + Finance +   │
│  → trigger rules  │ │ asks query  │ │ Securities + Life  │
│  → invoke         │ │ → selects   │ │                    │
│    workflows      │ │   workflow  │ │ Deterministic      │
│  → rank & push    │ │   or ReAct  │ │ projection tools   │
│    insight cards   │ │   fallback  │ │                    │
└────────┬──────────┘ └──────┬──────┘ └─────────┬──────────┘
         │                   │                   │
         ▼                   ▼                   ▼
┌──────────────────────────────────────────────────────────────────┐
│                    Workflow-as-Tool Layer                        │
│                                                                  │
│  ┌─────────────┐ ┌──────────┐ ┌─────────┐ ┌──────────────────┐ │
│  │ Spending    │ │ Goal     │ │ Product │ │ Life Event       │ │
│  │ Analysis    │ │ Tracking │ │ Match   │ │ Scenario         │ │
│  │ Workflow    │ │ Workflow │ │ Workflow│ │ Workflow          │ │
│  └─────────────┘ └──────────┘ └─────────┘ └──────────────────┘ │
│  Each is a compiled LangGraph subgraph, callable as a tool      │
│  Known intents → workflow; novel intents → ReAct fallback       │
└──────────────────────────────┬───────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                    Deterministic MCP Tools                       │
│                                                                  │
│  Data Extraction │ Math/Projection │ Chart Gen │ Product RAG    │
│  (Python only — LLM never calculates, only interprets)          │
└──────────────────────────────┬───────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                         Data Layer                               │
│                                                                  │
│  ┌───────────┐ ┌────────────┐ ┌────────┐ ┌──────────────────┐  │
│  │ Banking   │ │ Customer   │ │ Product│ │ Learning Journal │  │
│  │ Router    │ │ Learning   │ │ RAG    │ │ + Federated      │  │
│  │ (MCP)     │ │ Store      │ │(Qdrant)│ │   Cohort Store   │  │
│  │           │ │            │ │        │ │   (SQLite)       │  │
│  │ Bank API  │ │ Per-user   │ │        │ │                  │  │
│  │ Finance   │ │ lessons +  │ │        │ │ Anonymised       │  │
│  │ Securities│ │ goals +    │ │        │ │ cross-customer   │  │
│  │ Life API  │ │ state      │ │        │ │ insights         │  │
│  └───────────┘ └────────────┘ └────────┘ └──────────────────┘  │
└──────────────────────────────┬───────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                       Inference Layer                            │
│                                                                  │
│  Qwen3-8B (Q4_K_M) → llama.cpp / Ollama (PoC)                  │
│  32K context │ Tool calling │ Thinking mode toggle               │
│  Multilingual: VI / EN / KO (Qwen3 supports 119 languages)      │
└──────────────────────────────────────────────────────────────────┘
```

### Integration with SOL

SOL is a native iOS/Android mobile app developed by Shinhan Bank Global Dev Dept. (Korea). Supports Vietnamese, English, Korean. No public API or SDK. The integration path is:

- **Backend API**: Our service exposes a FastAPI backend that SOL connects to via authenticated REST endpoints
- **Insight Feed Tab**: A new tab in SOL — either native screens consuming our API, or an embedded WebView styled to match Shinhan's brand (`#0046FF` primary, light mode, card-based, sans-serif typography)
- **Drill-Down Chat**: Tapping an insight card opens a scoped conversational thread via the same API
- **Charts**: Returned as structured JSON specs; SOL frontend renders natively using its charting library
- **Push Notifications**: Trigger gates push via Shinhan's existing notification infrastructure
- **Branding**: All UI follows Shinhan's 2022 corporate identity — monochromatic blue system (`#0046FF`, `#2878F5`, `#4BAFF5`, `#00236E`), near-white text on blue (`#EAF0FF`)

### Integration Pattern: BFF + Native SDK

The recommended integration pattern is **Backend for Frontend (BFF)** — a dedicated backend layer per client type that aggregates, filters, and streams AI responses tailored to mobile constraints:

- BFF aggregates data from multiple Shinhan entity APIs into a single response
- Reduces mobile client complexity — the app doesn't orchestrate multi-entity calls
- Enables SSE (Server-Sent Events) for real-time insight streaming without WebSocket overhead

**Real-time transport:** SSE over HTTP/2 for pushing insights to the mobile app — auto-reconnects on mobile network drops, unidirectional (server pushes; client sends discrete requests). WebSocket reserved for drill-down chat where bidirectional streaming is needed.

### API Security

Following **FAPI (Financial-grade API)** standards with **mTLS + OAuth2 PKCE** for customer-facing flows:
- API gateway centralises auth, rate limiting, and anomaly detection
- mTLS mandatory for service-to-service calls within Shinhan's infrastructure
- All AI interactions logged for audit trail (regulatory requirement under SBV AI Circular)
- BOLA (Broken Object-Level Authorisation) is the leading API vulnerability in banking — gateway-level WAF is essential

### Shinhan Technology Context

Shinhan Bank runs **Red Hat OpenShift** (Kubernetes-based) with a microservices architecture that achieved 60% operating cost reduction. The chairman has named "AX (AI transformation)" as a survival imperative for 2026. This microservices posture is fully compatible with our FastAPI + containerised inference architecture.

### Event-Driven Architecture Options

For the background agent's transaction monitoring:

| Scale | Technology | Notes |
|---|---|---|
| PoC | Polling loop (Python asyncio) | Simplest, sufficient for demo |
| Pilot | **Redpanda** or Kafka Streams | Kafka-compatible, operationally simpler than full Kafka |
| Production | **Kafka + Flink** | Industry standard for stateful stream processing in banking |

### FastAPI Endpoint Signatures

```python
from fastapi import FastAPI, WebSocket
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel

app = FastAPI(title="Shinhan Financial Coach API")

# Insight feed
@app.get("/feed/{customer_id}")
async def get_insight_feed(customer_id: str, limit: int = 10) -> list[InsightCard]:
    """Ranked insight cards for the customer's feed tab."""

@app.post("/dismiss/{insight_id}")
async def dismiss_insight(insight_id: str, customer_id: str) -> None:
    """Customer dismisses an insight — feeds back into learning loop."""

# Drill-down chat
@app.post("/chat/{insight_id}")
async def chat_drill_down(insight_id: str, message: ChatMessage) -> EventSourceResponse:
    """Scoped conversational thread about a specific insight. SSE streaming."""

# Scenario simulation
@app.post("/simulate")
async def simulate_scenario(request: ScenarioRequest) -> ScenarioResult:
    """Cross-entity 'what if' simulation via digital twin."""

# Goals
@app.get("/goals/{customer_id}")
async def get_goals(customer_id: str) -> list[SavingsGoal]:
    """Active savings goals with progress."""

@app.post("/goals")
async def create_goal(goal: CreateGoalRequest) -> SavingsGoal:
    """Create a new savings goal."""

# Products
@app.get("/products/search")
async def search_products(query: str, customer_id: str | None = None) -> list[ProductInfo]:
    """RAG-powered product search with optional eligibility filtering."""

# Real-time insight stream (for background push)
@app.get("/stream/{customer_id}")
async def stream_insights(customer_id: str) -> EventSourceResponse:
    """SSE stream pushing new insight cards as they're generated."""
```

---

## 5. Orchestrator: Workflow-as-Tool Pattern

The orchestrator is **not** a LangGraph graph itself. It is an LLM agent (Qwen3-8B) that has access to **pre-built LangGraph workflows as callable tools**. For known intents, it invokes a deterministic workflow in a single tool call. For novel or ambiguous requests, it falls back to ReAct-style atomic tool calling.

This pattern is called **"Agents-as-Tools"** or **Hierarchical Delegation** (documented by AWS, Anthropic, and LangGraph). It gives us determinism and auditability for common flows, flexibility for edge cases, and 3-5x fewer tokens than pure ReAct.

### Two Operating Modes

#### Mode 1: Background Agent (Proactive — No User Interaction)

The background agent runs continuously, polling or streaming transaction data. It does not involve the LLM for trigger detection — triggers are deterministic Python rules. The LLM is only invoked to generate the natural language insight card after a trigger fires.

```
[Transaction Stream / Poll]
    │
    ▼
[Deterministic Trigger Rules] (Python, no LLM)
    │  - Velocity anomaly (3x normal in category)
    │  - Recurring charge change detected
    │  - Payday pattern recognised
    │  - Savings opportunity (persistent positive balance)
    │  - Budget threshold breach
    │  - Goal milestone reached
    │  - Life event pattern detected (see Section 9)
    │
    ▼ (trigger fired)
[Invoke relevant workflow-as-tool]
    │  e.g., spending_analysis_workflow(customer_id, trigger_context)
    │
    ▼
[Workflow returns structured result]
    │  - insight_summary (text)
    │  - chart_spec (JSON)
    │  - severity / priority score
    │  - suggested_actions
    │
    ▼
[LLM composes insight card] (thinking OFF — just format the result)
    │
    ▼
[Compliance Filter] → classify and gate
    │
    ▼
[Rank, deduplicate, push to customer's insight feed]
    │
    ▼
[Customer acts on or dismisses card]
    │
    ▼
[Async: Learning Loop Update] → evaluate insight quality, update importance scores
```

#### Mode 2: Reactive Orchestrator (User Taps Insight or Asks Question)

When a customer taps an insight card or types a question, the orchestrator activates. It receives the user's input plus the insight context (if drill-down) plus the customer's learning history.

```
[User Input + Insight Context + Learning History]
    │
    ▼
[Orchestrator LLM] (thinking ON — reason about intent)
    │
    ├── Known intent → invoke pre-built workflow as tool
    │   e.g., spending_analysis_workflow, goal_tracking_workflow,
    │         product_match_workflow, scenario_simulation_workflow
    │
    └── Novel/ambiguous → ReAct over atomic MCP tools
        (flexible, handles questions not covered by workflows)
    │
    ▼
[Workflow/Tool results returned]
    │
    ▼
[LLM composes response] (thinking OFF — interpret, don't calculate)
    │  + chart_spec if applicable
    │  + suggested follow-up actions
    │
    ▼
[Compliance Filter] → classify and gate
    │
    ▼
[Response to customer in scoped chat thread]
    │
    ▼
[Async: Reflection Trigger] → evaluate advice quality for learning loop
```

### Registered Workflows (Callable as Tools)

Each workflow is a compiled LangGraph subgraph, wrapped as a tool:

```python
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

class SpendingArgs(BaseModel):
    customer_id: str = Field(..., description="Customer identifier")
    period: str = Field(..., description="Period in YYYY-MM format")

class GoalArgs(BaseModel):
    customer_id: str = Field(..., description="Customer identifier")

class ProductArgs(BaseModel):
    query: str = Field(..., description="Product search query")
    customer_id: str = Field(None, description="Customer for eligibility filtering")

class ScenarioArgs(BaseModel):
    customer_id: str = Field(..., description="Customer identifier")
    scenario_type: str = Field(..., description="e.g. home_purchase, career_change")
    parameters: dict = Field(default_factory=dict)

spending_tool = StructuredTool.from_function(
    func=lambda args: spending_graph.invoke(args.model_dump()),
    name="spending_analysis",
    description="Run full spending analysis for a customer over a period.",
    args_schema=SpendingArgs,
)
goal_tool = StructuredTool.from_function(
    func=lambda args: goal_graph.invoke(args.model_dump()),
    name="goal_tracking",
    description="Check goal progress, project completion, suggest adjustments.",
    args_schema=GoalArgs,
)
product_tool = StructuredTool.from_function(
    func=lambda args: product_graph.invoke(args.model_dump()),
    name="product_match",
    description="Find and compare relevant Shinhan products for the customer.",
    args_schema=ProductArgs,
)
scenario_tool = StructuredTool.from_function(
    func=lambda args: scenario_graph.invoke(args.model_dump()),
    name="scenario_simulation",
    description="Simulate a financial scenario across Bank/Finance/Securities/Life.",
    args_schema=ScenarioArgs,
)
```

The orchestrator's system prompt instructs it to **prefer workflow tools for known intents** and fall back to atomic MCP tools only for novel requests.

### Evidence Base for This Pattern

**Token economics:** A March 2026 arXiv study on multi-agent financial document processing (10,000 SEC filings) found hierarchical supervisor-worker architectures achieve **98.5% of reflexive/self-correcting accuracy at ~61% of the token cost**. Pure ReAct loops degrade worst under scale, becoming the worst performer above 50,000 documents/day due to correction-loop timeouts (arXiv 2603.22651).

**Industry alignment:** The CFA Institute's 2025 agentic AI report notes that **predefined workflows will remain essential in production finance** for compliance-critical steps that cannot be delegated to probabilistic LLM outputs. Anthropic's "Building Effective Agents" guide explicitly recommends routing — classifying input and directing to specialised follow-up tasks — for cases where "distinct categories are better handled separately."

**Qwen3-8B tool calling caveat:** On BFCL-v3, parallel tool call accuracy is only ~37.5% even for larger Qwen3 variants, vs 81.7% on simple single calls. This means the orchestrator should invoke workflows as **single tool calls** (each workflow handles its own internal parallelism), not dispatch multiple parallel atomic tools. This is another argument for the workflow-as-tool pattern at the 8B model size.

**Implementation note:** Qwen-Agent natively supports parallel function calls in its tool-calling template and handles parsing internally. When using vLLM, do **not** pass `--enable-auto-tool-choice` or `--tool-call-parser hermes` — Qwen-Agent owns that parsing layer. Requires `transformers>=4.51.0`.

### LangGraph Implementation Detail

**Typed state with custom reducers for parallel branches:**

```python
from typing import Annotated, TypedDict
import operator
from langgraph.graph.message import add_messages

class CoachState(TypedDict):
    messages: Annotated[list, add_messages]
    spending_results: Annotated[list, operator.add]   # fan-in from parallel
    goal_results: Annotated[list, operator.add]       # fan-in from parallel
    chart_specs: Annotated[list, operator.add]
    compliance_classification: str                     # last-write-wins
```

**Fan-out / fan-in pattern:**

```python
builder = StateGraph(CoachState)
builder.add_edge(START, "spending_analysis")
builder.add_edge(START, "goal_tracking")           # runs in parallel
builder.add_edge("spending_analysis", "merge")
builder.add_edge("goal_tracking", "merge")
builder.add_edge("merge", "compliance_filter")
builder.add_edge("compliance_filter", END)
```

**Subgraph as tool (Option A — StructuredTool):**

```python
from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool

spending_subgraph = spending_builder.compile()

class SubgraphSpendingArgs(BaseModel):
    customer_id: str = Field(..., description="Customer to analyse")

def run_spending(customer_id: str) -> str:
    result = spending_subgraph.invoke({"customer_id": customer_id})
    return result["spending_summary"]

spending_tool = StructuredTool.from_function(
    func=run_spending,
    name="analyse_spending",
    args_schema=SubgraphSpendingArgs,
    description="Run full spending analysis pipeline for a customer.",
)
```

**Checkpointing (SQLite for PoC):**

```python
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

async with AsyncSqliteSaver.from_conn_string("coach.db") as checkpointer:
    graph = builder.compile(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": customer_id}}
    result = await graph.ainvoke(state, config)
```

**Streaming to FastAPI SSE:**

```python
from sse_starlette.sse import EventSourceResponse

async def event_generator(graph, state, config):
    async for event in graph.astream_events(state, config, version="v2"):
        if event["event"] == "on_chat_model_stream":
            yield {"data": event["data"]["chunk"].content}

@app.post("/chat/{insight_id}")
async def chat(insight_id: str, msg: ChatMessage):
    return EventSourceResponse(event_generator(graph, state, config))
```

---

## 6. Agent Design

### Specialist Agents

#### 1. Spending Analyst Agent

**Purpose:** Categorise transactions, detect patterns, generate spending insights with charts.

**Tools:**
- `categorise_transactions(transactions, period)` — hybrid rule-based + LLM categorisation
- `compute_spending_summary(customer_id, period)` — aggregated spending by category
- `detect_anomalies(customer_id, period)` — unusual spending detection
- `generate_chart_spec(data, chart_type)` — returns structured JSON for frontend rendering

**Workflow:**
1. Call `get_transactions()` — deterministic fetch from Core Banking API
2. Call `categorise_transactions()` — hybrid: rule-based first (known merchants), then LLM for unknowns
3. Call `compute_spending_summary()` — deterministic aggregation with pre-computed percentages and MoM changes
4. Call `generate_spending_chart()` — deterministic chart spec generation
5. LLM retrieves relevant customer learning context (past spending insights from journal)
6. LLM composes natural language summary from tool outputs — interprets, does not calculate
7. Pass through compliance filter

**Transaction Categorisation Strategy:**
- **Layer 1 — Rule-based:** Regex over transaction descriptions for high-frequency payees (electricity, Grab, Shopee, rent, Viettel)
- **Layer 2 — LLM zero-shot:** Qwen3-8B maps uncategorised descriptions to ISO MCC codes
- **Layer 3 — Fine-tuned classifier (future):** **PhoBERT** (VinAI Research, EMNLP 2020) — a RoBERTa-based model pre-trained on Vietnamese text that consistently outperforms multilingual XLM-R on classification tasks. **ViFinClass** (30,000+ Vietnamese financial articles, 2006-2023) demonstrates PhoBERT achieving state-of-the-art on financial text classification

**MCC code caveat:** MCC assignment is structurally inconsistent globally — branches of the same chain frequently hold different MCCs, and Vietnam's large cash-and-informal-merchant economy likely exhibits these gaps more acutely. MCC alone cannot be relied upon; the hybrid rule + LLM + fine-tuned classifier approach is necessary.

**Vietnamese financial terminology:** The CFPB Vietnamese-English Financial Glossary and KPMG Vietnam Glossary can seed the LLM's Vietnamese financial vocabulary for transaction categorisation prompts.

#### 2. Goal Tracker Agent

**Purpose:** Manage savings goals, track progress, project completion dates.

**Tools:**
- `create_goal(customer_id, name, target_amount, target_date)` — persist new goal
- `update_goal_progress(goal_id)` — recalculate based on current balances
- `project_completion(goal_id)` — estimate completion date based on savings rate trend
- `suggest_savings_adjustment(goal_id)` — recommend monthly savings amount changes

**Workflow:**
1. Call `compute_income_pattern()` — deterministic payday detection from transaction regularity
2. Call `compute_savings_rate()` — deterministic disposable income and savings rate calculation
3. Call `project_goal_completion()` — deterministic trajectory projection using historical savings rate
4. Call `generate_goal_progress_chart()` — structured JSON for progress bar + line chart
5. LLM injects relevant lessons from learning journal (e.g., "this customer tends to overspend in December")
6. LLM composes natural language summary from tool outputs — no arithmetic performed by the model

#### 3. Product Recommender Agent

**Purpose:** RAG-based retrieval over Shinhan's product catalogue, returning product information (not advice).

**Tools:**
- `search_products(query, filters)` — vector search over product catalogue
- `compare_products(product_ids)` — side-by-side comparison
- `check_eligibility(customer_id, product_id)` — basic eligibility check against known criteria

**RAG Pipeline:**
- **Vector DB:** Qdrant (embedded mode for PoC — single-process, no infra; client-server mode for production)
- **Embedding:** bge-m3 via `FlagEmbedding` (dense + sparse + ColBERT in one pass; MIRACL Vietnamese nDCG@10: 56.0, MKQA Recall@100: 76.6). Note: `fastembed` does not support bge-m3 ([issue #511](https://github.com/qdrant/fastembed/issues/511)) — use `FlagEmbedding` directly
- **Chunking:** One document per product variant, with metadata fields: `product_type`, `min_income`, `currency`, `interest_rate`, `eligibility_criteria`
- **Retrieval:** Qdrant payload filtering (product type, customer segment) → vector similarity → LLM re-ranking
- **Chunking best practice:** 200-512 token chunks with 20-50 token overlap, using semantic boundaries rather than fixed character splits. Hybrid retrieval (dense embeddings + BM25 keyword search + reranker) is the current enterprise standard (arXiv RAG best-practices survey, 2025)
- **Why Qdrant:** Rich payload filtering eliminates irrelevant products before vector search, built-in quantisation support, and seamless transition from embedded to distributed mode without code changes

**RAG implementation:**

```python
from qdrant_client import QdrantClient, models
from FlagEmbedding import BGEM3FlagModel

# Initialise (embedded mode — no server needed)
client = QdrantClient(path="./qdrant_data")
embedder = BGEM3FlagModel("BAAI/bge-m3", use_fp16=False)  # CPU; use_fp16=True for GPU

# Create collection with dense + sparse vectors for hybrid search
client.create_collection(
    collection_name="products",
    vectors_config={
        "dense": models.VectorParams(size=1024, distance=models.Distance.COSINE),
    },
    sparse_vectors_config={
        "sparse": models.SparseVectorParams(modifier=models.Modifier.IDF),
    },
)

# Create payload indexes for pre-filtering
client.create_payload_index("products", "product_type", models.PayloadSchemaType.KEYWORD)
client.create_payload_index("products", "min_income", models.PayloadSchemaType.FLOAT)

# Embed and insert with metadata payload
output = embedder.encode(
    ["Thẻ tín dụng hoàn tiền Shinhan — cashback 1% mọi giao dịch"],
    return_dense=True, return_sparse=True, max_length=512,
)
client.upsert(
    collection_name="products",
    points=[
        models.PointStruct(
            id=1,
            vector={
                "dense": output["dense_vecs"][0].tolist(),
                "sparse": models.SparseVector(
                    indices=list(output["lexical_weights"][0].keys()),
                    values=list(output["lexical_weights"][0].values()),
                ),
            },
            payload={
                "product_type": "credit_card",
                "min_income": 8000000,
                "interest_rate": 24.0,
                "currency": "VND",
                "description_vi": "Thẻ tín dụng hoàn tiền Shinhan...",
            },
        ),
    ],
)

# Hybrid query: dense + sparse with RRF fusion, payload pre-filtering
query = "thẻ tín dụng cho lương 10 triệu"
q_out = embedder.encode([query], return_dense=True, return_sparse=True)

banking_filter = models.Filter(must=[
    models.FieldCondition(key="product_type", match=models.MatchValue(value="credit_card")),
    models.FieldCondition(key="min_income", range=models.Range(lte=10000000)),
])

results = client.query_points(
    collection_name="products",
    prefetch=[
        models.Prefetch(
            query=q_out["dense_vecs"][0].tolist(), using="dense",
            limit=20, filter=banking_filter,
        ),
        models.Prefetch(
            query=models.SparseVector(
                indices=list(q_out["lexical_weights"][0].keys()),
                values=list(q_out["lexical_weights"][0].values()),
            ),
            using="sparse", limit=20, filter=banking_filter,
        ),
    ],
    query=models.FusionQuery(fusion=models.Fusion.RRF),  # Reciprocal Rank Fusion
    limit=5,
    with_payload=True,
)
```

**Performance at PoC scale (~500 chunks):** End-to-end query (encode + hybrid search + return) is ~100-350ms on CPU, dominated by bge-m3 inference. Vector search itself is 1-5ms. Memory: ~10MB for vectors + ~1.1GB for the bge-m3 model.

**Compliance constraint:** All outputs are framed as "information about available products" — never "we recommend" or "you should."

#### 4. Alert/Nudge Agent

**Purpose:** Proactive, event-driven notifications at optimal moments.

**Triggers:**
- Payday detected → "Your salary of X arrived. You saved Y% last month. Set aside Z for your [goal]?"
- Overspend threshold crossed → "You've spent 80% of your typical monthly food budget with 10 days remaining"
- Goal milestone → "You're 75% of the way to your [holiday fund]!"
- Recurring charge change → "Your [electricity] bill was 30% higher than usual this month"
- Inactivity → "It's been 2 weeks since you checked your savings progress"

**Pattern adapted from:** The nudge timing is informed by income pattern detection — identifying payday from transaction regularity, similar to Plum's auto-savings model.

#### 5. Compliance Filter Agent

**Purpose:** Mandatory final gate before any response reaches the customer.

**Classification:**
- `information` — factual data about products, spending, balances (ALLOWED)
- `guidance` — general financial principles, budgeting tips (ALLOWED with disclaimer)
- `advice` — specific investment recommendations, product endorsements (BLOCKED)

**Implementation:** Lightweight classifier prompt that runs on every response before delivery. Adds standard disclaimers where required. Logs all interactions for audit trail.

**Regulatory context:** The CFPB and global regulators treat AI chatbot output with the **same legal weight as human agent output** — disclaimers do not provide a safe harbour if the bot implies suitability. The classification boundary is **personalisation**: general product education is information; any output tailored to a user's circumstances that implies a recommendation is regulated advice.

**Engagement design for Goal Tracker:** Research shows three features drive highest savings goal engagement: **progress visualisation** (colour-coded bars toward target), **automatic round-up or percentage-based transfers** (zero friction), and **milestone badges/streaks** (gamification). Social sharing has less documented impact.

---

## 7. Proactive Insight Feed UX

### Design Philosophy

The primary interface is **not a chat window**. It is a **ranked insight feed** — a curated stream of AI-generated financial findings that the customer scrolls through, similar to a social media feed but for their finances. Chat is secondary: it activates only when the customer taps an insight to drill down.

### Feed Layout (Matching Shinhan Brand)

```
┌─────────────────────────────────────────┐
│  SOL App → "Financial Coach" Tab        │
│  Brand: #0046FF │ Light mode │ Cards    │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │ ● Spending Alert          Today  │  │
│  │ Food spending is 40% above your  │  │
│  │ 3-month average this month       │  │
│  │ [Donut chart thumbnail]          │  │
│  │                    [Review →]    │  │
│  └───────────────────────────────────┘  │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │ ● Savings Milestone    Yesterday │  │
│  │ You're 72% to your holiday goal  │  │
│  │ (14.4M / 20M VND)               │  │
│  │ [Progress bar]                   │  │
│  │                [See Progress →]  │  │
│  └───────────────────────────────────┘  │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │ ● Life Event Detected     Mar 28 │  │
│  │ It looks like you may be         │  │
│  │ planning a home purchase.        │  │
│  │ We've prepared a scenario.       │  │
│  │              [View Scenario →]   │  │
│  └───────────────────────────────────┘  │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │ ● Product Match           Mar 25 │  │
│  │ Based on your spending pattern,  │  │
│  │ Shinhan Cashback Card could      │  │
│  │ save ~200K/month                 │  │
│  │                [Learn More →]    │  │
│  └───────────────────────────────────┘  │
│                                         │
│  ─────────────────────────────────────  │
│  💬 Ask about your finances...          │
└─────────────────────────────────────────┘
```

### Drill-Down: Tap → Scoped Chat Thread

Tapping any insight card opens a **scoped conversational thread** — not a general assistant. The LLM receives the full context of that insight (relevant transactions, trend data, learning history) pre-loaded.

```
┌─────────────────────────────────────────┐
│  ← Back       Food Spending Alert       │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │     [Donut Chart: Categories]     │  │
│  │  Food 33.6% │ Transport 14.4%    │  │
│  │  Shopping 24.8% │ Bills 20%      │  │
│  └───────────────────────────────────┘  │
│                                         │
│  You've spent 4.2M VND on food this    │
│  month — 40% above your 3-month        │
│  average of 3.0M. Most of the increase │
│  is weekend dining (Fri-Sun).          │
│                                         │
│  Based on your history, this pattern   │
│  tends to happen in months with        │
│  public holidays.                      │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │ [Bar Chart: MoM Food Spending]   │  │
│  └───────────────────────────────────┘  │
│                                         │
│  ─────────────────────────────────────  │
│  💬 "Set a food budget" / "Why did     │
│      weekend spending go up?"           │
└─────────────────────────────────────────┘
```

### Insight Card Priority Ranking

Cards are ranked by a composite score:

```
priority = severity × recency × personalisation_boost
```

Where:
- **severity**: trigger-type weight (life event > anomaly > milestone > info)
- **recency**: exponential decay from detection time
- **personalisation_boost**: higher if the customer has engaged with similar insights before (from learning journal)

Cards are deduplicated via Redis (or in-memory dict for PoC) to prevent repeated alerts on the same trigger.

### Comparable Implementations

**Monzo Trends** (December 2025): Replaced older Summary feature with three sections — Spending (monthly/yearly category breakdowns with interactive graphs), Balance (running balance with "left to spend" factoring in upcoming payments), and Targets (progress against user-set category budgets). Paid-tier users receive AI-suggested targets from historical spending. Section-gated and pull-based, not a ranked feed.

**Revolut** (2025): Announced in-app AI assistant for "smarter money habits," adapting to individual spending history and goals. Includes real-time anomaly detection alerts and behaviour-driven product recommendations.

**UXDA BELLA banking case study**: Swipe-based navigation — centre for contextual notifications, left for pinned AI conversations, right for traditional account views. **Finshape** embedded "AI spotlight" cards directly in the transaction feed — overspending warnings and optimisation prompts inline.

### Notification Fatigue Management

- **43% of banking app users** disable alerts due to overload (Latinia research)
- Average volume: 13.3 (Android) to 15.9 (iOS) notifications per user per month in financial apps
- McKinsey Global Banking Annual Review 2024: real-time personalisation reduces opt-outs by 20%
- The lever is **relevance, not volume reduction** — our per-customer learning loop directly addresses this by ranking insights based on what the customer has engaged with before

### Accessibility Requirements

- WCAG 2.2 AA minimum 4.5:1 colour contrast ratio for text — Shinhan blue (`#0046FF`) on white meets this
- Avoid icon-only CTAs without accessible labels (screen readers announce "button" instead of action)
- 3 in 5 users with visual impairments encounter barriers in financial apps — proactive accessibility is a differentiator

---

## 8. Cross-Entity Financial Digital Twin

### The Opportunity

Shinhan has four entities in Vietnam (Bank, Finance, Securities, Life) that are currently **digital silos** — no shared customer dashboard, no unified AI. Korea is building SuperSOL to consolidate domestically (15.6B KRW budget, June 2026), but Vietnam has no such plan.

Vietnam's Open Banking Circular 64/2024 (effective March 2025) creates a legal path for consent-driven cross-entity data sharing, with banks required to implement customer-information APIs by September 2026.

**No bank globally has shipped a consumer-facing cross-entity financial digital twin.** The only documented precedent is Huawei's FinAgent Booster (infrastructure-level, not customer-facing). This is our highest-value innovation.

### What It Is

A living model of the customer's complete Shinhan financial state — across all entities — that can simulate future scenarios.

### Data Model

```
CustomerDigitalTwin:
  ├── Bank (Shinhan Bank Vietnam)
  │   ├── accounts: [savings, current, fixed_deposit]
  │   ├── balances: {current, projected}
  │   ├── transactions: [12-month history]
  │   └── income_pattern: {payday, regularity, amount}
  │
  ├── Finance (Shinhan Finance)
  │   ├── loans: [personal, auto, consumer]
  │   ├── credit_cards: [active cards, limits, utilisation]
  │   ├── repayment_schedules: [upcoming payments]
  │   └── debt_to_income: float
  │
  ├── Securities (Shinhan Securities Vietnam)
  │   ├── portfolio: [holdings, current_value]
  │   ├── unrealised_gains: float
  │   └── liquidation_options: [ranked by tax efficiency]
  │
  └── Life (Shinhan Life Insurance Vietnam)
      ├── policies: [active policies, coverage]
      ├── premiums: [upcoming, annual total]
      └── coverage_gaps: [identified gaps based on life stage]
```

### Scenario Simulation

The customer (or the background agent triggered by a life event) can run "what if" scenarios:

**Example: "What if I buy a house for 2 billion VND next year?"**

The simulation workflow (deterministic tools, no LLM maths) calculates:

| Entity | Simulation Output |
|---|---|
| **Bank** | Mortgage affordability: max loan 1.6B at 8.5% = 18.2M/month. Remaining savings after down payment: 120M. CASA impact: -400M. |
| **Finance** | Existing consumer loans: 3.2M/month. Combined DTI after mortgage: 62% (above 50% threshold — flag). Recommendation: pay off personal loan first (-85M). |
| **Securities** | Liquidation needed: 300M from portfolio. Tax-efficient order: sell Bond Fund A first (no capital gains), then ETF B (12M tax). |
| **Life** | Current coverage: 500M. With mortgage: recommended coverage increase to 2.5B. Premium increase: +1.2M/month. |
| **Combined** | Monthly cashflow after purchase: +2.1M (tight but viable if personal loan cleared first). Stress test: survives 3-month income loss with emergency fund intact. |

This is rendered as a **scenario comparison card** on the insight feed:

```
┌───────────────────────────────────────┐
│ ● Scenario: Home Purchase 2027       │
│                                       │
│ [Waterfall: Current vs Post-Purchase] │
│                                       │
│ Monthly cashflow: 8.3M → 2.1M        │
│ Recommended: clear personal loan first│
│ Risk: DTI at 62% (above comfort zone)│
│                                       │
│ [View Full Breakdown →]               │
└───────────────────────────────────────┘
```

### Academic Foundation

**FABS (ACM ICAIF 2025, Imperial College London):** An open-source C++ framework for large-scale agent-based digital twins of financial markets. Uses fine-grained parallel execution, decentralised message queues, and adaptive spectral clustering. Achieved 12.52x speed-up over prior state-of-the-art — validating digital twin fidelity with volatility clustering and fat-tailed returns.

**"AI-Powered Financial Digital Twins" (Journal of Next-Gen Research 5.0, 2025):** Five-layer architecture (data fabric, behavioural modelling, simulation environment, decision intelligence, experience orchestration). Uses MAML for rapid customer profile adaptation and hierarchical RL for concurrent savings/credit/spending optimisation. Claims 30-40% improvement in customer experience metrics.

**Existing scenario tools:** Wealthfront Path, Betterment RetireGuide, and Fidelity Planning & Guidance offer scenario simulation but only within their own product silo. None simulates across banking + lending + securities + insurance simultaneously. Our cross-entity approach is architecturally novel.

---

## 9. Predictive Life Event Detection

### How It Works

The background agent's trigger rules include **pattern-based life event detection** — identifying major life transitions from transaction shifts **before the customer explicitly tells us**.

### Detection Patterns

| Transaction Pattern | Detected Event | Confidence Signal | Proactive Action |
|---|---|---|---|
| Baby product purchases, hospital/clinic payments, maternity store transactions | **New baby** | 3+ signals within 2 months | Auto-generate: insurance coverage review, education savings goal, emergency fund check |
| Estate agent fees, furniture store spike, home inspection payments | **Home purchase** | 2+ signals within 1 month | Auto-generate: mortgage simulation across all entities, investment liquidation plan |
| Salary stops, freelance/consulting income appears, co-working space charges | **Career change** | Salary pattern break + new income source | Auto-generate: emergency fund adequacy, income stability assessment, insurance review |
| Wedding venue deposits, jewellery purchases, catering payments | **Marriage** | 3+ signals within 3 months | Auto-generate: joint account suggestion, combined financial plan, life insurance update |
| University tuition payments, textbook purchases, student accommodation | **Child's education** | Seasonal pattern + large education payments | Auto-generate: education fund progress, scholarship/loan options |
| Increased medical spending, pharmacy frequency increase | **Health change** | Sustained over 2+ months | Auto-generate: health insurance coverage check, emergency fund review |

### Implementation

Life event detection is a **two-stage pipeline**:

1. **Stage 1 — Deterministic pattern matching** (Python, no LLM): Transaction descriptions are matched against curated keyword lists per event type. Multiple signals within a time window raise a candidate event with a confidence score.

2. **Stage 2 — LLM confirmation** (Qwen3-8B, thinking ON): The candidate event plus supporting transactions are passed to the LLM for contextual validation. The LLM can reject false positives (e.g., buying baby products as a gift).

Only confirmed events trigger the scenario simulation workflow.

### Privacy and Sensitivity

- Life event detection is **opt-in** — customers consent during onboarding
- Detection results are never shared externally
- Customers can dismiss or correct any detection ("No, I'm not buying a house")
- Dismissed events feed back into the learning loop to reduce future false positives

### Academic Evidence

**Decision Support Systems (2019):** Researchers at a large European bank used fine-grained transaction data from 132,703 customers to predict life events including home purchase, marriage, and childbirth from spending pattern shifts — direct validation that this approach works at scale.

**Multimodal Banking Dataset (arXiv 2024):** 2 million corporate clients across 950 million transactions from a major Russian bank, using event sequences to infer client needs. Demonstrates that transaction sequences carry predictive signal for life stage transitions.

### NLP on Noisy Merchant Descriptions

Vietnamese bank transaction descriptions are not standardised — legacy encoding systems (TCVN/VSCII, Windows-1258) coexist with UTF-8. The practical NLP pipeline for merchant recognition: regex normalisation + NER (spaCy) + embedding-based classification. Bidirectional LSTM and BERT-family transformers are state-of-the-art for entity extraction from abbreviated, character-limited strings.

### False Positive Management

Industry data shows up to 95% of AML alerts are false positives — lifestyle inference has a structurally similar problem. Best practice: track rule-level false positive rates, use customer feedback ("No, I'm not buying a house") to retrain, and apply confidence thresholds before surfacing insights. Our quality gate and learning loop directly address this.

---

## 10. Persistent Learning Loop

**Adapted from:** TojiMoola's self-improving earnings analyst architecture — the core innovation that makes this financial coach progressively better per customer.

### How It Works

```
Customer Interaction
        │
        ▼
[1. Analyse with Context]
   │  Retrieve relevant past lessons for this customer
   │  Inject compressed lesson summary into agent prompt
   │  Generate response
        │
        ▼
[2. Evaluate Outcome] (async, post-response)
   │  Did the customer follow the suggestion?
   │  Did their financial behaviour improve?
   │  Was the insight accurate?
        │
        ▼
[3. Reflect]
   │  LLM evaluates: was the process good? Was the outcome good?
   │  Separates process quality from outcome quality (Van Tharp 2x2)
   │  Prevents reinforcing lucky advice
        │
        ▼
[4. Extract Lesson]
   │  Structured lesson with:
   │  - conditions (when this applies)
   │  - insight (what was learned)
   │  - confidence (how generalisable)
   │  - importance (0-10, adjustable)
        │
        ▼
[5. Quality Gate]
   │  Only persist if:
   │  - Process grade A/B (not lucky)
   │  - Confidence >= 0.70 (generalisable)
        │
        ▼
[6. Store / Evolve]
   │  If cosine similarity > 0.85 with existing lesson → MERGE
   │  Otherwise → store as new lesson
   │  Importance score updated post-outcome (+0.5 if helped, -0.3 if not)
```

### Lesson Retrieval Scoring

When the agent needs context for a new interaction, lessons are scored using a three-component formula:

```
score = normalised(recency) + normalised(importance) + normalised(relevance)
```

Where:
- **recency** = `0.99 ^ days_since_learned` (exponential decay)
- **importance** = `lesson.importance / 10.0` (LLM-assigned, feedback-updated)
- **relevance** = cosine similarity between current query embedding and lesson embedding

Top-k lessons are retrieved, then compressed into 2-3 sentences before injection into the agent prompt — preventing context window bloat.

### Customer-Specific Learning Examples

| Scenario | Lesson Stored | Future Impact |
|---|---|---|
| Customer consistently overspends on dining in weekends | "Customer X overspends on dining Fri-Sun, averaging 40% above weekday spend" | Weekend spending alerts triggered proactively |
| Customer ignores savings nudges sent on Monday mornings | "Customer X does not engage with Monday morning nudges; responds best to Thursday evening" | Nudge timing adjusted per customer |
| Customer asked about home loans 3 times but never applied | "Customer X has recurring interest in home loans but hasn't applied — possible barrier: income threshold or documentation" | Product recommender includes eligibility details and documentation guidance |
| Savings goal was missed due to unexpected medical expense | "Customer X's savings goals are disrupted by medical expenses (~quarterly). Emergency fund recommendation warranted" | Goal tracker factors in medical expense buffer |

### Storage

- **SQLite** for PoC (same as TojiMoola) — tables: `customer_lessons`, `customer_reflections`, `customer_goals`, `customer_credibility`
- **Embeddings** stored as BLOB in SQLite (packed via `struct.pack`)
- No external vector DB needed for per-customer lesson retrieval at PoC scale
- Production upgrade path: PostgreSQL + Qdrant (distributed)

### Implementation Libraries

```python
import aiosqlite        # Async SQLite for lesson/reflection/goal tables
import struct           # Pack/unpack embeddings as BLOB (same pattern as TojiMoola)
from FlagEmbedding import BGEM3FlagModel  # bge-m3 dense+sparse (fastembed does NOT support bge-m3)
from qdrant_client import QdrantClient  # Optional: Qdrant for lesson retrieval at scale
from pydantic import BaseModel, Field

class CustomerLesson(BaseModel):
    """Stored lesson from a customer interaction."""
    lesson_id: str
    customer_id: str
    conditions: str          # When this lesson applies
    insight: str             # What was learned
    error_type: str          # direction | magnitude | confidence | timing | missed_factor
    confidence: float = Field(ge=0, le=1)
    importance: float = Field(ge=0, le=10)
    times_evolved: int = 0
    supporting_months: list[str] = []  # Months that contributed to this lesson
    embedding: bytes | None = None     # Packed via struct.pack

class CustomerReflection(BaseModel):
    """Process/outcome evaluation of an interaction."""
    reflection_id: str
    customer_id: str
    interaction_id: str
    process_grade: str       # A, B, C, D, F
    outcome_quality: str     # good | bad
    quadrant: str            # earned_reward | bad_luck | dumb_luck | just_desserts
    lesson_extracted: bool
```

### Academic Foundation

**FinMem (AAAI 2024):** Three-layer long-term memory — Shallow (daily news, 14-day half-life), Intermediate (quarterly reports, 90-day half-life), Deep (annual reports, 365-day half-life). Semantic retrieval uses a composite score: recency (exponential decay with layer-specific constants) + relevancy (cosine similarity) + importance (piecewise scoring with layer-specific degrading ratio). Top-K events from each layer selected by descending score. Events promoted to deeper layers when access counters indicate criticality. This is the closest prior art to our per-customer learning architecture.

**Mem0 (arXiv 2504.19413):** Two-phase pipeline for production AI agent memory. Extraction phase: ingests latest exchange + rolling summary + recent messages. Update phase: new facts compared against vector DB entries, LLM applies ADD/UPDATE/DELETE/NOOP. Graph variant (Mem0g) stores memories as directed labelled graphs. Performance: 26% improvement over OpenAI's memory, 91% lower p95 latency, 90%+ token cost reduction. Directly applicable pattern for our customer learning store.

**Federated learning frameworks:** WeBank's FATE (Federated AI Technology Enabler) is the most production-tested FL framework for finance. IEEE 2025 published research on privacy-preserving FL specifically for mobile banking personalisation using on-device training with differential privacy.

---

## 11. Federated Customer Learning

### Beyond Per-Customer: Network-Effect Intelligence

The per-customer learning loop (Section 10) makes the coach smarter for each individual. Federated learning makes it smarter for **all customers** — without compromising privacy.

### How It Works

```
Customer A's Learning Journal
    │
    ▼
[Quality Gate] — only high-confidence, high-importance lessons pass
    │
    ▼
[Anonymisation Pipeline]
    │  Strip: customer_id, specific amounts, merchant names, dates
    │  Retain: pattern type, category, demographic band, outcome
    │  Apply: differential privacy (add calibrated noise to aggregates)
    │
    ▼
[Cohort Insight Store]
    │  Keyed by: demographic_band × income_bracket × life_stage
    │  Example: "Young professionals in HCMC (25-35, 8-15M VND/month)
    │            tend to overspend on dining by 30-50% in months with
    │            public holidays. Proactive budget alerts 3 days before
    │            holidays reduce overspend by ~20%."
    │
    ▼
[New Customer B — same cohort]
    │  Receives cohort insights from day one
    │  No cold-start problem — the system is already informed
```

### Cohort Insight Structure

```python
class CohortInsight(BaseModel):
    """Anonymised, aggregated insight derived from multiple customers."""
    cohort_key: str          # e.g., "hcmc_young_professional_mid_income"
    pattern_type: str        # e.g., "seasonal_overspend"
    category: str            # e.g., "dining"
    insight: str             # natural language description
    confidence: float        # 0-1, based on number of supporting customers
    supporting_count: int    # how many customers contributed
    effectiveness: float     # 0-1, how often acting on this improved outcomes
    min_customers: int = 50  # minimum threshold before cohort insight activates
```

### Privacy Guarantees

- **Differential privacy**: Calibrated noise added to all aggregates before storage
- **k-anonymity**: Cohort insights only activate when `supporting_count >= 50` customers
- **No raw data leaves the per-customer store**: Only abstracted patterns with PII stripped
- **Customer opt-out**: Customers can exclude their data from cohort aggregation
- **On-premise only**: Federated learning runs entirely within Shinhan's infrastructure

### The Network Effect

As more customers use the system:
1. Cohort insights become more accurate (more data points)
2. New customers benefit immediately (no cold-start)
3. Rare life events (e.g., career changes) become detectable earlier as the pattern library grows
4. The system's value increases super-linearly with user count — a moat

---

## 12. Data Sources and Integration

### Available Data (from Shinhan's use case brief and cross-entity analysis)

The target teams listed in the brief, plus the cross-entity opportunity, imply access to the following data:

| Data Source | Owner Team | Data Available | Use In Coach |
|---|---|---|---|
| **Transaction History** | Retail Customer Dept. | 12-24 months of transactions, merchant descriptions, amounts, dates | Spending categorisation, pattern detection, income identification |
| **Account Balances** | Retail Customer Dept. | All product balances (savings, current, fixed deposit) | Net worth view, liquidity alerts, CASA growth tracking |
| **Loan & Credit Data** | Retail Lending Dept. | Outstanding loans, repayment schedules, credit limits | Debt-to-income calculation, repayment planning |
| **Card Data** | Card Division | Card transactions, rewards points, billing cycles | Card-specific spending analysis, rewards optimisation |
| **Product Catalogue** | Wealth Management Dept. | All retail products (loans, savings, insurance, cards) with rates and terms | RAG knowledge base for product information |
| **Customer Profile** | Digital Business Unit | Demographics, segment, KYC data, app usage patterns | Personalisation baseline, eligibility filtering |
| **SOL App Behaviour** | Digital Business Unit | Session data, feature usage, notification engagement | Nudge timing optimisation, engagement scoring |

### Cross-Entity Data (for Digital Twin)

| Entity | Data Available | Use In Digital Twin |
|---|---|---|
| **Shinhan Finance** | Consumer loans, credit card balances, repayment schedules | Combined DTI calculation, loan restructuring simulation |
| **Shinhan Securities** | Portfolio holdings, unrealised gains, trade history | Investment liquidation planning, tax-efficient sell orders |
| **Shinhan Life** | Active policies, coverage amounts, premium schedules | Coverage gap analysis, premium impact in scenarios |

**Regulatory enabler:** Vietnam's Open Banking Circular 64/2024 (effective March 2025) mandates consent-driven API data sharing. Banks must implement customer-information APIs by September 2026. This creates the legal framework for cross-entity data flow within the Shinhan group.

**For PoC:** All cross-entity data is synthetic. For production, the Banking Router abstracts real APIs from each entity behind a unified interface.

### Integration Architecture

**Pattern adapted from:** Portfolio-Intelligence-Platform's `MCPRouter` — a compatibility shim that abstracts multiple backend APIs behind a unified tool interface.

```python
import httpx
from functools import lru_cache
from pydantic import BaseModel

class BankingRouter:
    """Unified interface to Shinhan's core banking systems.

    Abstracts Bank, Finance, Securities, and Life APIs behind
    a single call interface. For PoC, backends are synthetic
    data generators. For production, they connect to real APIs.
    """

    def __init__(self, config: dict[str, str]) -> None:
        self._clients: dict[str, httpx.AsyncClient] = {}
        for entity, base_url in config.items():
            self._clients[entity] = httpx.AsyncClient(
                base_url=base_url,
                timeout=30.0,
            )

    async def call(
        self, entity: str, method: str, params: dict
    ) -> dict:
        """Route a call to the appropriate entity API.

        Args:
            entity: One of 'bank', 'finance', 'securities', 'life'.
            method: API method name (e.g. 'get_transactions').
            params: Method parameters.

        Returns:
            API response as dict.
        """
        client = self._clients[entity]
        response = await client.post(
            f"/api/{method}",
            json=params,
        )
        response.raise_for_status()
        return response.json()

    # Convenience methods
    async def call_transaction_api(self, method: str, params: dict) -> dict:
        return await self.call("bank", method, params)

    async def call_product_api(self, method: str, params: dict) -> dict:
        return await self.call("bank", method, params)

    async def call_finance_api(self, method: str, params: dict) -> dict:
        return await self.call("finance", method, params)

    async def call_securities_api(self, method: str, params: dict) -> dict:
        return await self.call("securities", method, params)

    async def call_life_api(self, method: str, params: dict) -> dict:
        return await self.call("life", method, params)
```

For the PoC, these are backed by **synthetic data generators** (SDV or LLM-seeded). For production, they connect to Shinhan's actual core banking APIs.

**Core Banking Systems in Vietnam:** Temenos (T24/Transact) dominates with ~37.5% market share (~12 banks including Military Commercial, Orient Commercial, VPBank). Oracle FLEXCUBE holds ~25%. Shinhan's specific CBS vendor is undisclosed — the global group historically uses its in-house Korean "Nextgen" system.

**NAPAS (Vietnam's payment switch):** Processes 9.56 billion transactions annually (2024, +30% YoY). APIs cover payment initiation, transaction inquiry, void/reversal, and QR lookup. Settlement is sub-10 seconds. Raw merchant metadata resides within individual bank ledgers, not at the NAPAS switch level.

**Data quality caveat:** Transaction description fields are not standardised across Vietnamese banks. Legacy encoding systems (TCVN/VSCII, Windows-1258) coexist with UTF-8, creating mixed-encoding datasets. Free-text transfer descriptions are user-generated and highly inconsistent.

### Caching Strategy

**Pattern adapted from:** Portfolio-Intelligence-Platform's `@cached_async` decorator with per-type TTLs.

| Data Type | TTL | Rationale |
|---|---|---|
| Account balances | 60 seconds | Near real-time for balance queries |
| Transaction history | 4 hours | Doesn't change frequently intra-day |
| Product catalogue | 24 hours | Rates change daily at most |
| Customer profile | 7 days | Rarely changes |
| Spending aggregations | 1 hour | Precomputed summaries |

---

## 13. Visualisation Strategy

### Inline Chat Charts

Charts are rendered **inline in the chat response** — not in a separate analytics tab. This is the interaction model proven by Cleo 3.0 and KakaoBank.

The agent returns structured JSON; the SOL frontend renders natively.

### Chart Specification Format

```json
{
  "chart_type": "donut",
  "title": "Chi tieu thang 3/2026",
  "data": {
    "labels": ["An uong", "Di lai", "Mua sam", "Hoa don", "Khac"],
    "values": [4200000, 1800000, 3100000, 2500000, 900000],
    "currency": "VND"
  },
  "summary": "Ban da chi 12.5 trieu dong trong thang 3. An uong chiem 33.6% — tang 12% so voi thang truoc."
}
```

### Chart Types

| Chart | Use Case | When Triggered |
|---|---|---|
| **Donut/Pie** | Spending category breakdown | "How did I spend this month?" |
| **Stacked Bar** | Budget vs actual by category per month | "Am I on budget?" |
| **Line** | Balance/savings trajectory over time | "How are my savings going?" |
| **Progress Bar** | Goal completion percentage | Goal status queries |
| **Waterfall** | Income minus expense categories = net flow | "Where does my money go?" |
| **Grouped Bar** | Month-over-month comparison | "How does this month compare to last?" |

### Implementation

**Pattern adapted from:** Portfolio-Intelligence-Platform's Plotly chart generators — but outputting JSON specs instead of Plotly figures, since the mobile frontend renders natively.

For the PoC web demo, charts render via Plotly.js in the browser. For SOL integration, the same JSON spec is consumed by the native charting library (Victory Native for React Native, fl_chart for Flutter, or equivalent).

### Chart Library Recommendations

| Library | Best For | Vietnamese Locale |
|---|---|---|
| **ECharts** | Performance, mobile rendering, real-time data | Supports `registerLocale` but `vi` requires custom locale object |
| **Plotly** | Analytical interactivity (zoom, pan, tooltips) | d3-format has known non-English locale issues |
| **Chart.js** | Lightest option, simple dashboards | No locale concerns for basic charts |
| **Victory Native** | React Native, native SVG rendering | N/A (data-only) |
| **fl_chart** | Flutter, native rendering | N/A (data-only) |

For VND formatting, use `Intl.NumberFormat('vi-VN', { currency: 'VND' })` browser API regardless of charting library.

**Structured spec format:** Vega-Lite is the closest to an open standard — a declarative JSON schema describing mark type, data, and encoding. Most widely adopted for LLM-to-chart pipelines because its schema is compact enough for generation. Our chart spec format is inspired by Vega-Lite but simplified for mobile rendering.

### Colour and Accessibility

- WCAG 2.1 AA: 3:1 contrast between adjacent chart elements, 4.5:1 for text
- Blue is the safest anchor colour (rarely affected by colour vision deficiency)
- Shinhan blue (`#0046FF`) is safe as dominant brand colour
- Pair with orange/amber for positive contrast, desaturated red for negative — dual-encode with icons/patterns, not colour alone
- IBM accessibility palette: blue `#648FFF`, orange `#FE6100`, magenta `#DC267F`

---

## 14. Technology Stack

### PoC Stack (Local Development — 12GB GPU)

| Component | Technology | Notes |
|---|---|---|
| **LLM** | Qwen3-8B Q4_K_M GGUF | ~5.2GB weights, leaves ~6.8GB for KV cache |
| **Inference** | llama.cpp (llama-server) | OpenAI-compatible API, lowest overhead for single-user |
| **Context** | 32K tokens (conservative) | Native is 40,960; limited to 32K to fit KV cache in 12GB with Q8 + flash attention |
| **Agent Framework** | Qwen-Agent + LangGraph | Qwen-Agent for native tool parsing, LangGraph for workflow orchestration |
| **Backend API** | FastAPI | REST endpoints for chat, insights, goals, products |
| **Vector DB** | Qdrant (embedded mode) | Product catalogue RAG; payload filtering for metadata; same API as production |
| **Database** | SQLite | Learning journal, customer state, goals |
| **Embeddings** | bge-m3 or qwen3-embedding:0.6b | Vietnamese-capable, lightweight |
| **Frontend** | Next.js + shadcn/ui + Recharts | Deployed on Vercel; Shinhan-branded, mobile-responsive, shareable URL |
| **Synthetic Data** | SDV + LLM-seeded | Realistic Vietnamese banking transactions |
| **Language** | Python 3.11+ | Managed with uv |

### Python Dependencies

```toml
[project]
dependencies = [
    # Agent framework
    "qwen-agent>=0.0.14",           # First-party Qwen tool calling, MCP client, code interpreter
    "langgraph>=0.4",               # Workflow-as-tool orchestration, subgraph compilation
    "langgraph-checkpoint-sqlite>=2.0",  # AsyncSqliteSaver for workflow checkpointing
    "langchain-core>=0.3",          # StructuredTool for wrapping subgraphs as tools

    # LLM client
    "openai>=1.60",                 # OpenAI-compatible client for llama-server / Ollama

    # Backend API
    "fastapi>=0.115",               # REST + WebSocket endpoints
    "uvicorn[standard]>=0.34",      # ASGI server
    "sse-starlette>=2.0",           # Server-Sent Events for streaming insights
    "pydantic>=2.10",               # Typed models for all tool inputs/outputs

    # Vector DB + Embeddings
    "qdrant-client>=1.13",          # Qdrant embedded mode + client-server (same API)
    "FlagEmbedding>=1.3",           # bge-m3 dense+sparse+ColBERT (fastembed doesn't support bge-m3)

    # Database
    "aiosqlite>=0.20",              # Async SQLite for learning journal, goals, state

    # Data processing
    "pandas>=2.2",                  # Transaction aggregation, spending summaries
    "numpy>=2.0",                   # Numerical computation for projections
    "numpy-financial>=1.0",         # Mortgage/loan amortisation (npf.pmt, npf.ipmt)

    # Synthetic data generation
    "sdv>=1.18",                    # Synthetic Data Vault — realistic transaction generation
    "faker>=33.0",                  # Vietnamese locale (vi_VN) for merchant names

    # Visualisation (PoC demo)
    "plotly>=6.0",                  # Interactive charts for web demo
    # Frontend: Next.js + shadcn/ui (separate package.json, deployed on Vercel)

    # NLP / categorisation
    "underthesea>=6.8",             # Vietnamese NLP tokeniser, NER, POS tagging

    # Utilities
    "httpx>=0.28",                  # Async HTTP for Banking Router MCP calls
    "structlog>=24.4",              # Structured logging for audit trail
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
    "ruff>=0.8",
]
fine-tuning = [
    "ms-swift[llm]>=3.0",          # Alibaba ModelScope — native Qwen3 LoRA/QLoRA support
    "transformers>=4.51",           # Required for Qwen3 — earlier versions break silently
    "peft>=0.14",                   # LoRA / QLoRA adapters
    "datasets>=3.0",               # HuggingFace dataset loading
    "accelerate>=1.2",             # Multi-GPU / mixed precision
    "bitsandbytes>=0.45",          # 4-bit QLoRA quantisation
]
```

### Key Library Choices Explained

| Library | Why This Over Alternatives |
|---|---|
| **qwen-agent** | First-party Qwen tool-call parsing. LangChain's Qwen integration has prompt-concatenation bugs. Qwen-Agent handles Hermes template natively. |
| **langgraph** | Workflows compiled as `Runnable`, wrappable as tools via `StructuredTool.from_function()`. LangChain chains don't support this pattern. |
| **FlagEmbedding** | Runs bge-m3 with dense + sparse + ColBERT output in one pass. fastembed does NOT support bge-m3 ([issue #511](https://github.com/qdrant/fastembed/issues/511)). ~1.1GB RAM for model. |
| **qdrant-client** | Embedded mode = in-process, no infra. Same `QdrantClient` API scales to distributed cluster. ChromaDB lacks payload filtering. |
| **underthesea** | Vietnamese-specific NLP: word segmentation, NER, POS tagging. Required for transaction description parsing where PhoBERT is overkill. |
| **numpy-financial** | Deterministic mortgage/loan calculations (`npf.pmt`, `npf.ipmt`, `npf.ppmt`). No LLM involved in financial maths. |
| **sse-starlette** | SSE streaming for pushing insight cards to mobile. Lighter than WebSocket for unidirectional push. |
| **structlog** | Structured JSON logging for regulatory audit trail. Every agent interaction logged with timestamp, customer_id, intent, compliance classification. |

### Recommended llama-server Configuration

```bash
llama-server \
  --model Qwen3-8B-Q4_K_M.gguf \
  --ctx-size 32768 \
  --n-gpu-layers 99 \
  --flash-attn \
  --cache-type-k q8_0 \
  --cache-type-v q8_0 \
  --port 8080
```

### Thinking Mode Strategy

Qwen3-8B supports hybrid thinking mode (`<think>...</think>` blocks):

| Task | Thinking Mode | Rationale |
|---|---|---|
| Intent classification | ON | Needs to reason about ambiguous user requests |
| Interpreting learning journal context | ON | Synthesis across multiple lessons |
| Composing drill-down responses (complex follow-ups) | ON | Multi-paragraph Vietnamese explanations with context |
| Simple balance queries | OFF | Direct tool call, save tokens and latency |
| Product information retrieval | OFF | RAG retrieval, no complex reasoning needed |
| Greeting / small talk | OFF | Immediate response |

Toggle via `enable_thinking=False` in chat template or `/no_think` prefix per turn.

### Deterministic Tools via MCP / Skills

**Critical design principle:** The LLM should never perform mathematical calculations or data extraction directly. These operations are offloaded to deterministic MCP tools that guarantee correctness.

The LLM's role is to **decide which tools to call, interpret the results, and communicate in natural language**. All numerical computation happens in Python functions exposed as tools.

#### Why This Matters

LLMs are unreliable at arithmetic — especially quantised 8B models. Asking "what percentage of my spending is food?" should not involve the LLM doing division. Instead:

1. LLM decides: "I need a spending breakdown for this customer"
2. LLM calls: `compute_spending_summary(customer_id, period)` — a deterministic Python function
3. Tool returns: `{"food": 4200000, "transport": 1800000, ...}` with pre-computed percentages
4. LLM interprets and responds in Vietnamese natural language

#### MCP Tool Categories

**Data Extraction Tools** — deterministic retrieval, no LLM reasoning:

```python
# Spending & Transactions
get_transactions(customer_id, start_date, end_date, category?) -> list[Transaction]
compute_spending_summary(customer_id, period) -> SpendingSummary  # pre-aggregated with percentages
compute_income_pattern(customer_id) -> IncomePattern  # payday detection, regularity score
get_category_trend(customer_id, category, months) -> list[MonthlyAmount]
detect_recurring_charges(customer_id) -> list[RecurringCharge]

# Account & Balance
get_account_balances(customer_id) -> list[AccountBalance]
compute_net_worth(customer_id) -> NetWorth  # assets minus liabilities
get_debt_summary(customer_id) -> DebtSummary  # total debt, DTI ratio, repayment schedule
```

**Mathematical / Projection Tools** — deterministic computation:

```python
# Goal Calculations
project_goal_completion(goal_id) -> GoalProjection  # date, monthly_required, on_track boolean
compute_savings_rate(customer_id, months) -> SavingsRate  # percentage, trend direction
calculate_loan_affordability(customer_id, loan_amount, term, rate) -> AffordabilityResult

# Budget Analysis
compute_budget_variance(customer_id, period) -> BudgetVariance  # per-category over/under
compute_month_over_month_change(customer_id, category?) -> list[MoMChange]  # absolute and percentage
```

**Chart Generation Tools** — structured JSON output, no LLM involvement in data:

```python
# The LLM chooses the chart type; the tool computes and formats the data
generate_spending_chart(customer_id, period, chart_type) -> ChartSpec
generate_goal_progress_chart(goal_id) -> ChartSpec
generate_trend_chart(customer_id, category, months) -> ChartSpec
generate_cashflow_waterfall(customer_id, period) -> ChartSpec
```

**Product & RAG Tools** — retrieval, not generation:

```python
search_products(query, filters: ProductFilters) -> list[ProductInfo]
check_eligibility(customer_id, product_id) -> EligibilityResult
compare_products(product_ids: list[str]) -> ComparisonTable
```

#### Tool Execution Flow

```
User: "Thang nay toi chi tieu bao nhieu cho an uong?"
       (How much did I spend on food this month?)
           │
           ▼
[LLM — Thinking ON]
  "User wants food spending for current month.
   I need compute_spending_summary and possibly a chart."
           │
           ▼
[Tool Call] compute_spending_summary(customer_id="C001", period="2026-03")
  Returns: { "food": 4200000, "food_pct": 33.6, "total": 12500000,
             "food_mom_change": +12.3, "currency": "VND" }
           │
           ▼
[Tool Call] generate_spending_chart(customer_id="C001", period="2026-03", chart_type="donut")
  Returns: { "chart_type": "donut", "data": {...}, "title": "..." }
           │
           ▼
[LLM — Thinking OFF, just compose response]
  "Thang 3 ban da chi 4.2 trieu dong cho an uong, chiem 33.6% tong chi tieu.
   Tang 12.3% so voi thang truoc."
  + chart_spec attached
```

This pattern ensures every number the customer sees is computed by Python, not hallucinated by the LLM.

### Qwen3-8B Benchmarks and Practical Notes

**BFCL (Berkeley Function Calling Leaderboard):** Qwen3-32B sits at 75.7% on BFCL v3 (top open model as of April 2026). Qwen3-8B is listed but specific score not yet surfaced publicly. For reference, GLM 4.5 leads overall at 76.7%. Llama 3.1-8B and Mistral-7B do not appear in the top-22, confirming Qwen3 is meaningfully ahead on structured tool use.

**Qwen-Agent framework:** Beyond bare tool calling, provides Docker-sandboxed code interpreter, MCP client support (added May 2025), native vLLM tool-call parsing, RAG pipelines, and Gradio GUI scaffold. The key advantage over LangChain is first-party Qwen chat-template awareness — avoiding prompt-concatenation bugs that affect third-party integrations.

**llama.cpp Qwen3 status:** Qwen3 converts cleanly from bf16 via `convert-hf-to-gguf.py`. Recommended floor: Q4_K_M with imatrix calibration. A crash bug exists for certain Qwen3.5-27B builds (issue #19906) but is not reported for Qwen3-8B.

**llama-server vs Ollama:** llama-server gained native MCP client support in March 2026 (`--webui-mcp-proxy`), enabling agentic loops directly in-server. For banking agent requiring fine-grained tool-call streaming and MCP integration, llama-server is the stronger choice.

**bge-m3 for Vietnamese:** bge-m3 via `FlagEmbedding` (not fastembed). Supports dense + sparse + ColBERT retrieval modes in one encode pass. MIRACL Vietnamese nDCG@10: 56.0, MKQA Recall@100: 76.6 (equal or better than multilingual-e5-large). Vietnamese tokenisation handled natively by its multilingual BPE tokeniser — no pre-tokenisation needed. ~1.1GB model, 100-300ms per query on CPU.

**Qdrant embedded mode:** Runs in-process with the Python application, no separate server. Suitable for collections up to ~1M vectors on a single machine. Memory usage scales linearly with vector count (~1KB per 768-dim vector). Seamless migration to client-server mode with zero code changes.

---

### Qwen-Agent: Implementation Reference

Qwen-Agent uses a three-tier design: UI layer (Gradio/Python API), Agent layer, and LLM/Tool layer.

**Agent hierarchy:**

| Class | Role |
|---|---|
| `Agent` | Abstract base — all agents implement `_run()` |
| `FnCallAgent` | Iterative tool-calling loop (max 8 iterations per run) |
| `Assistant` | Extends `FnCallAgent` with RAG via a `Memory` component |
| `ReActChat` | Text-based ReAct prompting instead of native function-calling |
| `MultiAgentHub` | Routes tasks across multiple agents |

**Tool definition:**

```python
import json5
from qwen_agent.tools.base import BaseTool, register_tool

@register_tool('compute_spending_summary')
class ComputeSpendingSummary(BaseTool):
    """Compute spending breakdown for a customer over a period."""

    description = 'Aggregate spending by category with percentages and MoM changes.'
    parameters = {
        'type': 'object',
        'properties': {
            'customer_id': {'type': 'string', 'description': 'Customer identifier'},
            'period': {'type': 'string', 'description': 'Period in YYYY-MM format'},
        },
        'required': ['customer_id', 'period'],
    }

    def call(self, params: str, **kwargs) -> str:
        args = json5.loads(params)
        # Deterministic computation — no LLM involved
        summary = compute_spending(args['customer_id'], args['period'])
        return json5.dumps(summary)
```

**Connecting to llama-server:**

```python
llm_cfg = {
    'model': 'qwen3:8b',
    'model_server': 'http://localhost:8080/v1',  # llama-server
    'api_key': 'EMPTY',
    'generate_cfg': {'max_input_tokens': 28000, 'max_retries': 3},
}
bot = Assistant(llm=llm_cfg, function_list=['compute_spending_summary'])
```

**MCP integration (added May 2025):**

```python
mcp_config = {
    'mcpServers': {
        'banking_tools': {
            'url': 'http://localhost:9000/sse',  # SSE transport
            'headers': {'Authorization': 'Bearer TOKEN'},
        },
    }
}
bot = Assistant(llm=llm_cfg, function_list=[mcp_config])
```

Three transport types supported: `stdio`, `SSE`, `streamable-http`. Qwen-Agent acts as MCP **client** only — it cannot expose tools as an MCP server.

---

### Vietnamese NLP: underthesea Integration

underthesea provides the preprocessing layer before Qwen3 receives transaction descriptions.

**Key capabilities:** word segmentation (CRF-based, 80% F1), NER (PER/ORG/LOC/MISC), banking intent classification (`domain='bank'`), text normalisation (NFC diacritic recomposition).

```python
from underthesea import word_tokenize, text_normalize, ner
import re

def normalise_transaction(desc: str) -> str:
    """Normalise a raw banking transaction description for LLM input.

    Args:
        desc: Raw transaction description from core banking.

    Returns:
        Normalised, tokenised string.
    """
    desc = text_normalize(desc.upper().strip())
    desc = re.sub(r'[/\\|]+', ' ', desc)              # Split ATM separators
    desc = re.sub(r'\b(\d{6,})\b', 'ACCTNUM', desc)   # Mask account numbers
    return word_tokenize(desc, format='text')

def extract_financial_entities(text: str) -> dict:
    """Extract structured entities from a Vietnamese transaction.

    Args:
        text: Vietnamese transaction description.

    Returns:
        Dict with ner_entities, amounts, and dates.
    """
    entities = ner(text)
    amounts = re.findall(r'\d[\d.,]*\s*(?:đồng|VND|k|tr|triệu)', text, re.I)
    dates = re.findall(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', text)
    return {
        'ner_entities': [(w, t) for *_, w, t in entities if t != 'O'],
        'amounts': amounts,
        'dates': dates,
    }
```

**Limitation:** underthesea NER has no AMOUNT, DATE, or MERCHANT_CODE types — those need regex extraction (shown above). Segmentation accuracy on domain-shifted banking abbreviations (e.g. `GD/ATM/BIDV`) is untested. For legacy TCVN3/VSCII-encoded data from older core banking systems, explicit re-encoding via `cp1258` is needed before underthesea can process.

---

### Qwen3-8B Fine-Tuning Guide

#### Model Architecture

| Parameter | Qwen3-8B |
|---|---|
| Parameters | 8.2B |
| Layers | 36 |
| Hidden dimension | 4,096 |
| Attention heads | 32 (GQA: 8 KV heads) |
| Vocab size | 151,936 (includes Vietnamese subword units) |
| Context length | 40,960 (native), 128K (YaRN extended) |
| QKV bias | **False** (removed in Qwen3; was present in Qwen2.5) |
| QK-Norm | **Yes** (layer norm on Q and K before attention — new in Qwen3) |
| Architecture | Dense transformer (not MoE) |
| Activation | SwiGLU |
| Positional encoding | RoPE |

Key difference from Qwen2.5-7B: Qwen3-8B adds 1.2B parameters, expands vocabulary for 119 languages (from 29), and introduces hybrid thinking mode (`<think>` tags).

#### Recommended Fine-Tuning Stack

**Framework:** `ms-swift` (Alibaba ModelScope) or `LLaMA-Factory`. Both support Qwen3 natively with LoRA/QLoRA. Unsloth supports Qwen3 and offers 2x speed-up on consumer GPUs via fused kernels.

```bash
# Install ms-swift
uv add 'ms-swift[llm]'

# LoRA fine-tuning on a single 12GB GPU (QLoRA 4-bit)
swift sft \
  --model Qwen/Qwen3-8B \
  --dataset your_banking_data.jsonl \
  --quantization_bit 4 \
  --lora_rank 16 \
  --lora_alpha 32 \
  --target_modules q_proj k_proj v_proj o_proj gate_proj up_proj down_proj \
  --batch_size 1 \
  --gradient_accumulation_steps 16 \
  --learning_rate 1e-4 \
  --num_train_epochs 3 \
  --max_length 4096
```

#### LoRA Configuration for Qwen3-8B

| Parameter | Recommended Value | Notes |
|---|---|---|
| **rank (r)** | 16-32 | 16 for PoC, 32 for production quality |
| **alpha** | 2x rank (32-64) | Standard ratio |
| **target_modules** | `q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj` | All linear layers for maximum adaptation |
| **dropout** | 0.05 | Prevents overfitting on small datasets |
| **learning_rate** | 1e-4 (QLoRA) / 2e-5 (LoRA) | QLoRA needs higher LR |

#### Hardware for Fine-Tuning

| Method | VRAM | GPU | Time (1K samples) | Cost |
|---|---|---|---|---|
| QLoRA (4-bit) | **10-12 GB** | RTX 3060 12GB | ~2-4 hours | ~$0 (local) |
| LoRA (16-bit) | ~20 GB | RTX 4090 24GB | ~1-2 hours | ~$2-4 cloud |
| Full fine-tune | ~65 GB | 2x A100 80GB | ~4-8 hours | ~$50-100 cloud |

**QLoRA on 12GB is viable** — batch_size=1 with gradient_accumulation_steps=16 gives effective batch size 16. Use `--max_length 4096` to avoid OOM on long sequences.

#### Training Data Format

Qwen3 uses a **ChatML-style template** with tool definitions. Training JSONL for tool-calling fine-tuning:

```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are a Vietnamese financial coach. Use tools for all calculations."
    },
    {
      "role": "user",
      "content": "Tháng này tôi chi tiêu bao nhiêu cho ăn uống?"
    },
    {
      "role": "assistant",
      "content": "",
      "tool_calls": [
        {
          "type": "function",
          "function": {
            "name": "compute_spending_summary",
            "arguments": "{\"customer_id\": \"C001\", \"period\": \"2026-03\"}"
          }
        }
      ]
    },
    {
      "role": "tool",
      "name": "compute_spending_summary",
      "content": "{\"food\": 4200000, \"food_pct\": 33.6, \"total\": 12500000}"
    },
    {
      "role": "assistant",
      "content": "Tháng 3, bạn đã chi 4,2 triệu đồng cho ăn uống, chiếm 33,6% tổng chi tiêu."
    }
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "compute_spending_summary",
        "description": "Compute spending breakdown by category with percentages.",
        "parameters": {
          "type": "object",
          "properties": {
            "customer_id": {"type": "string"},
            "period": {"type": "string"}
          },
          "required": ["customer_id", "period"]
        }
      }
    }
  ]
}
```

#### Minimum Dataset Requirements

| Task | Min Examples | Quality Notes |
|---|---|---|
| Vietnamese banking terminology | 500-1,000 | Diverse transaction types, merchant names |
| Tool-calling improvement | 200-500 | Cover all registered tools, include multi-step |
| Thinking mode control | 100-200 | Examples of when to think vs not think |
| Compliance classification | 200-300 | Information vs guidance vs advice boundary cases |
| **Total recommended** | **1,000-2,000** | Quality > quantity. Hand-curated > LLM-generated. |

#### Thinking Mode and Fine-Tuning

Fine-tuning **does** affect thinking mode. To control when thinking activates:
- Include training examples **with** `<think>` blocks for complex reasoning tasks
- Include training examples **without** `<think>` blocks (or with `/no_think` prefix) for direct tool calls
- The model learns the pattern: complex intent → think; direct lookup → act immediately

#### Evaluation After Fine-Tuning

| Metric | How to Measure |
|---|---|
| Tool-calling accuracy | % of correct tool selections on held-out test set (target: >90%) |
| Vietnamese fluency | Human evaluation on 50 response samples (native speakers) |
| Compliance classification | Precision/recall on information vs advice boundary (target: >95% recall on blocking advice) |
| Numerical accuracy | 100% — all numbers come from deterministic tools, not the LLM |
| Latency | Time-to-first-token on llama-server (target: <500ms at Q4_K_M) |

---

### Frontend: Next.js + shadcn/ui (Deployed on Vercel)

Built using **Vercel skills** (deploy-to-vercel, vercel-react-best-practices, vercel-composition-patterns, shadcn, web-design-guidelines) for production-quality output.

**Why not Streamlit:** Streamlit looks like a data science notebook. For an executive banking demo, a branded Next.js app with shadcn components produces pixel-perfect UI that matches production app quality. Vercel gives shareable preview URLs with no setup for stakeholders.

**Frontend dependencies (package.json):**

```json
{
  "dependencies": {
    "next": "^15",
    "react": "^19",
    "recharts": "^2.15",
    "tailwindcss": "^4",
    "class-variance-authority": "^0.7",
    "clsx": "^2",
    "lucide-react": "^0.460"
  }
}
```

**Shinhan Blue theming (globals.css):**

```css
:root {
  --primary: oklch(0.45 0.27 264);          /* #0046FF Shinhan Blue */
  --primary-foreground: oklch(0.98 0 0);     /* Near-white on blue */
  --secondary: oklch(0.55 0.20 264);         /* #2878F5 Royal Blue */
  --accent: oklch(0.65 0.15 264);            /* #4BAFF5 Sky Blue */
  --background: oklch(1 0 0);                /* White */
  --card: oklch(0.98 0.01 264);              /* #F0F4FF Light blue card bg */
}
```

All shadcn components pick up `--primary` automatically — no per-component colour overrides needed.

**Insight feed card:**

```tsx
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ChartContainer, ChartConfig } from "@/components/ui/chart";
import { PieChart, Pie } from "recharts";

function InsightCard({ insight }: { insight: Insight }) {
  return (
    <Card className="w-full cursor-pointer hover:border-primary transition-colors">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium">{insight.title}</CardTitle>
        <Badge variant="outline">{insight.date}</Badge>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">{insight.summary}</p>
        {insight.chartSpec && (
          <ChartContainer config={chartConfig} className="h-[120px] mt-3">
            <PieChart><Pie data={insight.chartSpec.data} dataKey="value" /></PieChart>
          </ChartContainer>
        )}
      </CardContent>
    </Card>
  );
}
```

**Chat with inline charts (drill-down view):**

```tsx
// ChatInput is a custom component — install via: npx shadcn@latest add https://github.com/jakobhoeg/shadcn-chat
import { ChatInput } from "@/components/ui/chat-input";

function DrillDown({ insight }: { insight: Insight }) {
  return (
    <div className="flex flex-col h-full">
      {/* Assistant message with inline chart */}
      <div className="rounded-lg bg-muted p-3 max-w-sm">
        <p className="text-sm mb-2">{insight.explanation}</p>
        <ChartContainer config={config} className="h-[160px] w-full">
          <PieChart>...</PieChart>
        </ChartContainer>
      </div>

      {/* Chat input */}
      <div className="mt-auto pt-4">
        <ChatInput placeholder="Hỏi về tài chính của bạn..." />
      </div>
    </div>
  );
}
```

**SSE consumption from FastAPI backend:**

```tsx
"use client";
import { useEffect, useState } from "react";

export function useInsightStream(customerId: string) {
  const [insights, setInsights] = useState<Insight[]>([]);

  useEffect(() => {
    const es = new EventSource(
      `${process.env.NEXT_PUBLIC_API_URL}/stream/${customerId}`
    );
    es.onmessage = (event) => {
      const insight = JSON.parse(event.data);
      setInsights((prev) => [insight, ...prev]);
    };
    return () => es.close();
  }, [customerId]);

  return insights;
}
```

**Responsive insight feed layout:**

```tsx
<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 p-4">
  {insights.map((item) => (
    <InsightCard key={item.id} insight={item} />
  ))}
</div>
```

**Deployment:** Vercel hosts the Next.js frontend. FastAPI backend runs separately (Railway, Render, or Shinhan's own infra). Vercel's Next.js + FastAPI starter template supports both in a single repo if needed.

---

## 15. Regulatory Compliance

### Vietnam Regulatory Landscape

| Regulation | Status | Impact |
|---|---|---|
| **SBV AI Circular** | Draft, expected effective March 2026, grace period to September 2027 | Mandates safety requirements, risk management, customer rights for AI in banking |
| **Decree 94/2025/ND-CP** | Effective July 2025 | Fintech regulatory sandbox — **robo-advisory explicitly excluded** |
| **Circular 121/2022/TT-BTC** | Active | Investment advice must be based on reasonable, reliable analysis |
| **Decree 13/2023/ND-CP (Personal Data Protection)** | Effective 1 July 2023 | Consent-based data processing; sensitive data (financial records) triggers enhanced obligations |
| **Law on Digital Technology Industry** | Effective 1 January 2026 | Finance designated high-risk; mandatory AI registration, human oversight, operational logging |

### Compliance Architecture

1. **Scope v1 to non-advisory features only:**
   - Spending insights and categorisation (information)
   - Savings goals and nudges (guidance)
   - Product information lookup (information)
   - Budget tracking with visualisation (information)
   - **No investment recommendations** until regulatory clarity

2. **Compliance Filter Agent** as a first-class component (not an afterthought):
   - Classifies every output as `information`, `guidance`, or `advice`
   - Blocks `advice` category responses
   - Adds disclaimers to `guidance` responses
   - Logs all interactions for audit trail

3. **Data handling:**
   - All customer data processed on-premise or in Shinhan's private cloud
   - No data sent to external LLM APIs (Qwen runs locally)
   - Consent-based data access aligned with upcoming Personal Data Protection Law

4. **Audit trail:**
   - Every agent interaction logged with: timestamp, customer_id, intent, response, compliance_classification
   - Learning journal entries are traceable and auditable

### Detailed Regulatory Analysis

**Decree No. 94/2025/ND-CP (Fintech Sandbox):** Effective 1 July 2025. Participants must submit risk management protocols, operate IT systems within Vietnam, file quarterly progress reports to the SBV, and may pilot for up to two years (extendable to three).

**Law on Digital Technology Industry (June 2025, effective 1 January 2026):** Designates finance as a high-risk sector requiring pre-market government assessment, mandatory registration in a National AI Database, human oversight, operational logging, and incident suspension powers.

**Decree 13/2023 (Personal Data Protection):** Consent must be explicit, voluntary, and informed — pre-ticked boxes and silence are invalid. Sensitive data (biometrics, financial records) triggers enhanced obligations. Cross-border transfers require impact assessment filed with Ministry of Public Security within 60 days. Unlike GDPR, no "legitimate interests" basis — consent is the near-universal requirement.

**Circular 09/2020/TT-NHNN (Data Localisation):** Banks maintaining systems outside Vietnam must store Vietnamese customer personal and transaction data within Vietnam. Level 3+ systems require backup and disaster recovery on Vietnamese infrastructure. This reinforces the on-premise Qwen deployment strategy.

**ASEAN benchmarks:** MAS (Singapore) applies Financial Advisers Act to digital advisers with AI Risk Management Guidelines (2025) mandating board oversight, lifecycle controls, and explainability. Thailand SEC encourages robo-advisory under a five-step client-servicing framework. Vietnam is most likely to follow the MAS model.

---

## 16. PoC Scope

### What We Build (Minimum Viable Demo)

| Feature | Description | Component |
|---|---|---|
| **Proactive insight feed** | Ranked cards generated autonomously from transaction stream | Background Agent + Trigger Rules |
| **Drill-down scoped chat** | Tap any card → contextual conversation with charts | Reactive Orchestrator |
| **Spending analysis workflow** | Auto-categorise, summarise, chart — invoked as a tool | LangGraph Workflow |
| **Savings goal tracking** | Create goals, track progress, project completion | LangGraph Workflow |
| **Product information RAG** | "What credit cards are available?" via Qdrant | Product Match Workflow |
| **Cross-entity scenario simulation** | "What if I buy a house?" across Bank + Finance + Securities + Life | Digital Twin + Simulation Workflow |
| **Life event detection** | Pattern-based detection from transaction shifts | Trigger Rules + LLM Confirmation |
| **Per-customer learning loop** | Quality-gated lessons, semantic retrieval, importance feedback | Learning Journal |
| **Federated cohort insights** | Anonymised patterns benefit similar customers | Cohort Store |
| **Compliance filtering** | All outputs classified and gated before delivery | Compliance Filter |
| **Multilingual** | Vietnamese + English (Korean as stretch) | Qwen3 multilingual |
| **Shinhan-branded UI** | Matching #0046FF palette, card-based, mobile-responsive | Next.js + shadcn/ui on Vercel |

### What We Don't Build (PoC)

- Real core banking API integration (synthetic data across all 4 entities)
- Native mobile UI (web demo styled to match SOL instead)
- Voice interaction
- Investment recommendations (regulatory constraint)
- Real-time streaming infra (polling loop simulates streaming for demo)

### PoC Best Practices from Research

**Timeline:** Banking AI PoCs typically run 8-16 weeks. A focused 4-8 week sprint is achievable with narrow scope: one user persona, 3-5 insight types, single data source, and 10-20 internal testers. The FCA's AI Live Testing initiative confirms regulators expect incremental iteration, not full-scale deployment.

**Demo framework:** **Next.js + shadcn/ui deployed on Vercel** — built using Vercel skills (deploy-to-vercel, vercel-react-best-practices, shadcn, web-design-guidelines). Produces pixel-perfect branded UI that matches production app quality. Vercel gives shareable preview URLs with no setup for stakeholders. shadcn's built-in Chart component (Recharts) handles all financial visualisations. Banking decision-makers evaluate polish as a proxy for production readiness — a proper React app dramatically outperforms Streamlit/Gradio in boardroom settings.

**Synthetic data:** No off-the-shelf tool generates Vietnamese-style transaction descriptions (NAPAS transfers, VietQR merchant names). Practical approach: hand-craft a Vietnamese merchant taxonomy and wrap Faker (`vi_VN` locale) around it. Data only needs to be realistic enough to surface believable insight triggers.

**Key PoC metrics:**
- **Insight acceptance rate**: how often users act on a coach suggestion (core PoC signal)
- **Session depth**: how deep users drill into insights
- **Cross-sell lift**: AI targeting achieves up to 2x conversion vs baseline in production systems
- **Engagement**: AI coaching platforms report up to 73% engagement on proactive nudges

**Common failure mode:** 72% of AI failures stem from data infrastructure issues, not algorithms. Over-scoping is the dominant PoC killer — one hypothesis per sprint.

### Synthetic Data Requirements

| Dataset | Contents | Volume |
|---|---|---|
| **Bank transactions** | 12 months of realistic Vietnamese transactions (merchants, amounts, dates) | 5-10 customer profiles, ~500 transactions each |
| **Finance data** | Consumer loans, credit card balances, repayment schedules | Per customer, 1-3 products |
| **Securities data** | Portfolio holdings, valuations, trade history | Per customer, 3-10 holdings |
| **Life insurance data** | Policies, coverage, premiums | Per customer, 1-2 policies |
| **Product catalogue** | Full Shinhan product catalogue across all 4 entities | ~50 products |
| **Customer profiles** | Demographics, income bands, segments, life stages | 5-10 profiles with embedded life event signals |
| **Life event profiles** | 2-3 customers with planted life event transaction patterns (baby, home purchase, career change) | Embedded in transaction data |

### Synthetic Data Generation Code

```python
from sdv.metadata import SingleTableMetadata  # Metadata class renamed in SDV >= 1.0
from sdv.single_table import GaussianCopulaSynthesizer  # Faster than CTGAN for PoC
from faker import Faker
import pandas as pd
import numpy as np

fake = Faker('vi_VN')

# Vietnamese merchant taxonomy
MERCHANTS = {
    'food': ['Grab Food', 'ShopeeFood', 'Pho 24', 'Bún Chả Hương Liên', 'Circle K'],
    'transport': ['Grab', 'Be', 'Xăng dầu Petrolimex', 'VietJet Air'],
    'shopping': ['Shopee', 'Lazada', 'Thế Giới Di Động', 'Uniqlo VN'],
    'bills': ['EVN Hà Nội', 'Viettel', 'VNPT', 'Nước sạch Hà Nội'],
    'health': ['Bệnh viện Bạch Mai', 'Nhà thuốc Long Châu', 'Medicare VN'],
}

def generate_napas_description(category: str, merchant: str) -> str:
    """Generate a realistic NAPAS-style transaction description.

    Args:
        category: Spending category key.
        merchant: Merchant name.

    Returns:
        NAPAS-format transaction description string.
    """
    ref = fake.bothify(text='TF##########')
    return f"CT DEN {merchant} {ref}"

def plant_life_event(df: pd.DataFrame, customer_id: str, event: str, month: str) -> pd.DataFrame:
    """Insert life event transaction patterns into synthetic data.

    Args:
        df: Transaction DataFrame.
        customer_id: Target customer.
        event: Event type ('baby', 'home_purchase', 'career_change').
        month: Target month (YYYY-MM).

    Returns:
        DataFrame with planted life event transactions.
    """
    patterns = {
        'baby': [('health', 'Bệnh viện Phụ sản', 5000000),
                 ('shopping', 'Kids Plaza', 2000000),
                 ('shopping', 'Con Cưng', 1500000)],
        'home_purchase': [('bills', 'Công ty BĐS Vinhomes', 50000000),
                          ('bills', 'Nội thất IKEA VN', 15000000)],
    }
    rows = []
    for cat, merchant, amount in patterns.get(event, []):
        rows.append({
            'customer_id': customer_id,
            'date': f"{month}-15",
            'amount': amount + np.random.randint(-500000, 500000),
            'category': cat,
            'merchant': merchant,
            'description': generate_napas_description(cat, merchant),
        })
    return pd.concat([df, pd.DataFrame(rows)], ignore_index=True)
```

---

## 17. Scale-Up Path

The PoC runs on a single 12GB GPU. The solution architecture is identical at scale — only the compute layer changes.

### Compute Scale-Up Options

| Stage | Model | Hardware | Concurrent Users | Monthly Cost |
|---|---|---|---|---|
| **PoC** | Qwen3-8B Q4_K_M | 1x RTX 3060 12GB | 1-2 | ~$0 (local) |
| **Pilot (100 users)** | Qwen3-14B FP8 | 1x A100 80GB | 10-20 | ~$1,500-2,000 |
| **Production (1,000 users)** | Qwen3-14B FP8 | 4x A100 80GB | 50-80 | ~$6,000-9,000 |
| **Scale (10,000+ users)** | Qwen3-32B FP8 | 2x H100 80GB + horizontal | 200+ | ~$12,000-24,000 |

### Inference Backend Scale-Up

| Stage | Backend | Why |
|---|---|---|
| PoC | llama.cpp / Ollama | Simplest, single-user, no config overhead |
| Pilot | vLLM | Paged attention, better batching |
| Production | SGLang | 29% throughput advantage over vLLM; 6x better for shared system prompts (our use case) |

### Database Scale-Up

| Stage | Database | Why |
|---|---|---|
| PoC | SQLite | Zero-infra, single-file |
| Pilot | PostgreSQL | Multi-user, ACID, concurrent access |
| Production | PostgreSQL + Qdrant (distributed) | PostgreSQL for relational data; Qdrant cluster for vector search at scale |

### Model Quality Scale-Up

| Stage | Approach |
|---|---|
| PoC | Qwen3-8B Q4 — general-purpose, zero fine-tuning |
| Pilot | Qwen3-14B FP8 — higher quality, still general-purpose |
| Production | Fine-tuned Qwen3-14B on Vietnamese banking terminology + customer interaction data |
| Advanced | Specialist fine-tuned models per agent (spending analyst, product recommender) similar to TojiMoola's specialist sub-models |

### Vietnam-Specific Cloud GPU Options

| Provider | GPUs Available | Notes |
|---|---|---|
| **GreenNode / VNG Cloud** | H100, A40, L40S, RTX 5090 | Two AI data centres (STT VNG HCMC 1 & 2) operational H1 2026 |
| **FPT AI Factory** | Thousands of H100 (HGX B300) | Operational since January 2025, GPU Cloud for inference/training |
| **CMC Cloud** | General compute | Lags on GPU-specific offerings |
| **AWS/GCP Singapore** | Full GPU range | Higher latency, data localisation concerns |

Vietnam's Cybersecurity Law imposes data localisation requirements on certain financial data, making local providers strategically important for Shinhan.

**On-premise costs:** Single H100 80GB SXM: USD 30,000-40,000. 8-GPU server: USD 200,000-400,000 fully loaded. Lead times: 5-6 months. 3-5 year hardware refresh cycles.

### SGLang Prefix Caching for Tool-Calling Agents

SGLang's RadixAttention stores KV activations in a radix tree keyed on exact byte sequences. For agentic workloads with shared system prompts and tool schemas, cache hit rates reach **75-95%**, with TTFT of ~41ms at 2,620 tok/s. Critical constraint: system prompt and tool schema must be pinned as byte-identical constants — any whitespace drift creates a full cache miss. Reports **4-6x throughput over baseline vLLM** on agentic tasks.

### Fine-Tuning Economics

| Method | Min Dataset | Hardware | Cost | Quality Recovery |
|---|---|---|---|---|
| LoRA (r=16, alpha=16) | 1,000-5,000 examples | 1x A100 | ~$30-100 | 90-95% of full FT |
| QLoRA | 1,000-5,000 examples | 1x RTX 4090 | ~$10-30 | 80-90% of full FT |
| Full fine-tuning | 5,000-10,000 examples | Multiple H100s | ~$1,000+ | 100% (baseline) |

### Bank-Grade SLA (99.9%) Serving Pattern

Kubernetes-managed SGLang pods behind application-layer load balancer, with weighted routing away from degraded instances. Separate inference pools: interactive chat (latency-sensitive, small batch) and background agents (throughput-optimised, large batch) to prevent head-of-line blocking. Blue-green deployments for model upgrades without downtime.

---

## 18. Innovation Differentiators

### Novelty Assessment

| Innovation | Status | Prior Art |
|---|---|---|
| Cross-entity financial digital twin | **No production precedent globally** | Huawei FinAgent Booster is infra-level, not consumer-facing |
| Predictive life event detection | **Research exists, zero productisation** | No bank has shipped this |
| Federated customer learning (privacy-preserving) | **Research exists (IEEE 2025), no banking deployment** | WeBank uses federated learning for credit scoring, not coaching |
| Per-customer learning loop with quality gating | **Novel combination** | FinMem (AAAI 2024) is closest — for trading, not retail coaching |
| Van Tharp process-outcome separation for AI advice | **Genuinely novel application** | Zero evidence of anyone applying this to AI financial advice |
| Proactive insight feed (not chatbot) | **Cleo 3.0 is close** | But lacks cross-entity, simulation, life event detection |
| On-premise Qwen for retail banking | **No documented competitor** | Most banks use OpenAI/Azure APIs |

### What Makes This Solution Different

#### 1. Cross-Entity Financial Digital Twin — First of Its Kind

**Simulate financial decisions across Bank, Finance, Securities, and Life Insurance simultaneously.**

No bank globally has shipped a consumer-facing cross-entity financial simulation. Shinhan's unique position — owning all four entities in Vietnam — makes this possible. A customer asking "what if I buy a house?" gets a unified answer spanning mortgage, loan restructuring, investment liquidation, and insurance adjustment. This is the single most differentiated capability in the entire solution.

#### 2. Predictive Life Event Detection — The Agent Knows Before You Ask

**Detect major life transitions from transaction patterns before the customer acts on them.**

Baby products appearing in transactions? Estate agent fees? Salary pattern break? The background agent detects these shifts and proactively generates relevant scenarios — insurance review for a new baby, mortgage simulation for a home purchase, emergency fund check for a career change. No bank has productised this.

#### 3. Proactive-First, Chat-Second — Not a Chatbot

**The agent works when the customer isn't looking.**

This is not a chat window waiting for questions. It is an autonomous background agent that continuously monitors transaction streams, fires deterministic trigger gates, generates ranked insight cards, and presents them as a curated feed. Chat is a drill-down mechanism, not the primary interface. This inverts the standard banking AI pattern.

#### 4. Federated Customer Learning — Network-Effect Intelligence

**The system gets smarter for all customers, not just each individual.**

Anonymised, quality-gated patterns from one customer's learning journal improve advice for similar customers. A new user inherits cohort insights from day one — no cold-start problem. The value of the system increases super-linearly with user count. Privacy is guaranteed via differential privacy and k-anonymity (minimum 50 customers per cohort).

#### 5. Self-Improving with Process-Outcome Separation

**The system doesn't reinforce lucky advice.**

Using the Van Tharp 2x2 matrix, the reflection step separates process quality from outcome quality. A savings suggestion that worked by coincidence is flagged as "bad process, good outcome" and not reinforced. Only insights from sound analytical processes are persisted and evolved. This is a genuinely novel application — zero prior art in AI financial advice.

#### 6. Deterministic Computation — LLM Reasons, Tools Calculate

**Every number the customer sees is computed by Python, not by the LLM.**

All mathematical operations are handled by deterministic MCP tools. The LLM's role is strictly to select which workflow or tool to invoke, and to interpret results in natural language. This is critical in a regulated banking context where a hallucinated percentage could trigger compliance violations.

#### 7. Workflow-as-Tool Orchestration — Predictable When Possible, Flexible When Needed

**Pre-built workflows for known intents, ReAct fallback for novel queries.**

Common financial tasks (spending analysis, goal tracking, product search, scenario simulation) are compiled LangGraph subgraphs invoked as single tool calls — deterministic, auditable, 3-5x fewer tokens. Novel queries fall back to ReAct over atomic tools. This gives the system the reliability of hard-coded flows with the flexibility of a reasoning agent.

#### 8. Fully On-Premise — No Data Leaves the Bank

**Qwen3 runs entirely on Shinhan's infrastructure.**

All customer data processing happens on-premise using open-source models. This isn't just a compliance advantage — it's a fundamental requirement under Vietnam's upcoming SBV AI Circular and Personal Data Protection Law. No external API dependency means no data sovereignty risk.

#### 9. Proven Patterns from Production Financial AI Systems

The architecture draws on two proven systems:
- **TojiMoola**: Persistent learning loop, lesson evolution, quality gates, importance feedback, Van Tharp reflection (financial domain, proven in backtesting)
- **Portfolio-Intelligence-Platform**: LangGraph workflows, MCP tool abstraction, cached API calls, structured chart output, multi-agent debate patterns (financial domain, deployed on Hugging Face Spaces)

### Banking AI Competitive Landscape (2025-2026)

For context on where this solution sits relative to global banking AI:

| Institution | AI Scope | Scale |
|---|---|---|
| JPMorgan | AI across 150,000 employees, targeting 1,000+ use cases | $20B tech spend reclassified as core infrastructure |
| Goldman Sachs | GS AI Assistant firmwide, Cognition AI agents for 12,000 developers | Full firm deployment |
| DBS (Singapore) | 1,500+ AI models, 370 use cases | S$750M quantified economic value in 2024 |
| OCBC | 300+ use cases, 6M AI-driven decisions daily | 2025 Asian Banker award for AI personalisation |
| VietinBank (Vietnam) | Internal LLM assistant "Genie" | 350,000 queries in 2 months |
| Techcombank (Vietnam) | ML-driven personalisation | 100M data points, 52M recommendations |
| VPBank (Vietnam) | ML credit scoring | Defaults reduced 30% |

**Our position:** Vietnamese banks are active in internal AI tools and credit scoring but none has shipped a consumer-facing autonomous financial coach. The cross-entity digital twin and proactive insight feed are architecturally novel globally.

**On-premise LLM momentum:** Enterprise AI inference on-premises jumped to 55% of workloads in 2025 (up from 12% in 2023). Banks drove a 40% increase in on-premise LLM hosting, citing data residency and regulatory compliance. On-premise costs run up to 18x lower per million tokens than cloud APIs.

---

## 19. References

### Research Sources — AI and Finance

- Qwen3 Technical Report — https://arxiv.org/abs/2505.09388
- Qwen2.5 Technical Report — https://arxiv.org/abs/2412.15115
- Empirical Study of Qwen3 Quantisation — https://arxiv.org/html/2505.02214v1
- FinStat2SQL (Text-to-SQL for Financial Analysis, ACL 2025) — https://aclanthology.org/2025.inlg-main.27.pdf
- FinMem: LLM Trading Agent with Layered Memory (AAAI 2024) — https://arxiv.org/abs/2311.13743
- Mem0: Scalable Long-Term Memory for AI Agents — https://arxiv.org/pdf/2504.19413
- Agentic AI Systems in Financial Services — https://arxiv.org/html/2502.05439v1
- AI-Powered Financial Digital Twins — https://jngr5.com/index.php/journal-of-next-generation-resea/article/view/119
- FABS: Digital Twin Framework for AI-Driven Financial Systems (ACM ICAIF) — https://dl.acm.org/doi/10.1145/3768292.3770369
- Federated Learning for Privacy-Preserving Mobile Banking — https://ieeexplore.ieee.org/document/11296263/
- SoK: Agentic Skills Beyond Tool Use — https://arxiv.org/html/2602.20867v1
- Fair Agent-to-Agent Negotiations — https://arxiv.org/html/2506.00073v1

### Architecture Patterns

- Building Effective AI Agents (Anthropic) — https://www.anthropic.com/research/building-effective-agents
- Agents-as-Tools Pattern (AWS) — https://dev.to/aws/build-multi-agent-systems-using-the-agents-as-tools-pattern-jce
- Agentic AI in Banking (Deloitte) — https://www.deloitte.com/us/en/insights/industry/financial-services/agentic-ai-banking.html
- Agentic AI in Financial Services: Multi-Agent Patterns (AWS) — https://aws.amazon.com/blogs/industries/agentic-ai-in-financial-services-choosing-the-right-pattern-for-multi-agent-systems/
- LangGraph Subgraphs as Tools — https://docs.langchain.com/oss/python/langgraph/use-subgraphs
- Deterministic MCP Tools for Hallucination Prevention — https://tinyfn.io/blog/prevent-llm-hallucinations-mcp

### Market Data

- Vietnam Digital Banking Adoption — https://marketresearchvietnam.com/insights/articles/vietnam-digital-banking-adoption-inclusion
- Vietnam Retail Banking 2024 (Cimigo) — https://www.cimigo.com/en/trends/vietnam-retail-banking-2024/
- S&P Global FinLit Survey
- OECD/INFE Financial Literacy Index
- Shinhan Financial in Vietnam (Korea Herald) — https://www.koreaherald.com/article/10625096
- Vietnam Open Banking Circular 64/2024 — https://wso2.com/library/blogs/innovation-inclusion-interoperability-vietnams-leap-into-open-banking/

### Competitor Analysis

- Cleo 3.0 — https://techintelpro.com/news/finance/financial-services/cleo-30-launches-as-ai-financial-coach-with-voice-and-memory
- KakaoBank AI Financial Calculator — https://www.microsoft.com/en/customers/story/24967-kakao-bank-azure-openai
- Huawei FinAgent Booster (cross-entity AI) — https://e.huawei.com/en/news/2025/industries/finance/financial-intelligence-accelerator-fab
- Monzo Data-Driven Insights — https://cloud.google.com/customers/monzo-bank

### Regulatory

- SBV AI Circular draft — https://www.mlex.com/mlex/financial-services/articles/2445671
- Vietnam Fintech Regulatory Sandbox (Decree 94/2025) — https://www.vietnam-briefing.com/news/vietnam-proposes-regulatory-sandbox-for-banking-sector-draft-decree-guidelines.html/
- Vietnam AI Regulatory Frameworks 2025 — https://www.vietnam-briefing.com/news/vietnams-ai-sector-in-2025-regulatory-frameworks-and-opportunities-for-investors.html/

### Shinhan Ecosystem

- SuperSOL Consolidation (Korea) — https://www.asiae.co.kr/en/visual-news/article/2025051915251747963
- Shinhan Financial Group Corporate Identity — https://shinhangroup.com/en/about/identity/ci
- Shinhan SOL Vietnam (App Store) — https://apps.apple.com/vn/app/shinhan-sol-vietnam/id1071033810

### Vietnamese NLP and Data

- PhoBERT (Pre-trained Vietnamese Language Models, EMNLP 2020) — https://aclanthology.org/2020.findings-emnlp.92/
- ViFinClass (Vietnamese Financial Text Classification) — https://ceur-ws.org/Vol-3026/paper25.pdf
- CFPB Vietnamese-English Financial Glossary — https://files.consumerfinance.gov/f/documents/cfpb_adult-fin-ed_vietnamese-style-guide-glossary.pdf
- Vietnamese Banking Dataset 2002-2021 (MDPI) — https://www.mdpi.com/2306-5729/7/9/120
- Life Event Detection from Transaction Data (Decision Support Systems, 2019) — ScienceDirect

### Digital Twin and Simulation

- FABS: Financial Agent-Based Simulator (ACM ICAIF 2025) — https://dl.acm.org/doi/10.1145/3768292.3770369
- AI-Powered Financial Digital Twins (JNGR 5.0, 2025) — https://jngr5.com/index.php/journal-of-next-generation-resea/article/view/119

### Additional Industry Sources

- Shinhan Bank Cloud Migration (Red Hat) — https://www.redhat.com/en/success-stories/shinhan-bank
- Vietnam Core Banking Systems — https://victorleungtw.com/2025/04/24/vietnam/
- Vietnam Open Banking Circular 64/2024 (WSO2) — https://wso2.com/library/blogs/innovation-inclusion-interoperability-vietnams-leap-into-open-banking/
- NAPAS Payment Gateway — https://en.napas.com.vn/napas-payment-gateway-service-184230614091707354.htm
- GreenNode / VNG Cloud GPU — https://greennode.ai
- FPT AI Factory — https://fpt.com
- Cleo Autopilot — https://web.meetcleo.com/blog/introducing-autopilot
- RBC NOMI Insights — https://digitaldefynd.com/IQ/ai-in-banking-case-studies/
- Gartner Ambient Invisible Intelligence 2025 — https://www.gartner.com/en/newsroom/press-releases/2024-10-21-gartner-identifies-the-top-10-strategic-technology-trends-for-2025
- Benchmarking Multi-Agent Financial Document Processing (arXiv 2603.22651) — https://arxiv.org/html/2603.22651
- BFCL Leaderboard — https://gorilla.cs.berkeley.edu/leaderboard.html

### Open-Source References

- FinRobot (Multi-Agent Financial Analysis) — https://github.com/AI4Finance-Foundation/FinRobot
- FinGPT (Financial LLM Fine-Tuning) — https://github.com/AI4Finance-Foundation/FinGPT
- Qwen-Agent — https://github.com/QwenLM/Qwen-Agent
- MCC Codes Dataset — https://github.com/greggles/mcc-codes
- Synthetic Data Vault — https://github.com/sdv-dev/SDV
- PhoBERT — https://github.com/VinAIResearch/PhoBERT
- WeBank FATE (Federated Learning) — https://github.com/FederatedAI/FATE

### Internal References

- TojiMoola (self-improving earnings analyst) — `/home/brian-isaac/Documents/personal/tojimoola/`
- Portfolio-Intelligence-Platform — `/home/brian-isaac/Documents/personal/Portfolio-Intelligence-Platform/`

---

