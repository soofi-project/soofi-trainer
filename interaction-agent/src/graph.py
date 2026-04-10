"""LangGraph ReAct agent for the Soofi Interaction Agent."""

import asyncio
import collections
import contextvars
import functools
import json
import logging
import os
from typing import Any, Literal

import httpx
from langchain_core.callbacks import adispatch_custom_event
from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode

from .a2a_client import ask_advisor as _ask_advisor
from .a2a_client import ask_dataset_agent as _ask_dataset_agent
from .a2a_client import ask_training_agent as _ask_training_agent
from .a2a_client import stream_advisor as _stream_advisor
from .a2a_client import stream_dataset_agent as _stream_dataset_agent
from .a2a_client import stream_training_agent as _stream_training_agent
from .constants import (
    ADVISOR_EVENT,
    ADVISOR_KEY_CHUNK,
    ADVISOR_KEY_SEARCH_STATUS,
    AGENT_CARD_EVENT,
    AGENT_CARD_KEY,
    DATASET_AGENT_KEY_CHUNK,
    DATASET_AGENT_KEY_STATUS,
    DATASET_AGENT_KEY_TOOL,
    DATASET_EVENT,
    DOC_VIEWER_KEY,
    ADVISOR_KEY_RAG_SOURCES,
    SOOFI_EVENT_JOB_STARTED,
    SOOFI_EVENT_KEY,
    SOOFI_EVENT_RAG_SOURCES,
    SOOFI_EVENT_SEARCH_STATUS,
    TRAINING_AGENT_KEY_CHUNK,
    TRAINING_AGENT_KEY_JOB_STARTED,
    TRAINING_AGENT_KEY_STATUS,
    TRAINING_EVENT,
    TRAINING_VIEW_EVENT,
    TRAINING_VIEW_KEY,
)
from .i18n import Language, tr
from .prompts import get_system_prompt

logger = logging.getLogger(__name__)

_duckduckgo_web_search = DuckDuckGoSearchResults(num_results=5)
_OPENAI_WEB_SEARCH_TOOL = {"type": "web_search_preview"}


# Context variables to pass the A2A context_id into tools per-request
_advisor_context_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "_advisor_context_id", default=None
)
_training_context_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "_training_context_id", default=None
)
_dataset_context_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "_dataset_context_id", default=None
)
_language: contextvars.ContextVar[Language] = contextvars.ContextVar("_language", default="de")
# RAG source URLs per conversation — persisted across requests via advisor context_id.
# LRU-bounded to prevent unbounded memory growth from long-running processes.
_RAG_URLS_MAX = 256
_rag_urls_store: collections.OrderedDict[str, list[str]] = collections.OrderedDict()

base_url = os.getenv("OPENAI_BASE_URL") or None
model_name = os.getenv("INTERACTION_MODEL")
if not model_name:
    raise RuntimeError("INTERACTION_MODEL env var required.")

# Agent registry: parsed from AGENT_REGISTRY env var (comma-separated name=url pairs)
_raw_registry = os.getenv("AGENT_REGISTRY", "")
AGENT_REGISTRY: dict[str, str] = {}
for pair in _raw_registry.split(","):
    pair = pair.strip()
    if "=" in pair:
        name, url = pair.split("=", 1)
        AGENT_REGISTRY[name.strip()] = url.strip()

logger.info("Agent registry: %s", list(AGENT_REGISTRY.keys()))


def _get_openai_web_search_config() -> dict[str, str | None]:
    """Resolve dedicated config for the OpenAI-backed web-search backend."""
    model = (os.getenv("INTERACTION_WEB_SEARCH_OPENAI_MODEL") or "gpt-4.1-mini").strip()
    if not model:
        model = "gpt-4.1-mini"

    return {
        "model": model,
        "base_url": os.getenv("INTERACTION_WEB_SEARCH_OPENAI_BASE_URL") or None,
        "api_key": (
            os.getenv("INTERACTION_WEB_SEARCH_OPENAI_API_KEY")
            or os.getenv("OPENAI_API_KEY")
            or None
        ),
    }


def _extract_openai_web_search_text(response: Any) -> str:
    """Normalize an OpenAI Responses API result to plain text."""
    text = getattr(response, "text", None)
    if isinstance(text, str) and text.strip():
        return text.strip()

    content = getattr(response, "content", None)
    if isinstance(content, str) and content.strip():
        return content.strip()
    if isinstance(content, list):
        parts = [
            part.get("text", "")
            for part in content
            if isinstance(part, dict) and part.get("type") == "text" and part.get("text")
        ]
        if parts:
            return "\n".join(parts).strip()

    # Ignore annotations/citations and keep the wrapper contract as plain text.
    content_blocks = getattr(response, "content_blocks", None)
    if isinstance(content_blocks, list):
        parts = [
            block.get("text", "")
            for block in content_blocks
            if isinstance(block, dict) and block.get("type") == "text" and block.get("text")
        ]
        if parts:
            return "\n".join(parts).strip()

    raise ValueError("OpenAI web search returned no text content.")


