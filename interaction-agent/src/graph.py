"""LangGraph ReAct agent for the Soofi Interaction Agent."""

import asyncio
import collections
import contextvars
import json
import logging
import os
import re
from typing import Any, Literal

import httpx
from langchain_core.callbacks import adispatch_custom_event
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field

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
    TRANSITION_EVENT,
    TRANSITION_KEY,
)
from .i18n import Language, tr
from .prompts import get_slot_extraction_prompt, get_system_prompt

logger = logging.getLogger(__name__)

_TRUE_VALUES = {"1", "true", "yes", "on"}
_FALSE_VALUES = {"0", "false", "no", "off"}

_DEFAULT_SEARXNG_HOST = "http://searxng:8080"


# Context variable to pass the advisor context_id per-request (used for RAG URL store)
_advisor_context_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "_advisor_context_id", default=None
)
_language: contextvars.ContextVar[Language] = contextvars.ContextVar("_language", default="de")
# RAG source URLs per conversation — persisted across requests via advisor context_id.
# LRU-bounded to prevent unbounded memory growth from long-running processes.
_RAG_URLS_MAX = 256
_rag_urls_store: collections.OrderedDict[str, list[str]] = collections.OrderedDict()


# ---------------------------------------------------------------------------
# Typed state — slots carry the 4 training parameters derived from history.
# ---------------------------------------------------------------------------


class SlotState(BaseModel):
    """The 4 parameters needed to start a training job, plus a workflow flag."""

    use_case: str | None = Field(
        None,
        description=(
            "The user's target application/domain (e.g. 'Compliance', "
            "'Wissensmanagement', 'Predictive Maintenance'). None if not yet chosen."
        ),
    )
    dataset: str | None = Field(
        None,
        description=(
            "A concrete dataset the user has selected (e.g. 'medical-de-v1', "
            "'HuggingFace: foo/bar'). None if not yet chosen."
        ),
    )
    base_model: str | None = Field(
        None,
        description="Base model (e.g. 'Llama-3.1-8B', 'Mistral-7B'). None if not yet chosen.",
    )
    method: str | None = Field(
        None,
        description="Specialization method (RAG, LoRA, QLoRA, SFT, DPO). None if not yet chosen.",
    )
    workflow_intent: bool = Field(
        False,
        description=(
            "True if the user is actively working toward starting a training job "
            "(exploring use cases, datasets, models, methods). False for purely "
            "factual/exploratory questions like 'What is LoRA?'."
        ),
    )

    def next_missing(self) -> str | None:
        """Return the key of the next missing slot, or None if all filled."""
        if not self.use_case:
            return "use_case"
        if not self.dataset:
            return "dataset"
        if not self.base_model:
            return "base_model"
        if not self.method:
            return "method"
        return None


# Per-request slot snapshot — set in run_tools before tool execution so tools
# can check the user's workflow intent without needing access to graph state.
_slots: contextvars.ContextVar[SlotState | None] = contextvars.ContextVar(
    "_slots", default=None
)


class SoofiState(TypedDict):
    """Graph state: messages plus extracted slot state."""

    messages: Annotated[list[AnyMessage], add_messages]
    slots: SlotState


# Deterministic transition templates — appended by transition_node based on
# the next missing slot. Keeps the interaction prompt short and responses predictable.
_TRANSITIONS: dict[Language, dict[str, str]] = {
    "de": {
        "use_case": "Für welchen Anwendungsfall möchten Sie ein Modell spezialisieren?",
        "dataset": "Soll ich dazu passende Datensätze suchen?",
        "base_model": "Soll ich ein passendes Basismodell empfehlen?",
        "method": "Soll ich eine Spezialisierungsmethode empfehlen?",
        "ready": "Soll ich das Training jetzt starten?",
    },
    "en": {
        "use_case": "Which use case would you like to specialize a model for?",
        "dataset": "Should I search for suitable datasets?",
        "base_model": "Should I recommend a suitable base model?",
        "method": "Should I recommend a specialization method?",
        "ready": "Should I start the training now?",
    },
}

