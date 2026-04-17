"""Insight feed and chart data models."""

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


def _utc_naive_now() -> datetime:
    """Timezone-naive UTC default for SQLite compatibility."""
    return datetime.now(UTC).replace(tzinfo=None)


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


class QuickPrompt(BaseModel):
    """A tappable suggested next question / action surfaced on an insight card.

    `action` decides where the frontend should route the user:
    - "chat": open the drill-down chat with `text` auto-submitted
    - "plan": switch to the Plan tab, optionally pre-fill the goal form with
      `params` (name, target_amount, target_date)
    - "products": switch to the Products tab, optionally pre-fill the search
      with `params.query`
    """

    text: str
    action: str = "chat"
    params: dict = Field(default_factory=dict)


class InsightCard(BaseModel):
    """A single proactive insight displayed on the feed.

    `title` and `summary` hold the canonical Vietnamese text for backwards
    compat; `title_i18n` and `summary_i18n` carry the same content in all
    supported locales. The frontend prefers the i18n dict when present so
    toggling language is a pure client-side lookup — zero runtime LLM
    calls, zero network translation.

    Cards now carry two extra presentation fields surfaced directly in the
    feed (not just on the drill-down page):

    - `action_hint_i18n`: short list of compliance-safe "có thể cân nhắc"
      bullet points showing what the customer might do about the observed
      pattern. Same three-language dict shape as summary_i18n but the value
      is a list of strings.
    - `quick_prompts_i18n`: three language-matched chip-prompts that either
      open the drill-down chat with the prompt pre-submitted, or deep-link
      into the Plan or Products tab.
    """

    insight_id: str
    customer_id: str
    title: str
    summary: str
    title_i18n: dict[str, str] | None = None
    summary_i18n: dict[str, str] | None = None
    action_hint_i18n: dict[str, list[str]] | None = None
    quick_prompts_i18n: dict[str, list[QuickPrompt]] | None = None
    severity: InsightSeverity = InsightSeverity.INFO
    chart_spec: ChartSpec | None = None
    suggested_actions: list[str] = Field(default_factory=list)
    compliance_class: ComplianceClass = ComplianceClass.INFORMATION
    created_at: datetime = Field(default_factory=_utc_naive_now)
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