@functools.lru_cache(maxsize=1)
def _get_openai_web_search_llm() -> Any:
    """Build the dedicated ChatOpenAI client for built-in web search."""
    config = _get_openai_web_search_config()
    if not config["api_key"]:
        raise RuntimeError(
            "OpenAI web search requires INTERACTION_WEB_SEARCH_OPENAI_API_KEY or OPENAI_API_KEY."
        )

    kwargs: dict[str, Any] = {
        "model": config["model"],
        "api_key": config["api_key"],
        "use_responses_api": True,
    }
    if config["base_url"]:
        kwargs["base_url"] = config["base_url"]

    return ChatOpenAI(**kwargs).bind_tools([_OPENAI_WEB_SEARCH_TOOL])


def _web_search_duckduckgo(query: str) -> str:
    """Search the public web with DuckDuckGo."""
    return _duckduckgo_web_search.run(query)


def _web_search_openai(query: str) -> str:
    """Search the public web with ChatOpenAI built-in web search."""
    response = _get_openai_web_search_llm().invoke(query)
    return _extract_openai_web_search_text(response)


# Manual backend selection for web_search_tool. Keep exactly one assignment active.
# The OpenAI variant uses INTERACTION_WEB_SEARCH_OPENAI_* config and a dedicated
# Responses API client instead of the main interaction-model endpoint.
_active_web_search_backend = _web_search_duckduckgo
# _active_web_search_backend = _web_search_openai


async def _fetch_agent_card(
    name: str, base_url: str, client: httpx.AsyncClient | None = None, lang: str = "de"
) -> dict[str, Any]:
    """Fetch an A2A agent card from /.well-known/agent-card.json."""
    card_url = f"{base_url.rstrip('/')}/a2a/.well-known/agent-card.json?lang={lang}"
    try:
        if client is None:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(card_url)
        else:
            resp = await client.get(card_url)
        resp.raise_for_status()
        data = resp.json()
        data["_status"] = "online"
        return data
    except Exception as exc:
        logger.warning("Failed to fetch agent card for %s at %s: %s", name, card_url, exc)
        return {"name": name, "url": base_url, "_status": "offline", "_error": str(exc)}


@tool
async def show_agent_card(
    agent: Literal[
        "all", "interaction-agent", "advisor", "training-agent", "dataset-agent", "close"
    ],  # Keep enum values in sync with AGENT_REGISTRY in .env
) -> str:
    """Show or close the A2A agent card panel. YOU MUST call this tool — never respond with text only.

    REQUIRED for: agent cards, agent details, "welche Agenten", "Agenten zeigen/schließen",
    "mach zu", "schließen", "close". Use "close" to close the panel.
    Never confirm open/close actions without calling this tool first.

    Args:
        agent: Which agent card to show, "all" for all agents, or "close" to close.
    """
    lang = _language.get()
    if agent == "close":
        await adispatch_custom_event(
            AGENT_CARD_EVENT, {AGENT_CARD_KEY: {"action": "close"}}
        )
        return tr("cards_closed", lang)

    if agent == "all":
        # Keep in sync with Literal enum above and AGENT_REGISTRY in .env
        async with httpx.AsyncClient(timeout=3.0) as client:
            tasks = {
                name: _fetch_agent_card(name, url, client, lang=lang)
                for name, url in AGENT_REGISTRY.items()
            }
            results = await asyncio.gather(*tasks.values())
        cards = list(zip(tasks.keys(), results))
    elif agent in AGENT_REGISTRY:
        card = await _fetch_agent_card(agent, AGENT_REGISTRY[agent], lang=lang)
        cards = [(agent, card)]
    else:
        available = ", ".join(AGENT_REGISTRY.keys())
        return tr("agent_not_found", lang, agent=agent, available=available)

    # Send card data to the frontend panel via custom event (SSE).
    # The LLM only sees the short confirmation below — not the full card data.
    await adispatch_custom_event(
        AGENT_CARD_EVENT, {AGENT_CARD_KEY: {"action": "open", "cards": cards}}
    )
    names = [name for name, _ in cards]
    if len(names) == 1:
        return tr("card_opened", lang, name=names[0])
    return tr("cards_opened", lang, count=len(names))



