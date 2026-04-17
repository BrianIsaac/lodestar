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
        try:
            resp = await client.get("/products/search", params={"query": "thẻ tín dụng"})
            assert resp.status_code == 200
            products = resp.json()
            assert len(products) > 0
            assert any(p["product_type"] == "credit_card" for p in products)
        except Exception as e:
            if "OutOfMemoryError" in str(e) or "CUDA" in str(e):
                pytest.skip("GPU OOM — embedding model cannot load alongside other processes")
            raise


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


class TestChatHistory:
    """History endpoint reconstructs the interaction thread."""

    async def test_unknown_insight_returns_empty_list(
        self, client: AsyncClient
    ) -> None:
        resp = await client.get("/chat/INS-nonexistent/history")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_history_replay_with_tool_chips_and_i18n(
        self, client: AsyncClient
    ) -> None:
        """A stored interaction with an assistant turn that used tools and
        has tri-lingual content round-trips through /history with the tool
        chip injected before the assistant bubble and content_i18n preserved.
        """
        from lodestar.database import get_db
        from lodestar.learning.interactions import record_interaction

        # Insert a placeholder card so the FK on interactions is satisfied.
        insight_id = "INS-history-test"
        db = await get_db()
        try:
            await db.execute(
                """INSERT INTO insight_cards
                   (insight_id, customer_id, title, summary, severity,
                    suggested_actions, compliance_class, priority_score,
                    created_at, dismissed)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)""",
                (
                    insight_id,
                    "C001",
                    "history test",
                    "history test summary",
                    "info",
                    "[]",
                    "information",
                    0.5,
                    "2026-04-17T00:00:00",
                ),
            )
            await db.commit()
        finally:
            await db.close()

        await record_interaction(
            customer_id="C001",
            insight_id=insight_id,
            messages=[
                # Non-chat roles must be filtered out by the endpoint.
                {"role": "event", "content": "transaction detected"},
                {"role": "user", "content": "Vì sao tôi nhận được thẻ này?"},
                {
                    "role": "assistant",
                    "content": "Here is why.",
                    "content_i18n": {
                        "vi": "Đây là lý do.",
                        "en": "Here is why.",
                        "ko": "이유는 이렇습니다.",
                    },
                    "tool_calls": ["spending_analysis"],
                },
            ],
        )

        resp = await client.get(f"/chat/{insight_id}/history")
        assert resp.status_code == 200
        msgs = resp.json()

        roles = [m["role"] for m in msgs]
        assert roles == ["user", "tool", "assistant"], roles
        assert msgs[1]["content"] == "spending_analysis"
        assert msgs[2]["content_i18n"]["ko"] == "이유는 이렇습니다."
        assert msgs[2]["content_i18n"]["vi"] == "Đây là lý do."

        # Cleanup — FK ordering: interactions → insight_cards.
        db = await get_db()
        try:
            await db.execute(
                "DELETE FROM interactions WHERE insight_id = ?", (insight_id,)
            )
            await db.execute(
                "DELETE FROM insight_cards WHERE insight_id = ?", (insight_id,)
            )
            await db.commit()
        finally:
            await db.close()


class TestInteractionConcurrency:
    """append_to_interaction must serialise concurrent writers — the
    BEGIN IMMEDIATE guard in interactions.py means both appends are
    preserved instead of racing on the messages blob."""

    async def test_concurrent_appends_preserve_all_entries(self) -> None:
        import asyncio

        from lodestar.database import get_db
        from lodestar.learning.interactions import (
            append_to_interaction,
            get_interaction_for_insight,
            record_interaction,
        )

        insight_id = "INS-concur-test"
        db = await get_db()
        try:
            await db.execute(
                """INSERT INTO insight_cards
                   (insight_id, customer_id, title, summary, severity,
                    suggested_actions, compliance_class, priority_score,
                    created_at, dismissed)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)""",
                (
                    insight_id,
                    "C001",
                    "concur test",
                    "concur test summary",
                    "info",
                    "[]",
                    "information",
                    0.5,
                    "2026-04-17T00:00:00",
                ),
            )
            await db.commit()
        finally:
            await db.close()

        await record_interaction(
            customer_id="C001", insight_id=insight_id, messages=[]
        )

        N = 10
        await asyncio.gather(
            *[
                append_to_interaction(
                    insight_id, {"role": "event", "content": f"entry {i}"}
                )
                for i in range(N)
            ]
        )

        record = await get_interaction_for_insight(insight_id)
        assert record is not None
        contents = {m["content"] for m in record["messages"]}
        assert contents == {f"entry {i}" for i in range(N)}, (
            f"lost entries under concurrency: {contents}"
        )

        db = await get_db()
        try:
            await db.execute(
                "DELETE FROM interactions WHERE insight_id = ?", (insight_id,)
            )
            await db.execute(
                "DELETE FROM insight_cards WHERE insight_id = ?", (insight_id,)
            )
            await db.commit()
        finally:
            await db.close()
