"""LangGraph ReAct agent for the Soofi Dataset Agent."""

import logging
import os
from typing import Any

from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import MessagesState, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode

from .prompts import SYSTEM_PROMPT_DE

logger = logging.getLogger(__name__)

_TRUE_VALUES = {"1", "true", "yes", "on"}
_FALSE_VALUES = {"0", "false", "no", "off"}

model = os.getenv("DATASET_AGENT_MODEL")
if not model:
    raise RuntimeError("DATASET_AGENT_MODEL env var required.")

base_url = os.getenv("OPENAI_BASE_URL") or None


def _get_optional_env(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None
    value = value.strip()
    return value or None


def _get_required_env(name: str) -> str:
    value = _get_optional_env(name)
    if value is None:
        raise RuntimeError(f"{name} env var required.")
    return value


def _parse_float_env(name: str) -> float:
    raw = _get_required_env(name)
    try:
        return float(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} env var must be a float, got {raw!r}.") from exc


def _parse_int_env(name: str) -> int:
    raw = _get_required_env(name)
    try:
        return int(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} env var must be an integer, got {raw!r}.") from exc


def _parse_bool_env(name: str) -> bool:
    raw = _get_required_env(name)
    normalized = raw.lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False
    raise RuntimeError(
        f"{name} env var must be a boolean (true/false/1/0/yes/no/on/off), got {raw!r}."
    )


def _parse_optional_float_env(name: str) -> float | None:
    if _get_optional_env(name) is None:
        return None
    return _parse_float_env(name)


def _parse_optional_int_env(name: str) -> int | None:
    if _get_optional_env(name) is None:
        return None
    return _parse_int_env(name)


def _build_vllm_kwargs(prefix: str) -> dict[str, Any]:
    if _get_optional_env("SOOFI_LLM_BACKEND") != "vllm":
        return {}
    if not base_url:
        raise RuntimeError("OPENAI_BASE_URL env var required when SOOFI_LLM_BACKEND=vllm.")

    extra_body: dict[str, Any] = {
        "min_p": _parse_float_env(f"{prefix}_MIN_P"),
        "chat_template_kwargs": {
            "enable_thinking": _parse_bool_env(f"{prefix}_ENABLE_THINKING")
        },
    }

    top_k = _parse_optional_int_env(f"{prefix}_TOP_K")
    if top_k is not None:
        extra_body["top_k"] = top_k

    repetition_penalty = _parse_optional_float_env(f"{prefix}_REPEAT_PENALTY")
    if repetition_penalty is not None:
        extra_body["repetition_penalty"] = repetition_penalty

    llm_kwargs: dict[str, Any] = {
        "temperature": _parse_float_env(f"{prefix}_TEMPERATURE"),
        "top_p": _parse_float_env(f"{prefix}_TOP_P"),
        "extra_body": extra_body,
    }

    presence_penalty = _parse_optional_float_env(f"{prefix}_PRESENCE_PENALTY")
    if presence_penalty is not None:
        llm_kwargs["presence_penalty"] = presence_penalty

    return llm_kwargs


def build_graph(tools: list[BaseTool]) -> CompiledStateGraph:
    """Build the LangGraph ReAct agent with the given tools."""
    llm = ChatOpenAI(
        model=model,
        **({"openai_api_base": base_url} if base_url else {}),
        **_build_vllm_kwargs("DATASET_AGENT"),
    ).bind_tools(tools, **({"parallel_tool_calls": False} if not base_url else {}))
    tool_node = ToolNode(tools)

    async def agent(state: MessagesState, config: RunnableConfig) -> MessagesState:
        prompt = config.get("configurable", {}).get("system_prompt", SYSTEM_PROMPT_DE)
        system = {"role": "system", "content": prompt}
        response = await llm.ainvoke([system] + state["messages"])
        if hasattr(response, "tool_calls") and response.tool_calls:
            for tc in response.tool_calls:
                logger.info("Tool call: %s(%s)", tc["name"], tc["args"])
        return {"messages": [response]}

    async def log_tool_results(state: MessagesState) -> MessagesState:
        try:
            result = await tool_node.ainvoke(state)
            for msg in result["messages"]:
                logger.info("Tool result (%s): %s", msg.name, str(msg.content)[:500])
            return result
        except Exception as exc:
            logger.exception("Tool execution failed")
            last = state["messages"][-1]
            if not (hasattr(last, "tool_calls") and last.tool_calls):
                raise
            return {
                "messages": [
                    ToolMessage(
                        content=f"Tool error: {exc}",
                        tool_call_id=tc["id"],
                        name=tc["name"],
                    )
                    for tc in last.tool_calls
                ]
            }

    def should_continue(state: MessagesState) -> str:
        if not state["messages"]:
            return "__end__"
        last = state["messages"][-1]
        if hasattr(last, "tool_calls") and last.tool_calls:
            return "tools"
        return "__end__"

    graph_builder = StateGraph(MessagesState)
    graph_builder.add_node("agent", agent)
    graph_builder.add_node("tools", log_tool_results)
    graph_builder.set_entry_point("agent")
    graph_builder.add_conditional_edges(
        "agent", should_continue, {"tools": "tools", "__end__": "__end__"}
    )
    graph_builder.add_edge("tools", "agent")

    memory = MemorySaver()
    return graph_builder.compile(checkpointer=memory)
