# Regulatory Compliance

> Part of [SB1: AI Personal Financial Coach for Shinhan SOL Vietnam](../SB1_AI_Personal_Financial_Coach.md)

---

## 15. Regulatory Compliance

### Vietnam Regulatory Landscape

| Regulation | Status | Impact |
|---|---|---|
| **SBV AI Circular** | Draft, expected effective March 2026, grace period to September 2027 | Mandates safety requirements, risk management, customer rights for AI in banking |
| **Decree 94/2025/ND-CP** | Effective July 2025 | Fintech regulatory sandbox — **robo-advisory explicitly excluded** |
| **Circular 121/2022/TT-BTC** | Active | Investment advice must be based on reasonable, reliable analysis |
| **Decree 13/2023/ND-CP (Personal Data Protection)** | Effective 1 July 2023 | Consent-based data processing; sensitive data (financial records) triggers enhanced obligations |
| **Law on Digital Technology Industry** | Effective 1 January 2026 | Finance designated high-risk; mandatory AI registration, human oversight, operational logging |

### Compliance Architecture

1. **Scope v1 to non-advisory features only:**
   - Spending insights and categorisation (information)
   - Savings goals and nudges (guidance)
   - Product information lookup (information)
   - Budget tracking with visualisation (information)
   - **No investment recommendations** until regulatory clarity

2. **Compliance Filter Agent** as a first-class component (not an afterthought):
   - Classifies every output as `information`, `guidance`, or `advice`
   - Blocks `advice` category responses
   - Adds disclaimers to `guidance` responses
   - Logs all interactions for audit trail

3. **Data handling:**
   - All customer data processed on-premise or in Shinhan's private cloud
   - No data sent to external LLM APIs (Qwen runs locally)
   - Consent-based data access aligned with upcoming Personal Data Protection Law

4. **Audit trail:**
   - Every agent interaction logged with: timestamp, customer_id, intent, response, compliance_classification
   - Learning journal entries are traceable and auditable

### Detailed Regulatory Analysis

**Decree No. 94/2025/ND-CP (Fintech Sandbox):** Effective 1 July 2025. Participants must submit risk management protocols, operate IT systems within Vietnam, file quarterly progress reports to the SBV, and may pilot for up to two years (extendable to three).

**Law on Digital Technology Industry (June 2025, effective 1 January 2026):** Designates finance as a high-risk sector requiring pre-market government assessment, mandatory registration in a National AI Database, human oversight, operational logging, and incident suspension powers.

**Decree 13/2023 (Personal Data Protection):** Consent must be explicit, voluntary, and informed — pre-ticked boxes and silence are invalid. Sensitive data (biometrics, financial records) triggers enhanced obligations. Cross-border transfers require impact assessment filed with Ministry of Public Security within 60 days. Unlike GDPR, no "legitimate interests" basis — consent is the near-universal requirement.

**Circular 09/2020/TT-NHNN (Data Localisation):** Banks maintaining systems outside Vietnam must store Vietnamese customer personal and transaction data within Vietnam. Level 3+ systems require backup and disaster recovery on Vietnamese infrastructure. This reinforces the on-premise Qwen deployment strategy.

**ASEAN benchmarks:** MAS (Singapore) applies Financial Advisers Act to digital advisers with AI Risk Management Guidelines (2025) mandating board oversight, lifecycle controls, and explainability. Thailand SEC encourages robo-advisory under a five-step client-servicing framework. Vietnam is most likely to follow the MAS model.

---
