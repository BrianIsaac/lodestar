"""Reactive orchestrator — Qwen3 with workflow-as-tool pattern.

Uses the OpenAI-compatible API from llama-server/Ollama. Selects
pre-built workflow tools for known intents, falls back to direct
LLM response for novel queries.
"""

import json
import logging

from openai import AsyncOpenAI

from lodestar.agents.compliance import apply_compliance_multilingual
from lodestar.config import settings
from lodestar.models import ChatMessage, ChatResponse, ChartSpec

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_VI = """Bạn là trợ lý tài chính AI cho Shinhan Bank Việt Nam, được nhúng trong ứng dụng SOL.

Vai trò:
- Phân tích chi tiêu, thu nhập và lịch sử giao dịch của khách hàng
- Đề xuất kế hoạch tiết kiệm và thông tin sản phẩm phù hợp
- Trả lời câu hỏi tài chính bằng tiếng Việt tự nhiên

Quy tắc:
- LUÔN sử dụng công cụ (tools) cho mọi tính toán — KHÔNG BAO GIỜ tự tính toán
- Chỉ cung cấp THÔNG TIN sản phẩm, KHÔNG đưa ra lời khuyên đầu tư
- Trả lời ngắn gọn, rõ ràng, dễ hiểu
- Khi không chắc chắn, đề xuất liên hệ chuyên viên Shinhan

LUÔN trả lời bằng tiếng Việt."""

SYSTEM_PROMPT_EN = """You are the AI financial coach for Shinhan Bank Vietnam, embedded in the SOL app.

Role:
- Analyse the customer's spending, income, and transaction history
- Suggest savings plans and relevant product information
- Answer financial questions in clear, natural English

Rules:
- ALWAYS use the provided tools for any calculation — NEVER compute values yourself
- Provide product INFORMATION only, NEVER give investment advice
- Keep answers concise and clear
- When unsure, suggest contacting a Shinhan advisor

ALWAYS answer in English, even if the user's question is in Vietnamese.
Tool results may come back in Vietnamese — translate all user-facing output to English."""

SYSTEM_PROMPT_KO = """당신은 신한은행 베트남의 SOL 앱에 내장된 AI 금융 코치입니다.

역할:
- 고객의 지출, 수입, 거래 내역 분석
- 저축 계획 및 적합한 상품 정보 제안
- 자연스러운 한국어로 금융 관련 질문에 답변

규칙:
- 모든 계산은 반드시 제공된 도구(tools)를 사용 — 직접 계산하지 말 것
- 상품 정보만 제공하며, 투자 자문은 절대 제공하지 말 것
- 답변은 간결하고 명확하게
- 확실하지 않을 때는 신한 상담원 문의를 제안할 것

항상 한국어로 답변하십시오. 사용자의 질문이 베트남어로 들어와도 한국어로 답변해야 합니다.
도구의 결과가 베트남어로 나오면 사용자에게 보여주는 모든 내용을 한국어로 번역하십시오."""


def _system_prompt_for(language: str) -> str:
    """Pick the system prompt that matches the requested language."""
    if language == "en":
        return SYSTEM_PROMPT_EN
    if language == "ko":
        return SYSTEM_PROMPT_KO
    return SYSTEM_PROMPT_VI

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "spending_analysis",
            "description": "Analyse spending for a customer over a specific month. Returns summary with chart.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string", "description": "Customer ID (e.g. C001)"},
                    "period": {"type": "string", "description": "Month in YYYY-MM format"},
                },
                "required": ["customer_id", "period"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "product_search",
            "description": "Search Shinhan products. Returns product information (NOT advice).",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query in Vietnamese or English"},
                    "customer_id": {"type": "string", "description": "Customer ID for eligibility check (optional)"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "scenario_simulation",
            "description": "Simulate a financial scenario across Bank/Finance/Securities/Life entities.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string"},
                    "scenario_type": {"type": "string", "description": "home_purchase | career_change | new_baby | marriage"},
                    "parameters": {"type": "object", "description": "Scenario-specific parameters"},
                },
                "required": ["customer_id", "scenario_type"],
            },
        },
    },
]