base_url = os.getenv("OPENAI_BASE_URL") or None
model_name = os.getenv("INTERACTION_MODEL")
if not model_name:
    raise RuntimeError("INTERACTION_MODEL env var required.")


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


# Second ChatOpenAI instance — same model/endpoint/sampling as the main agent,
# but without bind_tools. Used one-shot via ainvoke() to summarize web search
# results outside the agent's message history, so raw snippets never pollute
# the main context window.
_utility_llm = ChatOpenAI(
    model=model_name,
    **({"openai_api_base": base_url} if base_url else {}),
    **_build_vllm_kwargs("INTERACTION"),
)


# Agent registry: parsed from AGENT_REGISTRY env var (comma-separated name=url pairs)
_raw_registry = os.getenv("AGENT_REGISTRY", "")
AGENT_REGISTRY: dict[str, str] = {}
for pair in _raw_registry.split(","):
    pair = pair.strip()
    if "=" in pair:
        name, url = pair.split("=", 1)
        AGENT_REGISTRY[name.strip()] = url.strip()

logger.info("Agent registry: %s", list(AGENT_REGISTRY.keys()))


def _get_searxng_web_search_config() -> dict[str, str]:
    """Resolve config for the self-hosted SearXNG-backed web-search backend."""
    host = (os.getenv("INTERACTION_WEB_SEARCH_SEARXNG_HOST") or _DEFAULT_SEARXNG_HOST).strip()
    if not host:
        host = _DEFAULT_SEARXNG_HOST

    return {"host": host}


_WEB_SEARCH_ENGINES = [
    "google",
    "bing",
    "wikipedia",
    # "duckduckgo" and "brave" do not reliably honor the `language`
    # parameter — foreign-language hits leak into the results otherwise.
    # "duckduckgo",
    # "brave",
]
_WEB_SEARCH_RESULT_LIMIT = 5

# CJK, Hiragana/Katakana, Arabic, Hebrew, Cyrillic. Even Bing's `language=de`
# filter is only a hint, so hits in these scripts still leak through — we
# drop them client-side for DE/EN user turns.
_NON_LATIN_SCRIPT_RE = re.compile(
    r"[\u0400-\u04ff\u0590-\u05ff\u0600-\u06ff\u3040-\u30ff\u4e00-\u9fff]"
)


def _looks_non_latin(text: str) -> bool:
    """True if more than 15% of characters are non-Latin script."""
    if not text:
        return False
    non_latin = len(_NON_LATIN_SCRIPT_RE.findall(text))
    return non_latin / len(text) > 0.15


