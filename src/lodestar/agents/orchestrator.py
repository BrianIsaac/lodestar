"""Reactive orchestrator — Qwen3 with workflow-as-tool pattern.

Uses the OpenAI-compatible API from llama-server/Ollama. Selects
pre-built workflow tools for known intents, falls back to direct
LLM response for novel queries.
"""

import json
import logging

from openai import AsyncOpenAI

from lodestar.agents.compliance import apply_compliance
from lodestar.config import settings
from lodestar.models import ChatMessage, ChatResponse, ChartSpec

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Bạn là trợ lý tài chính AI cho Shinhan Bank Việt Nam, được nhúng trong ứng dụng SOL.

Vai trò:
- Phân tích chi tiêu, thu nhập và lịch sử giao dịch của khách hàng
- Đề xuất kế hoạch tiết kiệm và thông tin sản phẩm phù hợp
- Trả lời câu hỏi tài chính bằng tiếng Việt tự nhiên

Quy tắc:
- LUÔN sử dụng công cụ (tools) cho mọi tính toán — KHÔNG BAO GIỜ tự tính toán
- Chỉ cung cấp THÔNG TIN sản phẩm, KHÔNG đưa ra lời khuyên đầu tư
- Trả lời ngắn gọn, rõ ràng, dễ hiểu
- Khi không chắc chắn, đề xuất liên hệ chuyên viên Shinhan

You also speak English and Korean for international customers."""

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
                    "scenario_type": {"type": "string", "description": "home_purchase | career_change | new_baby"},
                    "parameters": {"type": "object", "description": "Scenario-specific parameters"},
                },
                "required": ["customer_id", "scenario_type"],
            },
        },
    },
]


async def _execute_tool(name: str, arguments: dict) -> str:
    """Execute a workflow tool and return the result as a string.

    Args:
        name: Tool name.
        arguments: Tool arguments from the LLM.

    Returns:
        JSON string of tool results.
    """
    if name == "spending_analysis":
        from lodestar.agents.workflows.spending import spending_graph
        result = await spending_graph.ainvoke({
            "customer_id": arguments["customer_id"],
            "period": arguments["period"],
            "summary": None, "anomalies": [], "chart_spec": None, "insight_text": "",
        })
        return json.dumps({
            "insight_text": result["insight_text"],
            "chart_spec": result["chart_spec"].model_dump() if result["chart_spec"] else None,
        }, ensure_ascii=False)

    elif name == "product_search":
        from lodestar.agents.workflows.product_match import product_match_graph
        result = await product_match_graph.ainvoke({
            "query": arguments["query"],
            "customer_id": arguments.get("customer_id"),
            "results": [], "eligibility_checked": [], "insight_text": "",
        })
        return json.dumps({"insight_text": result["insight_text"]}, ensure_ascii=False)

    elif name == "scenario_simulation":
        from lodestar.agents.workflows.scenario import scenario_graph
        result = await scenario_graph.ainvoke({
            "customer_id": arguments["customer_id"],
            "scenario_type": arguments["scenario_type"],
            "parameters": arguments.get("parameters", {}),
            "result": None, "chart_spec": None, "insight_text": "",
        })
        return json.dumps({
            "insight_text": result["insight_text"],
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
        api_key="not-needed",
    )


async def chat(
    messages: list[ChatMessage],
    customer_id: str,
    insight_context: str = "",
) -> ChatResponse:
    """Process a user message through the reactive orchestrator.

    Args:
        messages: Conversation history.
        customer_id: Current customer ID (for tool context).
        insight_context: Pre-loaded insight context if drilling down.

    Returns:
        ChatResponse with assistant message and optional chart.
    """
    client = _get_client()

    system_content = SYSTEM_PROMPT
    if insight_context:
        system_content += f"\n\nContext from insight:\n{insight_context}"
    system_content += f"\n\nCurrent customer: {customer_id}"

    api_messages = [{"role": "system", "content": system_content}]
    for msg in messages:
        api_messages.append({"role": msg.role, "content": msg.content})

    try:
        response = await client.chat.completions.create(
            model=settings.llm_model,
            messages=api_messages,
            tools=TOOL_DEFINITIONS,
            temperature=0.7,
            max_tokens=2048,
        )

        choice = response.choices[0]
        chart_spec = None

        if choice.message.tool_calls:
            tool_call = choice.message.tool_calls[0]
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)

            if "customer_id" not in tool_args:
                tool_args["customer_id"] = customer_id

            tool_result = await _execute_tool(tool_name, tool_args)
            tool_data = json.loads(tool_result)

            if "chart_spec" in tool_data and tool_data["chart_spec"]:
                chart_spec = ChartSpec(**tool_data["chart_spec"])

            api_messages.append(choice.message.model_dump())
            api_messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_result,
            })

            followup = await client.chat.completions.create(
                model=settings.llm_model,
                messages=api_messages,
                temperature=0.7,
                max_tokens=1024,
            )
            assistant_text = followup.choices[0].message.content or ""
        else:
            assistant_text = choice.message.content or ""

        filtered_text, _ = apply_compliance(assistant_text)

        return ChatResponse(
            message=ChatMessage(
                role="assistant",
                content=filtered_text,
                chart_spec=chart_spec,
            ),
            suggested_followups=[],
        )

    except Exception as e:
        logger.exception("Orchestrator error")
        return ChatResponse(
            message=ChatMessage(
                role="assistant",
                content=f"Xin lỗi, đã xảy ra lỗi. Vui lòng thử lại. ({type(e).__name__})",
            ),
        )