_FOLLOWUP_SUGGESTIONS: dict[str, dict[str, list[str]]] = {
    "spending_analysis": {
        "vi": [
            "So sánh với tháng trước",
            "Khoản chi nào lớn nhất?",
            "Làm sao để tiết kiệm thêm?",
        ],
        "en": [
            "Compare with last month",
            "What was the biggest expense?",
            "How can I save more?",
        ],
        "ko": [
            "지난달과 비교해 주세요",
            "가장 큰 지출은 무엇이었나요?",
            "어떻게 더 절약할 수 있을까요?",
        ],
    },
    "product_search": {
        "vi": [
            "Điều kiện đủ cho sản phẩm này là gì?",
            "Có lựa chọn nào khác?",
            "So sánh hai sản phẩm hàng đầu",
        ],
        "en": [
            "What are the eligibility requirements?",
            "What other options exist?",
            "Compare the top two",
        ],
        "ko": [
            "자격 요건은 무엇인가요?",
            "다른 선택지가 있나요?",
            "상위 두 상품을 비교해 주세요",
        ],
    },
    "scenario_simulation": {
        "vi": [
            "Thử giảm giá nhà đi 20%",
            "Nếu lãi suất tăng thì sao?",
            "Nhìn vào cả bốn đơn vị Shinhan",
        ],
        "en": [
            "Try reducing the home price by 20%",
            "What if the interest rate rises?",
            "Show the four Shinhan entities",
        ],
        "ko": [
            "주택 가격을 20% 낮춰보기",
            "금리가 오르면 어떻게 될까요?",
            "신한 4개 계열사 전체 영향 보기",
        ],
    },
}


_ERROR_MESSAGES = {
    "vi": "Xin lỗi, đã xảy ra lỗi. Vui lòng thử lại.",
    "en": "Sorry, something went wrong. Please try again.",
    "ko": "죄송합니다. 오류가 발생했습니다. 다시 시도해주세요.",
}


_JSON_DECODER = json.JSONDecoder()


def _parse_final_json(raw: str) -> dict:
    """Parse the final-turn response, extracting a JSON object even when
    the model wraps it in a preamble like "Here is the JSON: {…}".

    Uses :class:`json.JSONDecoder.raw_decode` for the preamble case so
    string-escaped braces inside the JSON payload do not confuse the
    parse — a naive brace counter would terminate early on content like
    ``{"example":"use {key: value}"}``.

    Returns the parsed dict or an empty dict if no JSON object can be
    recovered. The caller is responsible for surfacing a localised
    fallback — this helper never leaks the raw text to a user bubble.
    """
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        value = None

    if isinstance(value, dict):
        return value

    # Preamble / suffix fallback: scan for every `{` and let the proper
    # decoder tell us where the object ends. response_format=json_object
    # usually prevents this case, but some Qwen builds prefix "Here is
    # the JSON: …" despite the flag.
    start = raw.find("{")
    while start != -1:
        try:
            value, _end = _JSON_DECODER.raw_decode(raw, start)
        except json.JSONDecodeError:
            start = raw.find("{", start + 1)
            continue
        if isinstance(value, dict):
            return value
        start = raw.find("{", start + 1)
    return {}


def _followups_for(tool_names: list[str], language: str) -> list[str]:
    """Return 3 contextual follow-up prompts based on which tool fired.

    Returns empty when no tool ran so the UI falls back to its default
    chip set. Contextual chips make the tool-calling loop feel purposeful
    instead of opaque.
    """
    if not tool_names:
        return []
    lang = language if language in ("vi", "en", "ko") else "vi"
    for name in tool_names:
        bundle = _FOLLOWUP_SUGGESTIONS.get(name)
        if bundle:
            return list(bundle.get(lang, bundle.get("vi", [])))
    return []


def _pick_text(text_or_dict: object, language: str) -> str:
    """Resolve a workflow's `insight_text` output to a single string.

    Each compose_* node now returns a {vi, en, ko} dict so every language
    is pre-rendered. Fall through to Vietnamese for unknown locales and
    gracefully handle legacy str outputs just in case."""
    if isinstance(text_or_dict, dict):
        return text_or_dict.get(language) or text_or_dict.get("vi") or ""
    return str(text_or_dict or "")


