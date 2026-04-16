"""Insight feed and chart data models."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class InsightSeverity(StrEnum):
    """Priority levels for insight cards."""

    LIFE_EVENT = "life_event"
    ANOMALY = "anomaly"
    MILESTONE = "milestone"
    INFO = "info"
    PRODUCT = "product"


class ComplianceClass(StrEnum):
    """Compliance classification for outputs."""

    INFORMATION = "information"
    GUIDANCE = "guidance"
    ADVICE = "advice"


class ChartSpec(BaseModel):
    """Structured chart specification rendered by the frontend."""

    chart_type: str = Field(description="donut | bar | line | progress | waterfall | grouped_bar")
    title: str = ""
    data: dict = Field(default_factory=dict)
    axes: dict | None = None
    summary: str = ""


class InsightCard(BaseModel):
    """A single proactive insight displayed on the feed.

    `title` and `summary` hold the canonical Vietnamese text for backwards
    compat; `title_i18n` and `summary_i18n` carry the same content in all
    supported locales. The frontend prefers the i18n dict when present so
    toggling language is a pure client-side lookup — zero runtime LLM
    calls, zero network translation.
    """

    insight_id: str
    customer_id: str
    title: str
    summary: str
    title_i18n: dict[str, str] | None = None
    summary_i18n: dict[str, str] | None = None
    severity: InsightSeverity = InsightSeverity.INFO
    chart_spec: ChartSpec | None = None
    suggested_actions: list[str] = Field(default_factory=list)
    compliance_class: ComplianceClass = ComplianceClass.INFORMATION
    created_at: datetime = Field(default_factory=datetime.utcnow)
    dismissed: bool = False
    priority_score: float = 0.0


class InsightFeed(BaseModel):
    """Paginated list of insight cards."""

    customer_id: str
    cards: list[InsightCard] = Field(default_factory=list)
    total: int = 0


class ChatMessage(BaseModel):
    """A single message in a drill-down chat thread."""

    role: str = Field(description="user | assistant | system | tool")
    content: str = ""
    chart_spec: ChartSpec | None = None
    insight_id: str | None = None


class InsightCardI18n(BaseModel):
    """Parallel structure carrying title/summary in every supported locale."""

    vi: str = ""
    en: str = ""
    ko: str = ""


class ChatResponse(BaseModel):
    """Response from the reactive orchestrator."""

    message: ChatMessage
    suggested_followups: list[str] = Field(default_factory=list)
    tool_calls: list[str] = Field(
        default_factory=list,
        description=(
            "Names of tools invoked by the orchestrator while producing this "
            "response. Surfaced to the UI so the tool-calling loop is visible."
        ),
    )