async def _web_search_searxng(query: str, language: Language) -> str:
    """Search the public web with a self-hosted SearXNG instance.

    Queries the SearXNG JSON API directly (instead of SearxSearchWrapper) so
    that both ``results`` (regular hits) and ``infoboxes`` (Wikipedia summary
    cards) can be surfaced — the wrapper only exposes ``results``.
    """
    host = _get_searxng_web_search_config()["host"]
    logger.info("Web search backend=searxng host=%s", host)
    params = {
        "q": query,
        "format": "json",
        "language": language,
        "engines": ",".join(_WEB_SEARCH_ENGINES),
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{host.rstrip('/')}/search", params=params)
        response.raise_for_status()
        data = response.json()

    sections: list[str] = []
    kept = 0
    for r in data.get("results") or []:
        if kept >= _WEB_SEARCH_RESULT_LIMIT:
            break
        title = r.get("title", "")
        url = r.get("url", "")
        snippet = r.get("content", "")
        if _looks_non_latin(title) or _looks_non_latin(snippet):
            logger.info("Dropping non-Latin web hit: %s", url)
            continue
        sections.append(f"**{title}** — {url}\n{snippet}")
        kept += 1

    for ib in data.get("infoboxes") or []:
        title = ib.get("infobox", "")
        url = ib.get("id", "")
        content = ib.get("content", "")
        if _looks_non_latin(title) or _looks_non_latin(content):
            continue
        sections.append(f"**{title}** — {url}\n{content}")

    if not sections:
        return tr("web_search_no_results", language)
    return "\n\n".join(sections)


_SUMMARY_PROMPT_DE = """\
Beantworte die Nutzerfrage anhand der folgenden Web-Suchergebnisse. Format:

1. Eine kompakte Antwort — **maximal 2 Sätze**, nur die Kernaussage, keine \
Zitate, keine Quellen im Fließtext.
2. Danach eine Leerzeile und darunter eine Quellenliste als Markdown-Bulletpoints, \
gruppiert und ohne Dopplungen, im Format:
   - [Titel der Seite](URL)

Verwende ausschließlich URLs, die wörtlich in den Ergebnissen vorkommen — keine \
erfinden, keine kombinieren. Wenn die Treffer keine brauchbare Antwort zulassen, \
sag das ehrlich in einem Satz und lass die Quellenliste weg.

Nutzerfrage: {query}

Suchergebnisse:
{results}
"""

_SUMMARY_PROMPT_EN = """\
Answer the user's question based on the following web search results. Format:

1. A compact answer — **max 2 sentences**, only the core statement, no inline \
citations, no sources in the prose.
2. Then a blank line, followed by a source list as markdown bullet points, \
grouped and deduplicated, in this format:
   - [Page title](URL)

Only use URLs that appear verbatim in the results — never invent or combine any. \
If the results don't support a useful answer, say so honestly in one sentence and \
omit the source list.

User question: {query}

Search results:
{results}
"""


async def _summarize_search_results(query: str, raw: str, language: Language) -> str:
    """One-shot summarization of SearXNG results so the raw snippets never enter
    the main agent's message history. Runs in-process on the same model as the
    main agent, but through a separate ChatOpenAI instance without tools and
    with no history. Emits no SSE events — the existing `web_search_tool`
    ToolStreamTracker owns the UI status label for the whole duration.
    """
    template = _SUMMARY_PROMPT_EN if language == "en" else _SUMMARY_PROMPT_DE
    prompt = template.replace("{query}", query).replace("{results}", raw)
    try:
        response = await _utility_llm.ainvoke([HumanMessage(content=prompt)])
        summary = response.content.strip() if isinstance(response.content, str) else ""
        logger.info(
            "Summarized search: raw=%d bytes → summary=%d bytes",
            len(raw),
            len(summary),
        )
        return summary or raw
    except Exception:
        logger.exception("Search summarization failed, returning raw results")
        return raw


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
    lang = _language.get()
    full_text = ""
    lang_tag = f" [LANG:{lang}]"

    try:
        async for chunk in _stream_advisor(question + lang_tag, context_id=None):
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
            full_text = await _ask_advisor(question, context_id=None)
        # Partial content already streamed — return what we have to avoid duplicates

    # Fallback if streaming completed but yielded no text (e.g. only status events)
    if not full_text:
        logger.warning("Advisor streaming yielded no content, falling back to blocking call")
        full_text = await _ask_advisor(question, context_id=None)

    return full_text


@tool
async def ask_training_agent_tool(question: str) -> str:
    """Ask the Training Agent to manage a training job via A2A.

    Use this tool for training job operations: starting a training job,
    checking job status, listing jobs, or cancelling a job.

    Args:
        question: The training request to send to the Training Agent.
    """
    lang = _language.get()
    full_text = ""
    lang_tag = f" [LANG:{lang}]"

    # Belt-and-suspenders: if this is a training-start (all 4 slots filled and
    # workflow_intent=True), open the view up front so the user sees the panel
    # immediately — independent of whether the job_started envelope arrives.
    slots = _slots.get()
    if slots and slots.workflow_intent and slots.next_missing() is None:
        logger.info("All slots filled — pre-opening training view on tool entry")
        await adispatch_custom_event(
            TRAINING_VIEW_EVENT, {TRAINING_VIEW_KEY: {"action": "open"}}
        )

    try:
        async for chunk in _stream_training_agent(question + lang_tag, context_id=None):
            # Detect special event envelopes from the training agent
            try:
                parsed = json.loads(chunk)
                event_type = parsed.get(SOOFI_EVENT_KEY) if isinstance(parsed, dict) else None
            except (json.JSONDecodeError, ValueError):
                event_type = None

            if event_type == SOOFI_EVENT_JOB_STARTED:
                job_id = parsed.get("job_id", "")
                logger.info("Training job started (id=%s) — auto-opening training view", job_id)
                await adispatch_custom_event(
                    TRAINING_EVENT, {TRAINING_AGENT_KEY_JOB_STARTED: job_id}
                )
                # Auto-open the training view on successful job start — deterministic
                # so it does not depend on the LLM emitting a parallel tool call.
                await adispatch_custom_event(
                    TRAINING_VIEW_EVENT, {TRAINING_VIEW_KEY: {"action": "open"}}
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
            full_text = await _ask_training_agent(question, context_id=None)

    if not full_text:
        logger.warning("Training agent streaming yielded no content, falling back to blocking call")
        full_text = await _ask_training_agent(question, context_id=None)

    return full_text


@tool
async def ask_dataset_agent_tool(question: str) -> str:
    """Ask the Dataset Agent to search for suitable public datasets via A2A.

    Use this tool for dataset discovery requests, especially searches on
    HuggingFace and Eclipse Dataspace (EDC).

    Args:
        question: The dataset search request to send to the Dataset Agent.
    """
    lang = _language.get()
    full_text = ""
    lang_tag = f" [LANG:{lang}]"

    try:
        async for chunk in _stream_dataset_agent(question + lang_tag, context_id=None):
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
            full_text = await _ask_dataset_agent(question, context_id=None)

    if not full_text:
        logger.warning("Dataset agent streaming yielded no content, falling back to blocking call")
        full_text = await _ask_dataset_agent(question, context_id=None)

    return full_text


@tool
async def web_search_tool(query: str) -> str:
    """Search the public web for explicit lookup requests or current public information.

    Use this tool when the user explicitly asks to search or browse the web, or asks for
    current/latest/recent public-web information outside the dataset and training flows.

    Keep queries short and natural — plain keywords work best. Avoid quoted phrases,
    OR-operators, or site:-filters: SearXNG aggregates several engines, most of which
    handle these operators poorly, which collapses recall to near-zero.

    Args:
        query: Short, plain-keyword query (e.g. "Wetter Hannover", "Bars Hannover").
    """
    lang = _language.get()
    try:
        raw = await _web_search_searxng(query, lang)
        if raw == tr("web_search_no_results", lang):
            return raw
        return await _summarize_search_results(query, raw, lang)
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


def _format_slot_hint(slots: SlotState, lang: Language) -> str:
    """Compact snapshot of slot state injected into the system prompt."""

    def mark(value: str | None) -> str:
        return value if value else "—"

    if lang == "en":
        return (
            "## Current slots (derived from history)\n"
            f"- use_case: {mark(slots.use_case)}\n"
            f"- dataset: {mark(slots.dataset)}\n"
            f"- base_model: {mark(slots.base_model)}\n"
            f"- method: {mark(slots.method)}\n"
            f"- workflow_intent: {slots.workflow_intent}"
        )
    return (
        "## Aktueller Slot-Status (aus dem Verlauf)\n"
        f"- Anwendungsfall: {mark(slots.use_case)}\n"
        f"- Datensatz: {mark(slots.dataset)}\n"
        f"- Basismodell: {mark(slots.base_model)}\n"
        f"- Methode: {mark(slots.method)}\n"
        f"- Workflow-Intent: {slots.workflow_intent}"
    )


# Streaming sub-agents whose response is passed through directly — no second
# LLM call follows. Transition text (if any) is emitted by transition_node
# from a template, not generated by the LLM.
_STREAMING_TOOLS: set[str] = {
    "ask_advisor_tool",
    "ask_training_agent_tool",
    "ask_dataset_agent_tool",
}
# Streaming tools that should be followed by a template transition question.
# Training agent handles its own follow-ups, so it's excluded.
_TRANSITION_TOOLS: set[str] = {"ask_advisor_tool", "ask_dataset_agent_tool"}

# Narration triggers — phrases that announce or claim an action (search/ask/
# check/start) but belong in a tool call, not user-facing text. If the agent
# emits any of these WITHOUT a tool call, we retry once with forced tool_choice.
_NARRATION_TRIGGERS: tuple[str, ...] = (
    # German — announcing
    "ich suche", "ich frage", "ich prüfe", "ich schaue", "ich recherchiere",
    "ich werde suchen", "ich werde fragen", "ich werde prüfen",
    "lass mich", "lassen sie mich",
    "hier sind die ergebnisse", "hier ist meine suche",
    "die suche hat ergeben", "die suche ergab",
    "ich habe folgende", "ich habe die folgende",
    "dataset agent", "advisor", "training agent",
    # German — claiming completed action (training/job)
    "wurde erfolgreich gestartet", "wurde gestartet", "ist gestartet",
    "trainingsjob wurde", "training wurde", "job wurde erstellt",
    "habe den job gestartet", "habe das training gestartet",
    # English — announcing
    "i'll search", "i will search", "i'm searching",
    "i'll ask", "i will ask", "i'm asking",
    "i'll check", "i will check", "i'm checking",
    "let me search", "let me ask", "let me check",
    "here are the results", "the search yielded", "the search returned",
    "i found the following", "i have found",
    # English — claiming completed action
    "has been started", "has been successfully started", "job has been created",
    "training has started", "i've started the training", "i have started the",
)


def _contains_narration_triggers(text: str) -> bool:
    if not text:
        return False
    lowered = text.lower()
    return any(trigger in lowered for trigger in _NARRATION_TRIGGERS)


_RETRY_HINT_DE = (
    "Dein letzter Output war Narration ohne Tool-Call. "
    "Rufe JETZT SOFORT das passende Tool auf — ohne weiteren Text, "
    "ohne Plan-Ansage, ohne Erklärung."
)
_RETRY_HINT_EN = (
    "Your last output narrated an action without calling the tool. "
    "Call the correct tool RIGHT NOW — no more text, no plan, no explanation."
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
        **_build_vllm_kwargs("INTERACTION"),
    )
    llm_with_tools = llm.bind_tools(
        tools, **({"parallel_tool_calls": False} if not base_url else {})
    )
    slot_extractor = llm.with_structured_output(SlotState)
    tool_node = ToolNode(tools)

    async def extract_slots(state: SoofiState) -> dict[str, Any]:
        """Derive slot state from the full conversation history."""
        lang = _language.get()
        system = SystemMessage(content=get_slot_extraction_prompt(lang))
        try:
            slots = await slot_extractor.ainvoke([system] + list(state["messages"]))
        except Exception:
            logger.exception("Slot extraction failed — defaulting to empty slots")
            slots = SlotState()
        logger.info(
            "Slots: use_case=%s dataset=%s base_model=%s method=%s intent=%s",
            slots.use_case, slots.dataset, slots.base_model, slots.method,
            slots.workflow_intent,
        )
        return {"slots": slots}

    async def agent(state: SoofiState) -> dict[str, Any]:
        lang = _language.get()
        slots = state.get("slots") or SlotState()
        system_content = get_system_prompt(lang) + "\n\n" + _format_slot_hint(slots, lang)
        system = SystemMessage(content=system_content)
        messages = [system] + list(state["messages"])
        response = await llm_with_tools.ainvoke(messages)

        # Safety net: detect narration-without-tool-call and force a retry.
        # Triggered when the agent claims or announces an action but made no
        # tool call. Fires regardless of slot state — covers both "search now"
        # (slot missing) and "training started" (all slots filled) hallucinations.
        has_tool_call = bool(getattr(response, "tool_calls", None))
        if (
            not has_tool_call
            and slots.workflow_intent
            and _contains_narration_triggers(str(getattr(response, "content", "")))
        ):
            logger.warning(
                "Agent narrated without tool call — retrying with tool_choice=required"
            )
            hint = _RETRY_HINT_EN if lang == "en" else _RETRY_HINT_DE
            try:
                forced = llm.bind_tools(
                    tools,
                    tool_choice="required",
                    **({"parallel_tool_calls": False} if not base_url else {}),
                )
                response = await forced.ainvoke(messages + [SystemMessage(content=hint)])
            except Exception:
                logger.exception("Forced-tool retry failed — keeping original response")

        if getattr(response, "tool_calls", None):
            for tc in response.tool_calls:
                logger.info("Tool call: %s(%s)", tc["name"], tc["args"])
        return {"messages": [response]}

    async def run_tools(state: SoofiState) -> dict[str, Any]:
        token = _slots.set(state.get("slots") or SlotState())
        try:
            result = await tool_node.ainvoke(state)
        finally:
            _slots.reset(token)
        for msg in result["messages"]:
            logger.info("Tool result (%s): %s", msg.name, str(msg.content)[:500])
        return result

    async def transition(state: SoofiState) -> dict[str, Any]:
        """Append a deterministic transition question based on slot state."""
        slots = state.get("slots") or SlotState()
        if not slots.workflow_intent:
            return {}
        lang = _language.get()
        next_slot = slots.next_missing() or "ready"
        text = _TRANSITIONS[lang].get(next_slot)
        if not text:
            return {}
        await adispatch_custom_event(TRANSITION_EVENT, {TRANSITION_KEY: "\n\n" + text})
        return {}

    def should_continue(state: SoofiState) -> str:
        if not state["messages"]:
            return "__end__"
        last = state["messages"][-1]
        if hasattr(last, "tool_calls") and last.tool_calls:
            return "tools"
        return "__end__"

    def after_tools(state: SoofiState) -> str:
        """Route by last tool kind: transition for advisor/dataset, end for training,
        second agent call for UI tools (so it can confirm the action)."""
        for msg in reversed(state["messages"]):
            if hasattr(msg, "tool_calls"):
                break
            name = getattr(msg, "name", None)
            if name in _TRANSITION_TOOLS:
                return "transition"
            if name in _STREAMING_TOOLS:
                return "__end__"
        return "agent"

    graph_builder = StateGraph(SoofiState)
    graph_builder.add_node("extract_slots", extract_slots)
    graph_builder.add_node("agent", agent)
    graph_builder.add_node("tools", run_tools)
    graph_builder.add_node("transition", transition)
    graph_builder.set_entry_point("extract_slots")
    graph_builder.add_edge("extract_slots", "agent")
    graph_builder.add_conditional_edges(
        "agent", should_continue, {"tools": "tools", "__end__": "__end__"}
    )
    graph_builder.add_conditional_edges(
        "tools",
        after_tools,
        {"agent": "agent", "transition": "transition", "__end__": "__end__"},
    )
    graph_builder.add_edge("transition", "__end__")

    return graph_builder.compile()


def set_advisor_context_id(context_id: str | None) -> None:
    """Set the advisor context_id for the current request (used for RAG URL store keying)."""
    _advisor_context_id.set(context_id)


def set_language(lang: Language) -> None:
    """Set the language for the current request."""
    _language.set(lang)