@tool
async def ask_advisor_tool(question: str) -> str:
    """Ask the Advisor agent a domain question via A2A.

    Use this tool for domain questions about LLM specialization,
    RAG, LoRA, fine-tuning, use-case analysis, etc.

    Args:
        question: The domain question to send to the Advisor.
    """
    ctx_id = _advisor_context_id.get()
    lang = _language.get()
    full_text = ""
    lang_tag = f" [LANG:{lang}]"

    try:
        async for chunk in _stream_advisor(question + lang_tag, context_id=ctx_id):
            # Detect special event envelopes from the advisor
            try:
                parsed = json.loads(chunk)
                event_type = parsed.get(SOOFI_EVENT_KEY) if isinstance(parsed, dict) else None
            except (json.JSONDecodeError, ValueError):
                event_type = None

            if event_type == SOOFI_EVENT_SEARCH_STATUS:
                await adispatch_custom_event(
                    ADVISOR_EVENT, {ADVISOR_KEY_SEARCH_STATUS: parsed["text"]}
                )
            elif event_type == SOOFI_EVENT_RAG_SOURCES:
                await adispatch_custom_event(
                    ADVISOR_EVENT, {ADVISOR_KEY_RAG_SOURCES: parsed["sources"]}
                )
                # Store source URLs so control_doc_viewer can reference them
                urls = [
                    s.get("url", "") for s in parsed.get("sources", [])
                    if s.get("url")
                ]
                ctx_key = _advisor_context_id.get() or ""
                _rag_urls_store[ctx_key] = urls
                _rag_urls_store.move_to_end(ctx_key)
                while len(_rag_urls_store) > _RAG_URLS_MAX:
                    _rag_urls_store.popitem(last=False)
            else:
                full_text += chunk
                await adispatch_custom_event(
                    ADVISOR_EVENT, {ADVISOR_KEY_CHUNK: chunk}
                )
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
        question: The training request to send to the Training Agent.
    """
    ctx_id = _training_context_id.get()
    lang = _language.get()
    full_text = ""
    lang_tag = f" [LANG:{lang}]"

    try:
        async for chunk in _stream_training_agent(question + lang_tag, context_id=ctx_id):
            # Detect special event envelopes from the training agent
            try:
                parsed = json.loads(chunk)
                event_type = parsed.get(SOOFI_EVENT_KEY) if isinstance(parsed, dict) else None
            except (json.JSONDecodeError, ValueError):
                event_type = None

            if event_type == SOOFI_EVENT_JOB_STARTED:
                await adispatch_custom_event(
                    TRAINING_EVENT, {TRAINING_AGENT_KEY_JOB_STARTED: parsed.get("job_id", "")}
                )
            elif event_type == SOOFI_EVENT_SEARCH_STATUS:
                await adispatch_custom_event(
                    TRAINING_EVENT, {TRAINING_AGENT_KEY_STATUS: parsed.get("text", "")}
                )
            else:
                full_text += chunk
                await adispatch_custom_event(
                    TRAINING_EVENT, {TRAINING_AGENT_KEY_CHUNK: chunk}
                )
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
async def ask_dataset_agent_tool(question: str) -> str:
    """Ask the Dataset Agent to search for suitable public datasets via A2A.

    Use this tool for dataset discovery requests, especially searches on
    HuggingFace and Eclipse Dataspace (EDC).

    Args:
        question: The dataset search request to send to the Dataset Agent.
    """
    ctx_id = _dataset_context_id.get()
    lang = _language.get()
    full_text = ""
    lang_tag = f" [LANG:{lang}]"

    try:
        async for chunk in _stream_dataset_agent(question + lang_tag, context_id=ctx_id):
            try:
                parsed = json.loads(chunk)
                event_type = parsed.get(SOOFI_EVENT_KEY) if isinstance(parsed, dict) else None
            except (json.JSONDecodeError, ValueError):
                event_type = None

            if event_type == SOOFI_EVENT_SEARCH_STATUS:
                payload: dict[str, str] = {DATASET_AGENT_KEY_STATUS: parsed.get("text", "")}
                tool = parsed.get("tool", "")
                if tool:
                    payload[DATASET_AGENT_KEY_TOOL] = tool
                await adispatch_custom_event(DATASET_EVENT, payload)
            else:
                full_text += chunk
                await adispatch_custom_event(
                    DATASET_EVENT, {DATASET_AGENT_KEY_CHUNK: chunk}
                )
    except Exception:
        logger.exception("Dataset agent streaming failed after %d chars", len(full_text))
        if not full_text:
            logger.warning("Falling back to blocking ask_dataset_agent call")
            full_text = await _ask_dataset_agent(question, context_id=ctx_id)

    if not full_text:
        logger.warning("Dataset agent streaming yielded no content, falling back to blocking call")
        full_text = await _ask_dataset_agent(question, context_id=ctx_id)

    return full_text


@tool
def web_search_tool(query: str) -> str:
    """Search the public web for explicit lookup requests or current public information.

    Use this tool when the user explicitly asks to search or browse the web, or asks for
    current/latest/recent public-web information outside the dataset and training flows.

    Args:
        query: The search query to look up on the public web.
    """
    lang = _language.get()
    try:
        return _active_web_search_backend(query)
    except Exception:
        logger.exception("Web search failed for query: %s", query)
        return tr("web_search_failed", lang)


@tool
async def control_training_view(action: Literal["open", "close"]) -> str:
    """Open or close the training jobs panel. YOU MUST call this tool — never respond with text only.

    REQUIRED for: "Jobs zeigen", "Trainingsübersicht", "Job-Ansicht schließen",
    "show jobs", "close training view". Never confirm open/close without calling this tool first.

    Args:
        action: "open" to show the training jobs panel, "close" to hide it.
    """
    lang = _language.get()
    await adispatch_custom_event(
        TRAINING_VIEW_EVENT, {TRAINING_VIEW_KEY: {"action": action}}
    )
    if action == "close":
        return tr("training_view_closed", lang)
    return tr("training_view_opened", lang)



@tool
def control_doc_viewer(action: str, index: int = 1) -> str:
    """Control the document/sources viewer. YOU MUST call this tool — never respond with text only.

    REQUIRED for: "öffne Quelle X", "Quelle schließen", "nächste Quelle", "mach zu",
    "close sources", "open source X". Never confirm open/close without calling this tool first.

    Args:
        action: One of "open", "close", "next", "previous".
                "open" opens the source at the given index (1-based).
        index: 1-based index matching the numbered sources shown below the answer.
    """
    lang = _language.get()
    if action == "close":
        label = tr("doc_closed", lang)
    elif action == "next":
        label = tr("doc_next", lang)
    elif action == "previous":
        label = tr("doc_previous", lang)
    else:
        ctx_key = _advisor_context_id.get() or ""
        urls = _rag_urls_store.get(ctx_key, [])
        total = len(urls)
        if total == 0:
            return tr("doc_none", lang)
        if index < 1 or index > total:
            return tr("doc_invalid_index", lang, index=index, total=total)
        label = tr("doc_opened", lang, index=index)
    return json.dumps(
        {DOC_VIEWER_KEY: {"action": action, "index": index}, "label": label},
        ensure_ascii=False,
    )


def build_graph() -> CompiledStateGraph:
    """Build the LangGraph ReAct agent for the Interaction Agent."""
    tools = [
        ask_advisor_tool,
        ask_training_agent_tool,
        ask_dataset_agent_tool,
        web_search_tool,
        show_agent_card,
        control_doc_viewer,
        control_training_view,
    ]
    llm = ChatOpenAI(
        model=model_name,
        **({"openai_api_base": base_url} if base_url else {}),
    ).bind_tools(tools, **({"parallel_tool_calls": False} if not base_url else {}))
    tool_node = ToolNode(tools)

    async def agent(state: MessagesState) -> MessagesState:
        system = {"role": "system", "content": get_system_prompt(_language.get())}
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

    # Tools whose responses are already streamed to the user — no second LLM call needed
    _STREAMING_TOOLS = {"ask_advisor_tool", "ask_training_agent_tool", "ask_dataset_agent_tool"}

    def should_continue(state: MessagesState) -> str:
        if not state["messages"]:
            return "__end__"
        last = state["messages"][-1]
        if hasattr(last, "tool_calls") and last.tool_calls:
            return "tools"
        return "__end__"

    def after_tools(state: MessagesState) -> str:
        """Skip the second LLM call if a streaming tool already delivered the response."""
        for msg in reversed(state["messages"]):
            # Stop at the last AI message — don't look further back
            if hasattr(msg, "tool_calls"):
                break
            if hasattr(msg, "name") and msg.name in _STREAMING_TOOLS:
                return "__end__"
        return "agent"

    graph_builder = StateGraph(MessagesState)
    graph_builder.add_node("agent", agent)
    graph_builder.add_node("tools", run_tools)
    graph_builder.set_entry_point("agent")
    graph_builder.add_conditional_edges(
        "agent", should_continue, {"tools": "tools", "__end__": "__end__"}
    )
    graph_builder.add_conditional_edges(
        "tools", after_tools, {"agent": "agent", "__end__": "__end__"}
    )

    return graph_builder.compile()


def set_advisor_context_id(context_id: str | None) -> None:
    """Set the A2A context_id for the current request (used by ask_advisor_tool)."""
    _advisor_context_id.set(context_id)


def set_training_context_id(context_id: str | None) -> None:
    """Set the A2A context_id for the current request (used by ask_training_agent_tool)."""
    _training_context_id.set(context_id)


def set_dataset_context_id(context_id: str | None) -> None:
    """Set the A2A context_id for the current request (used by ask_dataset_agent_tool)."""
    _dataset_context_id.set(context_id)


def set_language(lang: Language) -> None:
    """Set the language for the current request."""
    _language.set(lang)
