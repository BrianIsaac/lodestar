"""Dense retrieval with payload pre-filtering via Qdrant."""

from qdrant_client import models

from qwen_viet.models import ProductFilters, ProductInfo
from qwen_viet.rag.embeddings import embed_texts
from qwen_viet.rag.indexer import COLLECTION_NAME, get_qdrant_client


def _build_filter(filters: ProductFilters | None) -> models.Filter | None:
    """Build a Qdrant payload filter from ProductFilters.

    Args:
        filters: Optional product filter criteria.

    Returns:
        Qdrant Filter object or None.
    """
    if not filters:
        return None

    conditions = []
    if filters.product_type:
        conditions.append(
            models.FieldCondition(key="product_type", match=models.MatchValue(value=filters.product_type))
        )
    if filters.entity:
        conditions.append(
            models.FieldCondition(key="entity", match=models.MatchValue(value=filters.entity))
        )
    if filters.min_income_lte is not None:
        conditions.append(
            models.FieldCondition(key="min_income", range=models.Range(lte=filters.min_income_lte))
        )
    if filters.max_interest_rate is not None:
        conditions.append(
            models.FieldCondition(key="interest_rate", range=models.Range(lte=filters.max_interest_rate))
        )

    return models.Filter(must=conditions) if conditions else None


def search_products(
    query: str,
    filters: ProductFilters | None = None,
    limit: int = 5,
) -> list[ProductInfo]:
    """Dense vector search with payload pre-filtering.

    Args:
        query: Natural language search query (Vietnamese or English).
        filters: Optional payload filters applied before vector search.
        limit: Maximum number of results.

    Returns:
        Ranked list of matching products.
    """
    client = get_qdrant_client()
    query_vec = embed_texts([query])[0]

    qdrant_filter = _build_filter(filters)

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vec,
        query_filter=qdrant_filter,
        limit=limit,
        with_payload=True,
    )

    products = []
    for point in results.points:
        p = point.payload
        products.append(ProductInfo(
            product_id=p["product_id"],
            entity=p["entity"],
            product_type=p["product_type"],
            name_vi=p.get("name_vi", ""),
            name_en=p.get("name_en", ""),
            description_vi=p.get("description_vi", ""),
            description_en=p.get("description_en", ""),
            interest_rate=p.get("interest_rate"),
            min_income=p.get("min_income"),
            eligibility_criteria=p.get("eligibility_criteria", {}),
        ))

    return products
