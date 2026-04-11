# PoC Scope

> Part of [SB1: AI Personal Financial Coach for Shinhan SOL Vietnam](../SB1_AI_Personal_Financial_Coach.md)

---

## 16. PoC Scope

### What We Build (Minimum Viable Demo)

| Feature | Description | Component |
|---|---|---|
| **Proactive insight feed** | Ranked cards generated autonomously from transaction stream | Background Agent + Trigger Rules |
| **Drill-down scoped chat** | Tap any card → contextual conversation with charts | Reactive Orchestrator |
| **Spending analysis workflow** | Auto-categorise, summarise, chart — invoked as a tool | LangGraph Workflow |
| **Savings goal tracking** | Create goals, track progress, project completion | LangGraph Workflow |
| **Product information RAG** | "What credit cards are available?" via Qdrant | Product Match Workflow |
| **Cross-entity scenario simulation** | "What if I buy a house?" across Bank + Finance + Securities + Life | Digital Twin + Simulation Workflow |
| **Life event detection** | Pattern-based detection from transaction shifts | Trigger Rules + LLM Confirmation |
| **Per-customer learning loop** | Quality-gated lessons, semantic retrieval, importance feedback | Learning Journal |
| **Federated cohort insights** | Anonymised patterns benefit similar customers | Cohort Store |
| **Compliance filtering** | All outputs classified and gated before delivery | Compliance Filter |
| **Multilingual** | Vietnamese + English (Korean as stretch) | Qwen3 multilingual |
| **Shinhan-branded UI** | Matching #0046FF palette, card-based, mobile-responsive | Next.js + shadcn/ui on Vercel |

### What We Don't Build (PoC)

- Real core banking API integration (synthetic data across all 4 entities)
- Native mobile UI (web demo styled to match SOL instead)
- Voice interaction
- Investment recommendations (regulatory constraint)
- Real-time streaming infra (polling loop simulates streaming for demo)

### PoC Best Practices from Research

**Timeline:** Banking AI PoCs typically run 8-16 weeks. A focused 4-8 week sprint is achievable with narrow scope: one user persona, 3-5 insight types, single data source, and 10-20 internal testers. The FCA's AI Live Testing initiative confirms regulators expect incremental iteration, not full-scale deployment.

**Demo framework:** **Next.js + shadcn/ui deployed on Vercel** — built using Vercel skills (deploy-to-vercel, vercel-react-best-practices, shadcn, web-design-guidelines). Produces pixel-perfect branded UI that matches production app quality. Vercel gives shareable preview URLs with no setup for stakeholders. shadcn's built-in Chart component (Recharts) handles all financial visualisations. Banking decision-makers evaluate polish as a proxy for production readiness — a proper React app dramatically outperforms Streamlit/Gradio in boardroom settings.

**Synthetic data:** No off-the-shelf tool generates Vietnamese-style transaction descriptions (NAPAS transfers, VietQR merchant names). Practical approach: hand-craft a Vietnamese merchant taxonomy and wrap Faker (`vi_VN` locale) around it. Data only needs to be realistic enough to surface believable insight triggers.

**Key PoC metrics:**
- **Insight acceptance rate**: how often users act on a coach suggestion (core PoC signal)
- **Session depth**: how deep users drill into insights
- **Cross-sell lift**: AI targeting achieves up to 2x conversion vs baseline in production systems
- **Engagement**: AI coaching platforms report up to 73% engagement on proactive nudges

**Common failure mode:** 72% of AI failures stem from data infrastructure issues, not algorithms. Over-scoping is the dominant PoC killer — one hypothesis per sprint.

### Synthetic Data Requirements

| Dataset | Contents | Volume |
|---|---|---|
| **Bank transactions** | 12 months of realistic Vietnamese transactions (merchants, amounts, dates) | 5-10 customer profiles, ~500 transactions each |
| **Finance data** | Consumer loans, credit card balances, repayment schedules | Per customer, 1-3 products |
| **Securities data** | Portfolio holdings, valuations, trade history | Per customer, 3-10 holdings |
| **Life insurance data** | Policies, coverage, premiums | Per customer, 1-2 policies |
| **Product catalogue** | Full Shinhan product catalogue across all 4 entities | ~50 products |
| **Customer profiles** | Demographics, income bands, segments, life stages | 5-10 profiles with embedded life event signals |
| **Life event profiles** | 2-3 customers with planted life event transaction patterns (baby, home purchase, career change) | Embedded in transaction data |

### Synthetic Data Generation Code

```python
from sdv.metadata import SingleTableMetadata  # Metadata class renamed in SDV >= 1.0
from sdv.single_table import GaussianCopulaSynthesizer  # Faster than CTGAN for PoC
from faker import Faker
import pandas as pd
import numpy as np

fake = Faker('vi_VN')

# Vietnamese merchant taxonomy
MERCHANTS = {
    'food': ['Grab Food', 'ShopeeFood', 'Pho 24', 'Bún Chả Hương Liên', 'Circle K'],
    'transport': ['Grab', 'Be', 'Xăng dầu Petrolimex', 'VietJet Air'],
    'shopping': ['Shopee', 'Lazada', 'Thế Giới Di Động', 'Uniqlo VN'],
    'bills': ['EVN Hà Nội', 'Viettel', 'VNPT', 'Nước sạch Hà Nội'],
    'health': ['Bệnh viện Bạch Mai', 'Nhà thuốc Long Châu', 'Medicare VN'],
}

def generate_napas_description(category: str, merchant: str) -> str:
    """Generate a realistic NAPAS-style transaction description.

    Args:
        category: Spending category key.
        merchant: Merchant name.

    Returns:
        NAPAS-format transaction description string.
    """
    ref = fake.bothify(text='TF##########')
    return f"CT DEN {merchant} {ref}"

def plant_life_event(df: pd.DataFrame, customer_id: str, event: str, month: str) -> pd.DataFrame:
    """Insert life event transaction patterns into synthetic data.

    Args:
        df: Transaction DataFrame.
        customer_id: Target customer.
        event: Event type ('baby', 'home_purchase', 'career_change').
        month: Target month (YYYY-MM).

    Returns:
        DataFrame with planted life event transactions.
    """
    patterns = {
        'baby': [('health', 'Bệnh viện Phụ sản', 5000000),
                 ('shopping', 'Kids Plaza', 2000000),
                 ('shopping', 'Con Cưng', 1500000)],
        'home_purchase': [('bills', 'Công ty BĐS Vinhomes', 50000000),
                          ('bills', 'Nội thất IKEA VN', 15000000)],
    }
    rows = []
    for cat, merchant, amount in patterns.get(event, []):
        rows.append({
            'customer_id': customer_id,
            'date': f"{month}-15",
            'amount': amount + np.random.randint(-500000, 500000),
            'category': cat,
            'merchant': merchant,
            'description': generate_napas_description(cat, merchant),
        })
    return pd.concat([df, pd.DataFrame(rows)], ignore_index=True)
```

---
