# Data Sources and Integration

> Part of [SB1: AI Personal Financial Coach for Shinhan SOL Vietnam](../SB1_AI_Personal_Financial_Coach.md)

---

## 12. Data Sources and Integration

### Available Data (from Shinhan's use case brief and cross-entity analysis)

The target teams listed in the brief, plus the cross-entity opportunity, imply access to the following data:

| Data Source | Owner Team | Data Available | Use In Coach |
|---|---|---|---|
| **Transaction History** | Retail Customer Dept. | 12-24 months of transactions, merchant descriptions, amounts, dates | Spending categorisation, pattern detection, income identification |
| **Account Balances** | Retail Customer Dept. | All product balances (savings, current, fixed deposit) | Net worth view, liquidity alerts, CASA growth tracking |
| **Loan & Credit Data** | Retail Lending Dept. | Outstanding loans, repayment schedules, credit limits | Debt-to-income calculation, repayment planning |
| **Card Data** | Card Division | Card transactions, rewards points, billing cycles | Card-specific spending analysis, rewards optimisation |
| **Product Catalogue** | Wealth Management Dept. | All retail products (loans, savings, insurance, cards) with rates and terms | RAG knowledge base for product information |
| **Customer Profile** | Digital Business Unit | Demographics, segment, KYC data, app usage patterns | Personalisation baseline, eligibility filtering |
| **SOL App Behaviour** | Digital Business Unit | Session data, feature usage, notification engagement | Nudge timing optimisation, engagement scoring |

### Cross-Entity Data (for Digital Twin)

| Entity | Data Available | Use In Digital Twin |
|---|---|---|
| **Shinhan Finance** | Consumer loans, credit card balances, repayment schedules | Combined DTI calculation, loan restructuring simulation |
| **Shinhan Securities** | Portfolio holdings, unrealised gains, trade history | Investment liquidation planning, tax-efficient sell orders |
| **Shinhan Life** | Active policies, coverage amounts, premium schedules | Coverage gap analysis, premium impact in scenarios |

**Regulatory enabler:** Vietnam's Open Banking Circular 64/2024 (effective March 2025) mandates consent-driven API data sharing. Banks must implement customer-information APIs by September 2026. This creates the legal framework for cross-entity data flow within the Shinhan group.

**For PoC:** All cross-entity data is synthetic. For production, the Banking Router abstracts real APIs from each entity behind a unified interface.

### Integration Architecture

**Pattern adapted from:** Portfolio-Intelligence-Platform's `MCPRouter` — a compatibility shim that abstracts multiple backend APIs behind a unified tool interface.

```python
import httpx
from functools import lru_cache
from pydantic import BaseModel

class BankingRouter:
    """Unified interface to Shinhan's core banking systems.

    Abstracts Bank, Finance, Securities, and Life APIs behind
    a single call interface. For PoC, backends are synthetic
    data generators. For production, they connect to real APIs.
    """

    def __init__(self, config: dict[str, str]) -> None:
        self._clients: dict[str, httpx.AsyncClient] = {}
        for entity, base_url in config.items():
            self._clients[entity] = httpx.AsyncClient(
                base_url=base_url,
                timeout=30.0,
            )

    async def call(
        self, entity: str, method: str, params: dict
    ) -> dict:
        """Route a call to the appropriate entity API.

        Args:
            entity: One of 'bank', 'finance', 'securities', 'life'.
            method: API method name (e.g. 'get_transactions').
            params: Method parameters.

        Returns:
            API response as dict.
        """
        client = self._clients[entity]
        response = await client.post(
            f"/api/{method}",
            json=params,
        )
        response.raise_for_status()
        return response.json()

    # Convenience methods
    async def call_transaction_api(self, method: str, params: dict) -> dict:
        return await self.call("bank", method, params)

    async def call_product_api(self, method: str, params: dict) -> dict:
        return await self.call("bank", method, params)

    async def call_finance_api(self, method: str, params: dict) -> dict:
        return await self.call("finance", method, params)

    async def call_securities_api(self, method: str, params: dict) -> dict:
        return await self.call("securities", method, params)

    async def call_life_api(self, method: str, params: dict) -> dict:
        return await self.call("life", method, params)
```

For the PoC, these are backed by **synthetic data generators** (SDV or LLM-seeded). For production, they connect to Shinhan's actual core banking APIs.

**Core Banking Systems in Vietnam:** Temenos (T24/Transact) dominates with ~37.5% market share (~12 banks including Military Commercial, Orient Commercial, VPBank). Oracle FLEXCUBE holds ~25%. Shinhan's specific CBS vendor is undisclosed — the global group historically uses its in-house Korean "Nextgen" system.

**NAPAS (Vietnam's payment switch):** Processes 9.56 billion transactions annually (2024, +30% YoY). APIs cover payment initiation, transaction inquiry, void/reversal, and QR lookup. Settlement is sub-10 seconds. Raw merchant metadata resides within individual bank ledgers, not at the NAPAS switch level.

**Data quality caveat:** Transaction description fields are not standardised across Vietnamese banks. Legacy encoding systems (TCVN/VSCII, Windows-1258) coexist with UTF-8, creating mixed-encoding datasets. Free-text transfer descriptions are user-generated and highly inconsistent.

### Caching Strategy

**Pattern adapted from:** Portfolio-Intelligence-Platform's `@cached_async` decorator with per-type TTLs.

| Data Type | TTL | Rationale |
|---|---|---|
| Account balances | 60 seconds | Near real-time for balance queries |
| Transaction history | 4 hours | Doesn't change frequently intra-day |
| Product catalogue | 24 hours | Rates change daily at most |
| Customer profile | 7 days | Rarely changes |
| Spending aggregations | 1 hour | Precomputed summaries |

---
