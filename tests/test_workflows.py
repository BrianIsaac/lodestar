"""Tests for LangGraph workflow subgraphs."""

import shutil

import pytest

from lodestar.config import settings


@pytest.fixture(scope="module", autouse=True)
def setup_rag():
    """Initialise RAG for product match workflow tests."""
    original_path = settings.qdrant_path
    settings.qdrant_path = "data/qdrant_test_wf"

    from lodestar.rag.indexer import init_rag
    init_rag()

    yield

    settings.qdrant_path = original_path
    shutil.rmtree("data/qdrant_test_wf", ignore_errors=True)


class TestSpendingWorkflow:
    """Test the spending analysis LangGraph workflow."""

    async def test_end_to_end(self) -> None:
        from lodestar.agents.workflows.spending import spending_graph

        result = await spending_graph.ainvoke({
            "customer_id": "C001",
            "period": "2025-09",
            "summary": None,
            "anomalies": [],
            "chart_spec": None,
            "insight_text": "",
        })

        assert result["summary"] is not None
        assert result["summary"].total > 0
        assert result["chart_spec"] is not None
        assert result["chart_spec"].chart_type == "donut"
        insight = result["insight_text"]
        assert isinstance(insight, dict)
        assert set(insight.keys()) == {"vi", "en", "ko"}
        assert "chi tiêu" in insight["vi"].lower() or "VND" in insight["vi"]
        assert "spending" in insight["en"].lower() or "VND" in insight["en"]
        assert "지출" in insight["ko"] or "VND" in insight["ko"]

    async def test_returns_anomalies(self) -> None:
        from lodestar.agents.workflows.spending import spending_graph

        result = await spending_graph.ainvoke({
            "customer_id": "C001",
            "period": "2026-01",
            "summary": None,
            "anomalies": [],
            "chart_spec": None,
            "insight_text": "",
        })

        assert isinstance(result["anomalies"], list)


class TestProductMatchWorkflow:
    """Test the product match LangGraph workflow."""

    async def test_search_with_eligibility(self) -> None:
        from lodestar.agents.workflows.product_match import product_match_graph

        result = await product_match_graph.ainvoke({
            "query": "thẻ tín dụng",
            "customer_id": "C002",
            "results": [],
            "eligibility_checked": [],
            "insight_text": "",
        })

        assert len(result["results"]) > 0
        insight = result["insight_text"]
        assert isinstance(insight, dict)
        assert set(insight.keys()) == {"vi", "en", "ko"}
        assert "sản phẩm" in insight["vi"].lower()
        assert "thông tin sản phẩm" in insight["vi"].lower()
        assert "products" in insight["en"].lower()
        assert "상품" in insight["ko"]

    async def test_search_without_customer(self) -> None:
        from lodestar.agents.workflows.product_match import product_match_graph

        result = await product_match_graph.ainvoke({
            "query": "bảo hiểm sức khỏe",
            "customer_id": None,
            "results": [],
            "eligibility_checked": [],
            "insight_text": "",
        })

        assert len(result["results"]) > 0


class TestScenarioWorkflow:
    """Test the cross-entity scenario simulation workflow."""

    async def test_home_purchase(self) -> None:
        from lodestar.agents.workflows.scenario import scenario_graph

        result = await scenario_graph.ainvoke({
            "customer_id": "C002",
            "scenario_type": "home_purchase",
            "parameters": {"property_value": 2_000_000_000, "down_payment_pct": 0.2},
            "result": None,
            "chart_spec": None,
            "insight_text": "",
        })

        assert result["result"] is not None
        assert len(result["result"].entity_impacts) == 4
        entities = {e.entity for e in result["result"].entity_impacts}
        assert entities == {"bank", "finance", "securities", "life"}
        assert result["result"].monthly_cashflow_after < result["result"].monthly_cashflow_before

        assert result["chart_spec"] is not None
        assert result["chart_spec"].chart_type == "waterfall"

        insight = result["insight_text"]
        assert isinstance(insight, dict)
        assert set(insight.keys()) == {"vi", "en", "ko"}
        assert "kịch bản" in insight["vi"].lower() or "home_purchase" in insight["vi"]
        assert "scenario" in insight["en"].lower() or "home_purchase" in insight["en"]
        assert "시나리오" in insight["ko"] or "home_purchase" in insight["ko"]

    async def test_scenario_has_risk_flags(self) -> None:
        from lodestar.agents.workflows.scenario import scenario_graph

        result = await scenario_graph.ainvoke({
            "customer_id": "C002",
            "scenario_type": "home_purchase",
            "parameters": {"property_value": 5_000_000_000},
            "result": None,
            "chart_spec": None,
            "insight_text": "",
        })

        assert len(result["result"].risk_flags) > 0
