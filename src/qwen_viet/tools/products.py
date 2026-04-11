"""Product search, comparison, and eligibility tools."""

from qwen_viet.database import get_db
from qwen_viet.models import ComparisonTable, EligibilityResult, ProductFilters, ProductInfo
from qwen_viet.rag import retriever


async def search_products(
    query: str, filters: ProductFilters | None = None
) -> list[ProductInfo]:
    """Search Shinhan products using hybrid RAG.

    Args:
        query: Natural language query (Vietnamese or English).
        filters: Optional payload filters.

    Returns:
        Ranked list of matching products.
    """
    return retriever.search_products(query, filters)


async def compare_products(product_ids: list[str]) -> ComparisonTable:
    """Side-by-side comparison of selected products.

    Args:
        product_ids: List of product IDs to compare.

    Returns:
        ComparisonTable with aligned rows.
    """
    products = []
    for pid in product_ids:
        results = retriever.search_products(pid, limit=1)
        if results:
            products.append(results[0])

    columns = ["name_vi", "product_type", "entity", "interest_rate", "min_income"]
    rows = []
    for p in products:
        rows.append({
            "product_id": p.product_id,
            "name_vi": p.name_vi,
            "product_type": p.product_type,
            "entity": p.entity,
            "interest_rate": p.interest_rate,
            "min_income": p.min_income,
        })

    return ComparisonTable(product_ids=product_ids, columns=columns, rows=rows)


async def check_eligibility(
    customer_id: str, product_id: str
) -> EligibilityResult:
    """Check if a customer meets a product's eligibility criteria.

    Args:
        customer_id: Customer identifier.
        product_id: Product identifier.

    Returns:
        EligibilityResult with pass/fail and reasons.
    """
    from qwen_viet.rag.indexer import COLLECTION_NAME, get_qdrant_client
    from qdrant_client import models as qmodels

    client = get_qdrant_client()
    scroll_result = client.scroll(
        collection_name=COLLECTION_NAME,
        scroll_filter=qmodels.Filter(must=[
            qmodels.FieldCondition(key="product_id", match=qmodels.MatchValue(value=product_id)),
        ]),
        limit=1,
        with_payload=True,
    )
    points = scroll_result[0]
    if not points:
        return EligibilityResult(
            product_id=product_id,
            customer_id=customer_id,
            eligible=False,
            reasons=["Product not found"],
        )

    p = points[0].payload
    product = ProductInfo(
        product_id=p["product_id"],
        entity=p["entity"],
        product_type=p["product_type"],
        name_vi=p.get("name_vi", ""),
        min_income=p.get("min_income"),
        interest_rate=p.get("interest_rate"),
    )

    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT income_monthly FROM customers WHERE customer_id = ?",
            (customer_id,),
        )
        customer = await cursor.fetchone()
        if not customer:
            return EligibilityResult(
                product_id=product_id,
                customer_id=customer_id,
                eligible=False,
                reasons=["Customer not found"],
            )

        reasons = []
        eligible = True

        if product.min_income and customer["income_monthly"] < product.min_income:
            eligible = False
            reasons.append(
                f"Income {customer['income_monthly']:,.0f} below minimum {product.min_income:,.0f} VND"
            )

        return EligibilityResult(
            product_id=product_id,
            customer_id=customer_id,
            eligible=eligible,
            reasons=reasons,
        )
    finally:
        await db.close()
