"""Tests for FastAPI endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient

from lodestar.api import app


@pytest.fixture
async def client():
    """Create an async test client for the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestHealthAndFeed:
    """Test basic endpoints that don't require the LLM."""

    async def test_health(self, client: AsyncClient) -> None:
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["customers"] >= 5

    async def test_feed_returns_cards(self, client: AsyncClient) -> None:
        resp = await client.get("/feed/C001")
        assert resp.status_code == 200
        data = resp.json()
        assert data["customer_id"] == "C001"
        assert isinstance(data["cards"], list)

    async def test_feed_unknown_customer(self, client: AsyncClient) -> None:
        resp = await client.get("/feed/UNKNOWN")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0


class TestGoals:
    """Test goal CRUD endpoints."""

    async def test_create_and_list_goal(self, client: AsyncClient) -> None:
        resp = await client.post("/goals", json={
            "customer_id": "C001",
            "name": "Test Holiday Fund",
            "target_amount": 20_000_000,
            "target_date": "2026-12-31",
        })
        assert resp.status_code == 200
        goal = resp.json()
        assert goal["name"] == "Test Holiday Fund"
        assert goal["goal_id"].startswith("G-")

        resp = await client.get("/goals/C001")
        assert resp.status_code == 200
        goals = resp.json()
        assert any(g["name"] == "Test Holiday Fund" for g in goals)


class TestSimulation:
    """Test scenario simulation endpoint."""

    async def test_home_purchase(self, client: AsyncClient) -> None:
        resp = await client.post("/simulate", json={
            "customer_id": "C002",
            "scenario_type": "home_purchase",
            "parameters": {"property_value": 2_000_000_000, "down_payment_pct": 0.2},
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["scenario_type"] == "home_purchase"
        assert len(data["entity_impacts"]) == 4
        assert data["monthly_cashflow_after"] < data["monthly_cashflow_before"]


class TestProducts:
    """Test product search endpoint."""

    async def test_search(self, client: AsyncClient) -> None:
        resp = await client.get("/products/search", params={"query": "thẻ tín dụng"})
        assert resp.status_code == 200
        products = resp.json()
        assert len(products) > 0
        assert any(p["product_type"] == "credit_card" for p in products)


class TestDismiss:
    """Test insight dismissal."""

    async def test_dismiss_insight(self, client: AsyncClient) -> None:
        feed_resp = await client.get("/feed/C001")
        cards = feed_resp.json()["cards"]
        if not cards:
            pytest.skip("No insight cards to dismiss")

        insight_id = cards[0]["insight_id"]
        resp = await client.post(
            f"/dismiss/{insight_id}",
            json={"customer_id": "C001"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "dismissed"


class TestSSEStream:
    """Test SSE endpoint is configured correctly."""

    async def test_stream_endpoint_exists(self, client: AsyncClient) -> None:
        # SSE endpoint is long-lived; just verify it doesn't 404
        from lodestar.api import app as _app

        routes = [r.path for r in _app.routes]
        assert "/stream/{customer_id}" in routes
