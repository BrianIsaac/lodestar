# Cross-Entity Financial Digital Twin

> Part of [SB1: AI Personal Financial Coach for Shinhan SOL Vietnam](../SB1_AI_Personal_Financial_Coach.md)

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
