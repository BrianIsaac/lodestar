"""Product search, comparison, and eligibility tools.

Backed by a static JSON catalogue. Search is token-overlap scoring across
Vietnamese + English name/description/type fields — adequate for a PoC
with ~20-40 curated products.
"""

import json
import re
from functools import lru_cache
from pathlib import Path

from lodestar.database import get_db
from lodestar.models import ComparisonTable, EligibilityResult, ProductFilters, ProductInfo

CATALOGUE_PATH = Path(__file__).parent.parent / "data" / "products_catalogue.json"


@lru_cache(maxsize=1)
def _load_catalogue() -> list[ProductInfo]:
    """Load and validate the product catalogue once per process."""
    with open(CATALOGUE_PATH) as f:
        raw = json.load(f)
    return [ProductInfo(**p) for p in raw]


def _tokenise(text: str) -> list[str]:
    """Lowercase and split on non-alphanumerics. Handles Vietnamese diacritics."""
    return [t for t in re.split(r"[^\w]+", text.casefold(), flags=re.UNICODE) if t]


def _passes_filters(product: ProductInfo, filters: ProductFilters | None) -> bool:
    if not filters:
        return True
    if filters.product_type and product.product_type != filters.product_type:
        return False
    if filters.entity and product.entity != filters.entity:
        return False
    if filters.min_income_lte is not None:
        if product.min_income is not None and product.min_income > filters.min_income_lte:
            return False
    if filters.max_interest_rate is not None:
        if product.interest_rate is not None and product.interest_rate > filters.max_interest_rate:
            return False
    return True


def _score(product: ProductInfo, query_tokens: list[str]) -> int:
    """Token-overlap score. Matches in name weighted 3x, type 2x, description 1x."""
    if not query_tokens:
        return 0
    name_tokens = set(_tokenise(f"{product.name_vi} {product.name_en}"))
    type_tokens = set(_tokenise(product.product_type))
    desc_tokens = set(_tokenise(f"{product.description_vi} {product.description_en}"))

    score = 0
    for tok in query_tokens:
        if tok in name_tokens:
            score += 3
        if tok in type_tokens:
            score += 2
        if tok in desc_tokens:
            score += 1
    return score


def _search_sync(
    query: str, filters: ProductFilters | None = None, limit: int = 5
) -> list[ProductInfo]:
    catalogue = _load_catalogue()
    candidates = [p for p in catalogue if _passes_filters(p, filters)]
    query_tokens = _tokenise(query)

    scored = [(p, _score(p, query_tokens)) for p in candidates]
    scored = [s for s in scored if s[1] > 0]
    scored.sort(key=lambda x: (-x[1], x[0].product_id))
    return [p for p, _ in scored[:limit]]


async def search_products(
    query: str, filters: ProductFilters | None = None
) -> list[ProductInfo]:
    """Search the static Shinhan product catalogue.

    Args:
        query: Natural language query (Vietnamese or English).
        filters: Optional payload filters.

    Returns:
        Ranked list of matching products (top 5).
    """
    return _search_sync(query, filters)


async def compare_products(product_ids: list[str]) -> ComparisonTable:
    """Side-by-side comparison of selected products.

    Args:
        product_ids: List of product IDs to compare.

    Returns:
        ComparisonTable with aligned rows.
    """
    by_id = {p.product_id: p for p in _load_catalogue()}
    columns = ["name_vi", "product_type", "entity", "interest_rate", "min_income"]
    rows = []
    for pid in product_ids:
        p = by_id.get(pid)
        if not p:
            continue
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
    by_id = {p.product_id: p for p in _load_catalogue()}
    product = by_id.get(product_id)
    if not product:
        return EligibilityResult(
            product_id=product_id,
            customer_id=customer_id,
            eligible=False,
            reasons=["Product not found"],
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
