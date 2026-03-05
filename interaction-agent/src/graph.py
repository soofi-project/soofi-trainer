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
from .a2a_client import ask_training_agent as _ask_training_agent
from .a2a_client import stream_advisor as _stream_advisor
from .a2a_client import stream_training_agent as _stream_training_agent
from .a2ui_surfaces import mcp_inspector_surface, n8n_surface
from .constants import (
    ADVISOR_KEY_CHUNK,
    ADVISOR_KEY_SEARCH_STATUS,
    SOOFI_EVENT_JOB_STARTED,
    SOOFI_EVENT_KEY,
    SOOFI_EVENT_SEARCH_STATUS,
    TRAINING_AGENT_KEY_CHUNK,
    TRAINING_AGENT_KEY_JOB_STARTED,
    TRAINING_AGENT_KEY_STATUS,
)

logger = logging.getLogger(__name__)

# Context variables to pass the A2A context_id into tools per-request
_advisor_context_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "_advisor_context_id", default=None
)
_training_context_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "_training_context_id", default=None
)

SYSTEM_PROMPT = """\
Du bist der Soofi Trainer — ein KI-Assistent des DFKI für LLM-Spezialisierung. \
Deine Antworten erscheinen direkt im Chat-UI. Nutze Markdown.

## Tools
- **ask_advisor_tool**: Für Fachfragen zu LLM-Spezialisierung (RAG, Fine-Tuning, LoRA, QLoRA, \
Datensätze, Methoden-Empfehlungen, Use-Case-Analyse). Der Nutzer sieht den Aufruf NICHT — \
für ihn bist DU der Experte. Merkt sich den Gesprächsverlauf.
- **ask_training_agent_tool**: Für Trainingsaufträge (Job starten, Status abfragen, Job abbrechen).
- **show_dashboard**: Zeigt Link-Karten (z.B. MCP Inspector, N8N).

## Tool-Wahl
- **ask_advisor_tool**: Fachfragen — Wissen, Erklärungen, Vergleiche, Empfehlungen \
(z.B. "Was ist LoRA?", "Was weißt du über RAG?", "Erkläre QLoRA", "Wann Fine-Tuning?"). \
Jede Frage der Form "Was weißt du über X", "Erkläre X", "Was ist X" ist eine Fachfrage — \
SOFORT ask_advisor_tool, nie selbst antworten.
- **ask_training_agent_tool**: Job-Operationen — einen Job starten, den Status abfragen, \
einen Job abbrechen (z.B. "Starte ein LoRA-Training", "Was ist der Status von Job xyz?").
- **show_dashboard**: Link-Karten nur auf explizite Anfrage.

## Ablauf
1. Enthält die Nachricht ein Thema oder eine Fachfrage (LoRA, RAG, Fine-Tuning, \
Modell-Vergleich, Datensätze usw.): SOFORT ask_advisor_tool aufrufen — \
auch beim allerersten Satz, auch mit Begrüßung.
2. Trainingsauftrag (Job starten, Status, Abbruch): SOFORT ask_training_agent_tool aufrufen.
3. Reine Begrüßung ohne jedes Thema → einmalig begrüßen und nach dem Anwendungsfall fragen.
4. Antworten DIREKT und VOLLSTÄNDIG weitergeben — NICHT umformulieren, NICHT kürzen.
5. NIEMALS "Advisor", "Training Agent", "weiterleiten", "Wissensdatenbank" erwähnen.
6. NIEMALS Fachfragen aus eigenem Wissen beantworten — IMMER ask_advisor_tool nutzen.

## Regeln
- Deutsch. Nur einmal begrüßen.
- Dashboard-Links nur auf Anfrage (z.B. "Zeig mir den MCP Inspector").
"""

model_name = os.getenv("INTERACTION_MODEL")
if not model_name:
    raise RuntimeError("INTERACTION_MODEL env var required.")


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
async def ask_training_agent_tool(question: str) -> str:
    """Ask the Training Agent to manage a training job via A2A.

    Use this tool for training job operations: starting a training job,
    checking job status, listing jobs, or cancelling a job.

    Args:
        question: The training request to send to the Training Agent (in German).
    """
    write = get_stream_writer()
    ctx_id = _training_context_id.get()
    full_text = ""

    try:
        async for chunk in _stream_training_agent(question, context_id=ctx_id):
            # Detect special event envelopes from the training agent
            try:
                parsed = json.loads(chunk)
                event_type = parsed.get(SOOFI_EVENT_KEY) if isinstance(parsed, dict) else None
            except (json.JSONDecodeError, ValueError):
                event_type = None

            if event_type == SOOFI_EVENT_JOB_STARTED:
                write({TRAINING_AGENT_KEY_JOB_STARTED: parsed.get("job_id", "")})
            else:
                full_text += chunk
                write({TRAINING_AGENT_KEY_CHUNK: chunk})
    except Exception:
        logger.exception("Training agent streaming failed after %d chars", len(full_text))
        if not full_text:
            logger.warning("Falling back to blocking ask_training_agent call")
            full_text = await _ask_training_agent(question, context_id=ctx_id)

    if not full_text:
        logger.warning("Training agent streaming yielded no content, falling back to blocking call")
        full_text = await _ask_training_agent(question, context_id=ctx_id)

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
    tools = [ask_advisor_tool, ask_training_agent_tool, show_dashboard]
    llm = ChatOpenAI(model=model_name).bind_tools(tools)
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


def set_training_context_id(context_id: str | None) -> None:
    """Set the A2A context_id for the current request (used by ask_training_agent_tool)."""
    _training_context_id.set(context_id)
