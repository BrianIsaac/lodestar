"""Tests for static product catalogue search and eligibility."""

import time

import pytest

from lodestar.models import ProductFilters


@pytest.fixture(scope="module", autouse=True)
async def seed_db():
    """Ensure the SQLite schema exists and customers are seeded for eligibility tests."""
    from lodestar.data.seed_data import seed
    from lodestar.database import get_db, init_db

    await init_db()
    db = await get_db()
    try:
        cursor = await db.execute("SELECT COUNT(*) FROM customers")
        count = (await cursor.fetchone())[0]
    finally:
        await db.close()

    if count == 0:
        await seed()


class TestProductSearch:
    """Test token-overlap search, filtering, and performance."""

    async def test_basic_search_returns_results(self) -> None:
        from lodestar.tools.products import search_products

        results = await search_products("thẻ tín dụng")
        assert len(results) > 0
        assert all(r.product_id for r in results)

    async def test_vietnamese_credit_card_query(self) -> None:
        from lodestar.tools.products import search_products

        results = await search_products("thẻ tín dụng cho lương 10 triệu")
        assert len(results) > 0
        has_credit_card = any(r.product_type == "credit_card" for r in results)
        assert has_credit_card, f"Expected credit card, got: {[r.product_type for r in results]}"

    async def test_english_query(self) -> None:
        from lodestar.tools.products import search_products

        results = await search_products("credit card cashback")
        assert len(results) > 0

    async def test_filter_by_type(self) -> None:
        from lodestar.tools.products import search_products

        results = await search_products("tiết kiệm", ProductFilters(product_type="savings"))
        assert len(results) > 0
        assert all(r.product_type == "savings" for r in results)

    async def test_filter_by_income(self) -> None:
        from lodestar.tools.products import search_products

        results = await search_products("vay", ProductFilters(min_income_lte=5_000_000))
        for r in results:
            if r.min_income is not None:
                assert r.min_income <= 5_000_000, f"{r.name_vi} requires {r.min_income}"

    async def test_filter_by_entity(self) -> None:
        from lodestar.tools.products import search_products

        results = await search_products("bảo hiểm", ProductFilters(entity="life"))
        assert len(results) > 0
        assert all(r.entity == "life" for r in results)

    async def test_no_match_returns_empty(self) -> None:
        from lodestar.tools.products import search_products

        results = await search_products("xyzzy nonsense query zzz")
        assert results == []

    async def test_query_latency(self) -> None:
        from lodestar.tools.products import search_products

        start = time.time()
        await search_products("home loan")
        elapsed = time.time() - start
        assert elapsed < 1.0, f"Query took {elapsed:.2f}s — expected <1s for static search"


class TestEligibility:
    """Test eligibility checks against the SQLite customer table."""

    async def test_check_eligibility_pass(self) -> None:
        from lodestar.tools.products import check_eligibility

        result = await check_eligibility("C002", "SB-CC-001")
        assert result.eligible is True

    async def test_check_eligibility_fail(self) -> None:
        from lodestar.tools.products import check_eligibility

        result = await check_eligibility("C003", "SB-CC-002")
        assert result.eligible is False
        assert any("Income" in r for r in result.reasons)

    async def test_unknown_product(self) -> None:
        from lodestar.tools.products import check_eligibility

        result = await check_eligibility("C001", "DOES-NOT-EXIST")
        assert result.eligible is False
        assert "Product not found" in result.reasons
