# Orchestrator: Workflow-as-Tool Pattern

> Part of [SB1: AI Personal Financial Coach for Shinhan SOL Vietnam](../SB1_AI_Personal_Financial_Coach.md)

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
