"""LangGraph product match workflow — compiled as a callable subgraph."""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from qwen_viet.models import ProductInfo


class ProductMatchState(TypedDict):
    """State for the product match workflow."""

    query: str
    customer_id: str | None
    results: list[ProductInfo]
    eligibility_checked: list[dict]
    insight_text: str


async def search(state: ProductMatchState) -> dict:
    """Search products via hybrid RAG."""
    from qwen_viet.rag.retriever import search_products

    results = search_products(state["query"], limit=5)
    return {"results": results}


async def check_eligibility(state: ProductMatchState) -> dict:
    """Check eligibility for each result if customer_id is provided."""
    customer_id = state.get("customer_id")
    results = state.get("results", [])

    if not customer_id or not results:
        return {"eligibility_checked": []}

    from qwen_viet.tools.products import check_eligibility as _check

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


def compose_response(state: ProductMatchState) -> dict:
    """Compose product information response."""
    results = state.get("results", [])
    eligibility = state.get("eligibility_checked", [])

    if not results:
        return {"insight_text": "Không tìm thấy sản phẩm phù hợp."}

    elig_map = {e["product_id"]: e for e in eligibility}
    lines = [f"Tìm thấy {len(results)} sản phẩm phù hợp:"]

    for i, p in enumerate(results, 1):
        rate_str = f"lãi suất {p.interest_rate}%" if p.interest_rate is not None else ""
        line = f"  {i}. {p.name_vi} ({p.entity}) {rate_str}"

        elig = elig_map.get(p.product_id)
        if elig:
            if elig["eligible"]:
                line += " ✓ đủ điều kiện"
            else:
                line += f" ✗ {', '.join(elig['reasons'])}"

        lines.append(line)

    lines.append("")
    lines.append("Đây là thông tin sản phẩm, không phải tư vấn tài chính.")

    return {"insight_text": "\n".join(lines)}


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
