# Predictive Life Event Detection

> Part of [SB1: AI Personal Financial Coach for Shinhan SOL Vietnam](../SB1_AI_Personal_Financial_Coach.md)

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
