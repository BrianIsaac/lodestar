# Visualisation Strategy

> Part of [SB1: AI Personal Financial Coach for Shinhan SOL Vietnam](../SB1_AI_Personal_Financial_Coach.md)

---

## 13. Visualisation Strategy

### Inline Chat Charts

Charts are rendered **inline in the chat response** — not in a separate analytics tab. This is the interaction model proven by Cleo 3.0 and KakaoBank.

The agent returns structured JSON; the SOL frontend renders natively.

### Chart Specification Format

```json
{
  "chart_type": "donut",
  "title": "Chi tieu thang 3/2026",
  "data": {
    "labels": ["An uong", "Di lai", "Mua sam", "Hoa don", "Khac"],
    "values": [4200000, 1800000, 3100000, 2500000, 900000],
    "currency": "VND"
  },
  "summary": "Ban da chi 12.5 trieu dong trong thang 3. An uong chiem 33.6% — tang 12% so voi thang truoc."
}
```

### Chart Types

| Chart | Use Case | When Triggered |
|---|---|---|
| **Donut/Pie** | Spending category breakdown | "How did I spend this month?" |
| **Stacked Bar** | Budget vs actual by category per month | "Am I on budget?" |
| **Line** | Balance/savings trajectory over time | "How are my savings going?" |
| **Progress Bar** | Goal completion percentage | Goal status queries |
| **Waterfall** | Income minus expense categories = net flow | "Where does my money go?" |
| **Grouped Bar** | Month-over-month comparison | "How does this month compare to last?" |

### Implementation

**Pattern adapted from:** Portfolio-Intelligence-Platform's Plotly chart generators — but outputting JSON specs instead of Plotly figures, since the mobile frontend renders natively.

For the PoC web demo, charts render via Plotly.js in the browser. For SOL integration, the same JSON spec is consumed by the native charting library (Victory Native for React Native, fl_chart for Flutter, or equivalent).

### Chart Library Recommendations

| Library | Best For | Vietnamese Locale |
|---|---|---|
| **ECharts** | Performance, mobile rendering, real-time data | Supports `registerLocale` but `vi` requires custom locale object |
| **Plotly** | Analytical interactivity (zoom, pan, tooltips) | d3-format has known non-English locale issues |
| **Chart.js** | Lightest option, simple dashboards | No locale concerns for basic charts |
| **Victory Native** | React Native, native SVG rendering | N/A (data-only) |
| **fl_chart** | Flutter, native rendering | N/A (data-only) |

For VND formatting, use `Intl.NumberFormat('vi-VN', { currency: 'VND' })` browser API regardless of charting library.

**Structured spec format:** Vega-Lite is the closest to an open standard — a declarative JSON schema describing mark type, data, and encoding. Most widely adopted for LLM-to-chart pipelines because its schema is compact enough for generation. Our chart spec format is inspired by Vega-Lite but simplified for mobile rendering.

### Colour and Accessibility

- WCAG 2.1 AA: 3:1 contrast between adjacent chart elements, 4.5:1 for text
- Blue is the safest anchor colour (rarely affected by colour vision deficiency)
- Shinhan blue (`#0046FF`) is safe as dominant brand colour
- Pair with orange/amber for positive contrast, desaturated red for negative — dual-encode with icons/patterns, not colour alone
- IBM accessibility palette: blue `#648FFF`, orange `#FE6100`, magenta `#DC267F`

---
