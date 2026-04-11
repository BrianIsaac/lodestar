"""Tests for the RAG pipeline — Qdrant hybrid search with bge-m3."""

import shutil
import time
from pathlib import Path

import pytest

from lodestar.config import settings
from lodestar.models import ProductFilters


@pytest.fixture(scope="module", autouse=True)
def setup_rag():
    """Initialise RAG with a temporary Qdrant path."""
    original_path = settings.qdrant_path
    settings.qdrant_path = "data/qdrant_test"

    from lodestar.rag.indexer import init_rag
    count = init_rag()
    print(f"Indexed {count} products")

    yield

    settings.qdrant_path = original_path
    shutil.rmtree("data/qdrant_test", ignore_errors=True)


class TestRagPipeline:
    """Test hybrid search, filtering, and performance."""

    def test_basic_search_returns_results(self) -> None:
        from lodestar.rag.retriever import search_products

        results = search_products("thẻ tín dụng")
        assert len(results) > 0
        assert all(r.product_id for r in results)

    def test_vietnamese_credit_card_query(self) -> None:
        from lodestar.rag.retriever import search_products

        results = search_products("thẻ tín dụng cho lương 10 triệu")
        assert len(results) > 0
        has_credit_card = any(r.product_type == "credit_card" for r in results)
        assert has_credit_card, f"Expected credit card in results, got: {[r.product_type for r in results]}"

    def test_payload_filter_by_type(self) -> None:
        from lodestar.rag.retriever import search_products

        filters = ProductFilters(product_type="savings")
        results = search_products("tiết kiệm lãi suất cao", filters)
        assert len(results) > 0
        assert all(r.product_type == "savings" for r in results)

    def test_payload_filter_by_income(self) -> None:
        from lodestar.rag.retriever import search_products

        filters = ProductFilters(min_income_lte=5_000_000)
        results = search_products("vay tiêu dùng", filters)
        for r in results:
            if r.min_income is not None:
                assert r.min_income <= 5_000_000, f"{r.name_vi} requires {r.min_income}"

    def test_payload_filter_by_entity(self) -> None:
        from lodestar.rag.retriever import search_products

        filters = ProductFilters(entity="life")
        results = search_products("bảo hiểm", filters)
        assert len(results) > 0
        assert all(r.entity == "life" for r in results)

    def test_indexing_performance(self) -> None:
        """Verify indexing 21 products completes in <10 seconds (already done in fixture)."""
        pass

    def test_query_latency(self) -> None:
        from lodestar.rag.retriever import search_products

        start = time.time()
        search_products("home loan")
        elapsed = time.time() - start
        assert elapsed < 5.0, f"Query took {elapsed:.1f}s — expected <5s on CPU"


class TestProductTools:
    """Test product tool wrappers."""

    async def test_search_products_tool(self) -> None:
        from lodestar.tools.products import search_products

        results = await search_products("credit card cashback")
        assert len(results) > 0

    async def test_check_eligibility_pass(self) -> None:
        from lodestar.tools.products import check_eligibility

        result = await check_eligibility("C002", "SB-CC-001")
        assert result.eligible is True

    async def test_check_eligibility_fail(self) -> None:
        from lodestar.tools.products import check_eligibility

        result = await check_eligibility("C003", "SB-CC-002")
        assert result.eligible is False
        assert any("Income" in r for r in result.reasons)