async def _execute_tool(name: str, arguments: dict, language: str = "vi") -> str:
    """Execute a workflow tool and return the result as a JSON string.

    Workflow compose_* nodes author `insight_text` as a per-language dict,
    so this function picks the requested locale with zero LLM calls — no
    translation, no cache warmup, no round-trips.

    Args:
        name: Tool name.
        arguments: Tool arguments from the LLM.
        language: Requested response locale (vi | en | ko).

    Returns:
        JSON string of tool results (serialised for the LLM's tool turn).
    """
    if name == "spending_analysis":
        from lodestar.agents.workflows.spending import spending_graph
        result = await spending_graph.ainvoke({
            "customer_id": arguments["customer_id"],
            "period": arguments["period"],
            "summary": None, "anomalies": [], "chart_spec": None, "insight_text": {},
        })
        return json.dumps({
            "insight_text": _pick_text(result["insight_text"], language),
            "chart_spec": result["chart_spec"].model_dump() if result["chart_spec"] else None,
        }, ensure_ascii=False)

    elif name == "product_search":
        from lodestar.agents.workflows.product_match import product_match_graph
        result = await product_match_graph.ainvoke({
            "query": arguments["query"],
            "customer_id": arguments.get("customer_id"),
            "results": [], "eligibility_checked": [], "insight_text": {},
        })
        return json.dumps(
            {"insight_text": _pick_text(result["insight_text"], language)},
            ensure_ascii=False,
        )

    elif name == "scenario_simulation":
        from lodestar.agents.workflows.scenario import scenario_graph
        result = await scenario_graph.ainvoke({
            "customer_id": arguments["customer_id"],
            "scenario_type": arguments["scenario_type"],
            "parameters": arguments.get("parameters", {}),
            "result": None, "chart_spec": None, "insight_text": {},
        })
        return json.dumps({
            "insight_text": _pick_text(result["insight_text"], language),
            "chart_spec": result["chart_spec"].model_dump() if result["chart_spec"] else None,
        }, ensure_ascii=False)

    return json.dumps({"error": f"Unknown tool: {name}"})


def _get_client() -> AsyncOpenAI:
    """Get an OpenAI-compatible client for llama-server.

    Returns:
        AsyncOpenAI client configured for the local inference server.
    """
    return AsyncOpenAI(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
    )


