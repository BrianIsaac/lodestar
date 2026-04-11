# Lodestar — AI Personal Financial Coach

**Lodestar** is an autonomous AI financial coach PoC for **Shinhan Bank Vietnam's SOL app**, built for Innoboost 2026.

The name reflects the product's role: a guiding star for customers navigating their financial lives — surfacing the right signals at the right time without ever telling them what to do.

Runs fully on-premise using **Qwen3** via Ollama, with a proactive insight feed, cross-entity financial simulation across all four Shinhan entities (Bank, Finance, Securities, Life), a per-customer learning loop, and a Vietnamese-language first experience.

## What It Is

Not a chatbot. An **autonomous agent** that continuously monitors customer transactions, detects patterns and life events, surfaces ranked insight cards, and enables drill-down conversations with inline charts.

Key innovations:

- **Cross-entity financial digital twin** — simulate "what if I buy a house?" across mortgage (Bank), existing loans (Finance), investments (Securities), and insurance (Life)
- **Predictive life event detection** from transaction patterns (baby, home purchase, career change)
- **Per-customer learning loop** with quality gating, semantic deduplication, and importance feedback
- **Federated cohort intelligence** — anonymised patterns benefit similar customers (k-anonymity, differential privacy)
- **Van Tharp process/outcome separation** — the system doesn't reinforce lucky advice
- **Deterministic MCP tools** — all financial calculations done in Python, LLM only reasons and communicates
- **Workflow-as-tool orchestration** — pre-built LangGraph workflows invoked by Qwen-Agent with ReAct fallback

## Stack

**Backend:** Python 3.11+, FastAPI, LangGraph, Qwen-Agent, Qdrant, SQLite, bge-m3 via sentence-transformers, underthesea (Vietnamese NLP), SDV + Faker (synthetic data)

**LLM:** Qwen3:14b via Ollama at `localhost:11434` (production target: Qwen3-8B Q4_K_M via llama.cpp on 12GB GPU)

**Frontend:** Next.js 15 + shadcn/ui + Recharts, deployed on Vercel. Shinhan Blue (#0046FF) OKLCH theming.

## Quick Start

```bash
# 1. Install deps
uv sync
uv sync --extra dev

# 2. Seed synthetic data (5 Vietnamese customers, 12 months of transactions)
uv run python -m lodestar.data.seed_data

# 3. Run tests
uv run pytest

# 4. Start backend (requires Ollama with qwen3:14b pulled)
CUDA_VISIBLE_DEVICES="" uv run uvicorn lodestar.api:app --port 8000

# 5. Start frontend
cd frontend
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

Open <http://localhost:3000>.

## Project Structure

```
lodestar/
├── docs/                          # 17 research documents
├── plans/                         # Implementation plan
├── src/lodestar/
│   ├── api.py                     # FastAPI endpoints
│   ├── config.py                  # Pydantic settings
│   ├── database.py                # SQLite schema
│   ├── models/                    # Pydantic data models
│   ├── data/                      # Synthetic data generators
│   ├── tools/                     # Deterministic MCP tools (spending, goals, charts, simulation)
│   ├── rag/                       # Qdrant + bge-m3 RAG pipeline
│   ├── agents/
│   │   ├── orchestrator.py        # Qwen-Agent reactive orchestrator
│   │   ├── background.py          # Polling trigger loop
│   │   ├── triggers.py            # Deterministic trigger rules
│   │   ├── compliance.py          # Compliance filter
│   │   └── workflows/             # LangGraph subgraphs (spending, goals, products, scenario)
│   ├── learning/                  # Per-customer journal + cohort store
│   └── nlp/                       # Vietnamese NLP helpers
├── frontend/                      # Next.js + shadcn/ui + Recharts
├── tests/                         # 80+ tests across all modules
├── SB1_AI_Personal_Financial_Coach.md   # Master design doc
├── pyproject.toml
└── LICENSE                        # Apache 2.0
```

## Documentation

- [Master Design Document](SB1_AI_Personal_Financial_Coach.md) — full architecture, research, and novelty assessment
- [Research Docs](docs/README.md) — 17 augmented research documents
- [Implementation Plan](plans/2026-04-03-sb1-financial-coach-poc.md) — 8-phase build plan with verification checkpoints

## License

Apache License 2.0 — see [LICENSE](LICENSE).
