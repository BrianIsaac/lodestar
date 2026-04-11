# Persistent Learning Loop and Federated Customer Learning

> Part of [SB1: AI Personal Financial Coach for Shinhan SOL Vietnam](../SB1_AI_Personal_Financial_Coach.md)

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
