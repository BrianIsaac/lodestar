"""LangGraph product match workflow — compiled as a callable subgraph."""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from lodestar.models import ProductInfo


class ProductMatchState(TypedDict):
    """State for the product match workflow."""

    query: str
    customer_id: str | None
    results: list[ProductInfo]
    eligibility_checked: list[dict]
    insight_text: dict[str, str]


async def search(state: ProductMatchState) -> dict:
    """Search products via hybrid RAG."""
    from lodestar.rag.retriever import search_products

    results = search_products(state["query"], limit=5)
    return {"results": results}


async def check_eligibility(state: ProductMatchState) -> dict:
    """Check eligibility for each result if customer_id is provided."""
    customer_id = state.get("customer_id")
    results = state.get("results", [])

    if not customer_id or not results:
        return {"eligibility_checked": []}

    from lodestar.tools.products import check_eligibility as _check

    checked = []
    for product in results:
        result = await _check(customer_id, product.product_id)
        checked.append({
            "product_id": product.product_id,
            "name_vi": product.name_vi,
            "eligible": result.eligible,
            "reasons": result.reasons,
        })

    return {"eligibility_checked": checked}


_PRODUCT_COPY: dict[str, dict[str, str]] = {
    "none": {
        "vi": "Không tìm thấy sản phẩm phù hợp.",
        "en": "No matching products found.",
        "ko": "적합한 상품을 찾지 못했습니다.",
    },
    "found": {
        "vi": "Tìm thấy {n} sản phẩm phù hợp:",
        "en": "Found {n} matching products:",
        "ko": "{n}개의 적합한 상품을 찾았습니다:",
    },
    "rate": {
        "vi": "lãi suất {r}%",
        "en": "{r}% rate",
        "ko": "금리 {r}%",
    },
    "eligible": {
        "vi": "✓ đủ điều kiện",
        "en": "✓ eligible",
        "ko": "✓ 자격 충족",
    },
    "disclaimer": {
        "vi": "Đây là thông tin sản phẩm, không phải tư vấn tài chính.",
        "en": "This is product information, not financial advice.",
        "ko": "상품 정보이며 금융 자문이 아닙니다.",
    },
}


def _pick_name(product: ProductInfo, lang: str) -> str:
    if lang == "ko":
        return getattr(product, "name_ko", "") or product.name_vi
    if lang == "en":
        return product.name_en or product.name_vi
    return product.name_vi


def compose_response(state: ProductMatchState) -> dict:
    """Compose product information response in every supported language."""
    results = state.get("results", [])
    eligibility = state.get("eligibility_checked", [])

    if not results:
        return {"insight_text": dict(_PRODUCT_COPY["none"])}

    elig_map = {e["product_id"]: e for e in eligibility}
    out: dict[str, str] = {}
    for lang in ("vi", "en", "ko"):
        lines = [_PRODUCT_COPY["found"][lang].format(n=len(results))]
        for i, p in enumerate(results, 1):
            rate_str = (
                _PRODUCT_COPY["rate"][lang].format(r=p.interest_rate)
                if p.interest_rate is not None
                else ""
            )
            line = f"  {i}. {_pick_name(p, lang)} ({p.entity}) {rate_str}".rstrip()
            elig = elig_map.get(p.product_id)
            if elig:
                if elig["eligible"]:
                    line += f" {_PRODUCT_COPY['eligible'][lang]}"
                else:
                    line += f" ✗ {', '.join(elig['reasons'])}"
            lines.append(line)
        lines.append("")
        lines.append(_PRODUCT_COPY["disclaimer"][lang])
        out[lang] = "\n".join(lines)

    return {"insight_text": out}


def build_product_match_graph() -> StateGraph:
    """Build and return the product match workflow graph.

    Returns:
        Compiled LangGraph StateGraph.
    """
    builder = StateGraph(ProductMatchState)

    builder.add_node("search", search)
    builder.add_node("check_eligibility", check_eligibility)
    builder.add_node("compose_response", compose_response)

    builder.add_edge(START, "search")
    builder.add_edge("search", "check_eligibility")
    builder.add_edge("check_eligibility", "compose_response")
    builder.add_edge("compose_response", END)

    return builder.compile()


product_match_graph = build_product_match_graph()
