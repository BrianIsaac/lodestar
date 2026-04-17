"""Product search and eligibility tools."""

from lodestar.database import get_db
from lodestar.models import EligibilityResult, ProductFilters, ProductInfo
from lodestar.rag import retriever


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
    from lodestar.rag.indexer import COLLECTION_NAME, get_qdrant_client
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

    p = points[0].payload or {}
    product = ProductInfo(
        product_id=p.get("product_id", product_id),
        entity=p.get("entity", ""),
        product_type=p.get("product_type", ""),
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
