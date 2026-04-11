# Technology Stack

> Part of [SB1: AI Personal Financial Coach for Shinhan SOL Vietnam](../SB1_AI_Personal_Financial_Coach.md)

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
