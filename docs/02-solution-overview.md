# Solution Overview

> Part of [SB1: AI Personal Financial Coach for Shinhan SOL Vietnam](../SB1_AI_Personal_Financial_Coach.md)

---

## 3. Solution Overview

An autonomous AI financial intelligence system embedded within Shinhan's SOL mobile app — **not a chatbot, but a proactive financial agent** that continuously monitors customer data, detects patterns and life events, simulates future scenarios across all Shinhan entities (Bank, Finance, Securities, Life), and surfaces actionable insights before the customer asks.

### Core Capabilities

1. **Monitors autonomously** — background agent streams customer transaction data, detecting spending anomalies, recurring charge changes, payday patterns, and life events in real-time
2. **Surfaces proactively** — ranked insight cards appear on a dedicated tab, each with a clear action; the customer reviews findings, not prompts an assistant
3. **Simulates across entities** — financial digital twin models the customer's full Shinhan relationship (bank accounts, loans, securities, insurance), enabling "what if" scenario simulation
4. **Learns per-customer** — quality-gated persistent learning loop improves advice over time; anonymised cohort insights improve advice for all customers via federated learning
5. **Drills down conversationally** — tapping any insight card opens a scoped chat thread with full context pre-loaded, charts inline, and follow-up actions available
6. **Multilingual** — Vietnamese, English, Korean (matching SOL's supported languages); Qwen3 covers 119 languages for future expansion

### What This Is NOT

This is not a chatbot waiting for questions. It is an **autonomous financial agent** that:
- Works when the customer is not looking
- Detects what matters before the customer knows to ask
- Presents findings as a curated feed, not a conversation
- Offers conversational drill-down only when the customer wants depth
- Simulates financial futures, not just reports the past

### Why Proactive Beats Reactive

Gartner named **Ambient Invisible Intelligence** a top-10 strategic technology trend for 2025 — AI that senses and acts in the background without explicit user interaction. The evidence from deployed financial products confirms this direction:

- **RBC NOMI**: Proactive nudging autonomously set aside ~$6.5 billion in customer savings — no user prompt required
- **JPMorgan**: AI nudge system produced 10-20% lift in product application completion rates
- **Cleo Autopilot** (July 2025): Three-layer architecture — Roadmap (goal plan), Daily Plan (personalised guidance), Actions (autonomous execution with pre-approved guardrails). A Smart Insights Agent powered by OpenAI o3 reviews six months of history and surfaces findings unprompted

The key insight: proactive financial AI drives measurably higher engagement and conversion than reactive chatbots. However, notification fatigue is a real constraint — 64% of users delete an app after 5+ irrelevant notifications per week (MagicBell). The lever is **relevance, not volume**: banks applying real-time personalisation see 30% higher digital engagement and 20% fewer opt-outs.

Our system manages this through per-customer learning — the more the system knows about what a customer engages with, the more precisely it can rank and surface only the insights that matter.

---
