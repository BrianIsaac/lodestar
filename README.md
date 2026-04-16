# Lodestar — AI Personal Financial Coach

**Lodestar** is an autonomous AI financial coach PoC for **Shinhan Bank Vietnam's SOL app**, built for Innoboost 2026.

The name reflects the product's role: a guiding star for customers navigating their financial lives — surfacing the right signals at the right time without ever telling them what to do.

Runs on **Qwen** (Alibaba DashScope in production, local Ollama for development), with a proactive insight feed, cross-entity financial simulation across all four Shinhan entities (Bank, Finance, Securities, Life), a per-customer learning loop, and a Vietnamese-language first experience.

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

**Backend:** Python 3.11+, FastAPI, LangGraph, Qwen-Agent, Qdrant, SQLite, bge-m3 via sentence-transformers, underthesea (Vietnamese NLP), SDV + Faker (synthetic data).

**LLM:** Qwen via Alibaba DashScope (`qwen-plus`) in production, or local Ollama (`qwen3:14b`) for development. Both speak the OpenAI-compatible API so swapping providers is a one-line env change.

**Frontend:** Next.js 15 + shadcn/ui + Recharts. Shinhan Blue (#0046FF) OKLCH theming.

**Deployment:** Alibaba Cloud ECS (Ubuntu 22.04) via Docker Compose — see [DEPLOY.md](DEPLOY.md).

## Quick Start

```bash
# 1. Install deps
uv sync
uv sync --extra dev

# 2. Seed synthetic data (5 Vietnamese customers, 12 months of transactions)
uv run python -m lodestar.data.seed_data

# 3. Run tests
uv run pytest

# 4. Start backend
# Needs an LLM — either local Ollama (qwen3:14b) or a DashScope key in .env.
# See .env.example for both configurations.
CUDA_VISIBLE_DEVICES="" uv run uvicorn lodestar.api:app --port 8000

# 5. Start frontend
cd frontend
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

Open <http://localhost:3000>.

## Project Structure

```
lodestar/
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
├── Dockerfile                     # Multi-stage backend + frontend image
├── docker-compose.yml             # ECS deployment orchestration
├── .env.example                   # LLM / API config template
├── pyproject.toml
├── DEPLOY.md                      # Alibaba Cloud ECS deployment guide
└── LICENSE                        # Apache 2.0
```

## Deployment

Live demo on Alibaba Cloud ECS:

- Frontend: <http://43.98.179.20:3000>
- Backend API: <http://43.98.179.20:8000>

See [DEPLOY.md](DEPLOY.md) for the full setup, DashScope configuration, and update workflow.

## License

Apache License 2.0 — see [LICENSE](LICENSE).