async def chat(
    messages: list[ChatMessage],
    customer_id: str,
    insight_context: str = "",
    language: str = "vi",
) -> tuple[ChatResponse, dict[str, str]]:
    """Process a user message through the reactive orchestrator.

    Args:
        messages: Conversation history.
        customer_id: Current customer ID (for tool context).
        insight_context: Pre-loaded insight context if drilling down.
        language: Target response language — "vi", "en", or "ko". Selects
            the system prompt that constrains the assistant's output.

    Returns:
        A ``(ChatResponse, user_message_i18n)`` tuple. ``ChatResponse``
        carries the assistant message (tri-lingual via ``content_i18n``)
        plus tool trace and i18n follow-up chips. ``user_message_i18n``
        is the user's last message translated verbatim into each locale
        so the caller can persist it for the drill-down history replay.
    """
    client = _get_client()

    system_content = _system_prompt_for(language)
    if insight_context:
        system_content += f"\n\nContext from insight:\n{insight_context}"
    system_content += f"\n\nCurrent customer: {customer_id}"

    api_messages = [{"role": "system", "content": system_content}]
    for msg in messages:
        api_messages.append({"role": msg.role, "content": msg.content})

    try:
        # Turn 1 — tool-calling turn. The model needs enough headroom to
        # serialise the full tool_calls payload; truncating mid-arguments
        # produces a malformed JSON string that the dispatcher below
        # cannot recover from, leaking a KeyError on required tool args.
        response = await client.chat.completions.create(
            model=settings.llm_model,
            messages=api_messages,
            tools=TOOL_DEFINITIONS,
            temperature=0.7,
            max_tokens=1024,
        )

        choice = response.choices[0]
        chart_spec = None
        tool_names: list[str] = []

        if choice.message.tool_calls:
            # Execute every tool the LLM asked for, not just the first.
            # Every tool_call in the assistant message MUST have a matching
            # `role="tool"` reply before turn 2 or the OpenAI-compat
            # contract is violated and the model sees a malformed
            # conversation. On parse/exec failure we still append a
            # synthetic error result so the pairing stays intact.
            api_messages.append(choice.message.model_dump())
            for tool_call in choice.message.tool_calls:
                tool_name = tool_call.function.name
                tool_names.append(tool_name)

                try:
                    tool_args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    logger.warning(
                        "tool_call args failed JSON parse for %s — marking failed",
                        tool_name,
                    )
                    api_messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(
                            {"error": "arguments were not valid JSON"},
                            ensure_ascii=False,
                        ),
                    })
                    continue

                if "customer_id" not in tool_args:
                    tool_args["customer_id"] = customer_id

                try:
                    tool_result = await _execute_tool(
                        tool_name, tool_args, language=language
                    )
                except Exception:
                    # Stack + class name go to the log; only a generic
                    # marker reaches the LLM's turn-2 context. Echoing a
                    # raw exception class name (e.g. "ConnectionError")
                    # via the LLM's synthesis would leak internals into
                    # a user-visible chat bubble.
                    logger.exception("tool %s failed — marking failed", tool_name)
                    tool_result = json.dumps(
                        {"error": "tool unavailable"},
                        ensure_ascii=False,
                    )

                try:
                    tool_data = json.loads(tool_result)
                except json.JSONDecodeError:
                    tool_data = {}

                if chart_spec is None and tool_data.get("chart_spec"):
                    chart_spec = ChartSpec(**tool_data["chart_spec"])

                api_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result,
                })

        # Turn 2 — final synthesis turn. Always runs (tool or no-tool),
        # and always emits tri-lingual JSON so a client language toggle
        # can swap the bubble without a round-trip. Mirrors the detector
        # pattern: tools stripped, response_format=json_object, bumped
        # max_tokens. The user_message_i18n field is also authored here
        # so the user bubble can swap on toggle too.
        _raw_user = messages[-1].content if messages else ""
        api_messages.append({
            "role": "user",
            "content": (
                "Produce your final reply as a single JSON object with this "
                "exact shape:\n"
                "{\n"
                '  "content_i18n": {"vi": "...", "en": "...", "ko": "..."},\n'
                '  "user_message_i18n": {"vi": "...", "en": "...", "ko": "..."}\n'
                "}\n"
                "`content_i18n` is your assistant reply in all three locales, "
                "consistent in meaning and tone across them. "
                "`user_message_i18n` must contain the user's exact last "
                "message translated verbatim into each locale — do not "
                "rephrase, summarise or answer the user's message inside "
                "this field; preserve register, abbreviations and informal "
                "phrasing. Echo the original locale's value unchanged. "
                f"The user's last message was: {_raw_user!r}."
            ),
        })

        final = await client.chat.completions.create(
            model=settings.llm_model,
            messages=api_messages,
            temperature=0.3,
            max_tokens=2048,
            response_format={"type": "json_object"},
        )
        final_text = final.choices[0].message.content or "{}"

        parsed = _parse_final_json(final_text)

        content_i18n_raw = parsed.get("content_i18n") if isinstance(parsed, dict) else None
        user_i18n_raw = parsed.get("user_message_i18n") if isinstance(parsed, dict) else None

        # Coerce + trim to strings; drop any unknown locales.
        content_i18n: dict[str, str] = {}
        if isinstance(content_i18n_raw, dict):
            for lang in ("vi", "en", "ko"):
                v = content_i18n_raw.get(lang)
                if isinstance(v, str) and v.strip():
                    content_i18n[lang] = v

        if not content_i18n:
            # Degraded path: JSON mode ensures final_text is SOME JSON, but
            # the expected shape may be wrong. Surface a localised fallback
            # rather than leak raw JSON preamble into a chat bubble.
            logger.warning(
                "final-turn JSON missing content_i18n; emitting localised fallback"
            )
            content_i18n = {
                "vi": _ERROR_MESSAGES["vi"],
                "en": _ERROR_MESSAGES["en"],
                "ko": _ERROR_MESSAGES["ko"],
            }

        user_message_i18n: dict[str, str] = {}
        if isinstance(user_i18n_raw, dict):
            for lang in ("vi", "en", "ko"):
                v = user_i18n_raw.get(lang)
                if isinstance(v, str) and v.strip():
                    user_message_i18n[lang] = v
        # Always ensure the original locale reflects the verbatim user text.
        if _raw_user:
            user_message_i18n.setdefault(language, _raw_user)

        # One multilingual compliance pass so a Vi refusal cannot ship
        # next to untreated En/Ko advice-style copy.
        filtered_i18n, _cls = apply_compliance_multilingual(content_i18n)

        display_content = filtered_i18n.get(language) or filtered_i18n.get("vi") or final_text
        followups_dict = {
            "vi": _followups_for(tool_names, "vi"),
            "en": _followups_for(tool_names, "en"),
            "ko": _followups_for(tool_names, "ko"),
        }

        return ChatResponse(
            message=ChatMessage(
                role="assistant",
                content=display_content,
                content_i18n=filtered_i18n or None,
                chart_spec=chart_spec,
            ),
            suggested_followups=followups_dict.get(language, []),
            suggested_followups_i18n=followups_dict,
            tool_calls=tool_names,
        ), user_message_i18n

    except Exception:
        logger.exception("Orchestrator error")
        # Let the API layer map this to a 502 with a localised detail so
        # the HTTP status carries the real failure signal; a 200 with
        # error text would hide the failure from monitoring/retries.
        raise
