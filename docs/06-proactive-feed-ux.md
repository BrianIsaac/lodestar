# Proactive Insight Feed UX

> Part of [SB1: AI Personal Financial Coach for Shinhan SOL Vietnam](../SB1_AI_Personal_Financial_Coach.md)

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
