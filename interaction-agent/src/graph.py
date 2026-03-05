"""LangGraph ReAct agent for the Soofi Interaction Agent."""

import contextvars
import json
import logging
import os

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.config import get_stream_writer
from langgraph.graph import MessagesState, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode

from .a2a_client import ask_advisor as _ask_advisor
from .a2a_client import stream_advisor as _stream_advisor
from .a2ui_surfaces import mcp_inspector_surface, n8n_surface
from .constants import (
    ADVISOR_KEY_CHUNK,
    ADVISOR_KEY_SEARCH_STATUS,
    SOOFI_EVENT_KEY,
    SOOFI_EVENT_SEARCH_STATUS,
)

logger = logging.getLogger(__name__)

# Context variable to pass the A2A context_id into tools per-request
_advisor_context_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "_advisor_context_id", default=None
)

SYSTEM_PROMPT = """\
Du bist der Soofi Trainer — ein KI-Assistent des DFKI für LLM-Spezialisierung. \
Deine Antworten erscheinen direkt im Chat-UI. Nutze Markdown.

## Tools
- **ask_advisor_tool**: Durchsucht deine Wissensdatenbank. Der Nutzer sieht den \
Aufruf NICHT — für ihn bist DU der Experte. Die Wissensdatenbank merkt sich den \
Gesprächsverlauf, du kannst Folgefragen direkt weiterleiten.
- **show_dashboard**: Zeigt Link-Karten (z.B. MCP Inspector, N8N).

## Ablauf
1. Begrüße den Nutzer einmalig und frage nach seinem Anwendungsfall.
2. Bei Fachfragen oder Anwendungsbeschreibungen: SOFORT ask_advisor_tool aufrufen.
3. Die Antwort von ask_advisor_tool DIREKT und VOLLSTÄNDIG an den Nutzer weitergeben. \
NICHT umformulieren, NICHT zusammenfassen, NICHT kürzen. Die Antwort ist bereits \
für den Nutzer geschrieben. Gib sie 1:1 aus — inklusive Quellen-Abschnitt.
4. NIEMALS "Advisor", "weiterleiten", "Wissensdatenbank" etc. erwähnen.
5. NIEMALS Fachfragen aus eigenem Wissen beantworten — IMMER ask_advisor_tool nutzen.

## Regeln
- Deutsch. Nur einmal begrüßen.
- Kein Anwendungsfall bekannt → zuerst nachfragen, nicht erfinden.
- Dashboard-Links nur auf Anfrage (z.B. "Zeig mir den MCP Inspector").
"""

model_name = os.getenv("INTERACTION_MODEL")
if not model_name:
    raise RuntimeError("INTERACTION_MODEL env var required.")

base_url = os.getenv("OPENAI_BASE_URL") or None


@tool
async def ask_advisor_tool(question: str) -> str:
    """Ask the Advisor agent a domain question via A2A.

    Use this tool for domain questions about LLM specialization,
    RAG, LoRA, fine-tuning, use-case analysis, etc.

    Args:
        question: The domain question to send to the Advisor (in German).
    """
    write = get_stream_writer()
    ctx_id = _advisor_context_id.get()
    full_text = ""

    try:
        async for chunk in _stream_advisor(question, context_id=ctx_id):
            # Detect special event envelopes from the advisor
            try:
                parsed = json.loads(chunk)
                event_type = parsed.get(SOOFI_EVENT_KEY) if isinstance(parsed, dict) else None
            except (json.JSONDecodeError, ValueError):
                event_type = None

            if event_type == SOOFI_EVENT_SEARCH_STATUS:
                write({ADVISOR_KEY_SEARCH_STATUS: parsed["text"]})
            else:
                full_text += chunk
                write({ADVISOR_KEY_CHUNK: chunk})
    except Exception:
        logger.exception("Advisor streaming failed after %d chars", len(full_text))
        if not full_text:
            logger.warning("Falling back to blocking ask_advisor call")
            full_text = await _ask_advisor(question, context_id=ctx_id)
        # Partial content already streamed — return what we have to avoid duplicates

    # Fallback if streaming completed but yielded no text (e.g. only status events)
    if not full_text:
        logger.warning("Advisor streaming yielded no content, falling back to blocking call")
        full_text = await _ask_advisor(question, context_id=ctx_id)

    return full_text


@tool
def show_dashboard(name: str) -> str:
    """Show a dashboard link as an A2UI surface.

    Args:
        name: Dashboard name — either "mcp_inspector" or "n8n".
    """
    if name == "mcp_inspector":
        surface = mcp_inspector_surface()
        return json.dumps({"surface": "mcp_inspector", "a2ui": surface}, ensure_ascii=False)
    elif name == "n8n":
        surface = n8n_surface()
        return json.dumps({"surface": "n8n", "a2ui": surface}, ensure_ascii=False)
    return json.dumps({"error": f"Unknown dashboard: {name}"}, ensure_ascii=False)


def build_graph() -> CompiledStateGraph:
    """Build the LangGraph ReAct agent for the Interaction Agent."""
    tools = [ask_advisor_tool, show_dashboard]
    llm = ChatOpenAI(
        model=model_name,
        **({"openai_api_base": base_url} if base_url else {}),
    ).bind_tools(tools)
    tool_node = ToolNode(tools)

    async def agent(state: MessagesState) -> MessagesState:
        system = {"role": "system", "content": SYSTEM_PROMPT}
        response = await llm.ainvoke([system] + state["messages"])
        if hasattr(response, "tool_calls") and response.tool_calls:
            for tc in response.tool_calls:
                logger.info("Tool call: %s(%s)", tc["name"], tc["args"])
        return {"messages": [response]}

    async def run_tools(state: MessagesState) -> MessagesState:
        result = await tool_node.ainvoke(state)
        for msg in result["messages"]:
            logger.info("Tool result (%s): %s", msg.name, str(msg.content)[:500])
        return result

    def should_continue(state: MessagesState) -> str:
        if not state["messages"]:
            return "__end__"
        last = state["messages"][-1]
        if hasattr(last, "tool_calls") and last.tool_calls:
            return "tools"
        return "__end__"

    graph_builder = StateGraph(MessagesState)
    graph_builder.add_node("agent", agent)
    graph_builder.add_node("tools", run_tools)
    graph_builder.set_entry_point("agent")
    graph_builder.add_conditional_edges(
        "agent", should_continue, {"tools": "tools", "__end__": "__end__"}
    )
    graph_builder.add_edge("tools", "agent")

    return graph_builder.compile()


def set_advisor_context_id(context_id: str | None) -> None:
    """Set the A2A context_id for the current request (used by ask_advisor_tool)."""
    _advisor_context_id.set(context_id)
