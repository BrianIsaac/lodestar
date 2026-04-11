# Agent Design

> Part of [SB1: AI Personal Financial Coach for Shinhan SOL Vietnam](../SB1_AI_Personal_Financial_Coach.md)

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
