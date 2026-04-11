# System Architecture

> Part of [SB1: AI Personal Financial Coach for Shinhan SOL Vietnam](../SB1_AI_Personal_Financial_Coach.md)

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
