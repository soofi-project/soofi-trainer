"""AG-UI backend for the Soofi Interaction Agent (LangGraph + A2A)."""

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph.state import CompiledStateGraph

from .constants import (
    ADVISOR_KEY_CHUNK,
    ADVISOR_KEY_SEARCH_STATUS,
    TRAINING_AGENT_KEY_CHUNK,
    TRAINING_AGENT_KEY_JOB_STARTED,
    TRAINING_AGENT_KEY_STATUS,
)
from .graph import build_graph, set_advisor_context_id, set_language, set_training_context_id
from .i18n import Language
from .sse_stream import SSEStream, ToolStreamTracker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tracker configuration — one entry per delegated agent tool.
# Adding a new agent = adding a new ToolStreamTracker here.
# ---------------------------------------------------------------------------

TRACKERS = [
    ToolStreamTracker(
        tool_name="ask_advisor_tool",
        chunk_key=ADVISOR_KEY_CHUNK,
        status_keys=[ADVISOR_KEY_SEARCH_STATUS],
        on_start_label="search_kb",
        on_start_delay=0.6,
    ),
    ToolStreamTracker(
        tool_name="ask_training_agent_tool",
        chunk_key=TRAINING_AGENT_KEY_CHUNK,
        status_keys=[TRAINING_AGENT_KEY_STATUS],
        capture_keys={TRAINING_AGENT_KEY_JOB_STARTED: "job_id"},
        component_name="soofi-training-progress",
        on_start_label="processing_training",
    ),
    ToolStreamTracker(
        tool_name="show_agent_card",
        chunk_key="",
        on_start_label="loading_agent_card",
    ),
]

# Initialized at startup
graph: CompiledStateGraph | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    global graph

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    graph = build_graph()
    logger.info("Interaction Agent graph built successfully")
    yield


app = FastAPI(title="Soofi Interaction Agent", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _build_lc_messages(messages: list[dict[str, str]]) -> list[HumanMessage | AIMessage]:
    """Convert chat history dicts to LangChain message objects."""
    lc_messages: list[HumanMessage | AIMessage] = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content") or msg.get("text") or ""
        if role == "user":
            lc_messages.append(HumanMessage(content=content))
        elif role == "assistant":
            lc_messages.append(AIMessage(content=content))
    return lc_messages


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.post("/agent")
async def agent_endpoint(request: Request) -> StreamingResponse:
    assert graph is not None
    body = await request.json()

    messages: list[dict[str, str]] = []
    if "messages" in body and body["messages"]:
        for msg in body["messages"]:
            if isinstance(msg, dict):
                messages.append(msg)
            else:
                messages.append({"role": "user", "content": str(msg)})
    elif "message" in body:
        messages.append({"role": "user", "content": body["message"]})

    session_id = body.get("session_id")
    lang: Language = body.get("language", "de")
    if lang not in ("de", "en"):
        lang = "de"
    set_advisor_context_id(session_id)
    set_training_context_id(session_id)
    set_language(lang)

    lc_messages = _build_lc_messages(messages)
    sse = SSEStream(graph, TRACKERS, language=lang)

    return StreamingResponse(
        sse.stream(lc_messages),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/health")
async def health() -> dict[str, str]:
    if graph is None:
        return {"status": "error", "detail": "Graph not initialized"}
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# A2A Agent Card — compatible endpoint so the agent card viewer can discover
# this agent like any other A2A agent in the system.
# ---------------------------------------------------------------------------

_AGENT_CARD_I18N: dict[str, dict[Language, str]] = {
    "description": {
        "de": (
            "Zentraler Gesprächsagent — nimmt Nutzereingaben entgegen, "
            "koordiniert Advisor und Training Agent, steuert die UI"
        ),
        "en": (
            "Central conversation agent — receives user input, "
            "coordinates Advisor and Training Agent, controls the UI"
        ),
    },
    "skill_conversation_name": {"de": "Gesprächsführung", "en": "Conversation"},
    "skill_conversation_desc": {
        "de": "Führt den Nutzer durch den LLM-Spezialisierungsprozess",
        "en": "Guides the user through the LLM specialization process",
    },
    "skill_discovery_name": {"de": "Agentenerkennung", "en": "Agent Discovery"},
    "skill_discovery_desc": {
        "de": "Zeigt registrierte Agenten und deren Fähigkeiten an",
        "en": "Shows registered agents and their capabilities",
    },
}


def _build_agent_card(lang: Language) -> dict:
    t = _AGENT_CARD_I18N
    return {
        "name": "Soofi Interaction Agent",
        "description": t["description"][lang],
        "url": "http://interaction-agent:8000",
        "version": os.getenv("SOOFI_UI_INTERACTIONAGENT_VERSION", "0.1.0"),
        "capabilities": {"streaming": True},
        "skills": [
            {
                "id": "conversation",
                "name": t["skill_conversation_name"][lang],
                "description": t["skill_conversation_desc"][lang],
                "tags": ["dialog", "orchestration", "a2a"],
            },
            {
                "id": "agent_discovery",
                "name": t["skill_discovery_name"][lang],
                "description": t["skill_discovery_desc"][lang],
                "tags": ["a2a", "agent-card"],
            },
        ],
        "defaultInputModes": ["text/plain"],
        "defaultOutputModes": ["text/plain"],
    }


@app.get("/a2a/.well-known/agent-card.json")
async def agent_card(lang: str = "de") -> JSONResponse:
    card_lang: Language = "en" if lang == "en" else "de"
    return JSONResponse(_build_agent_card(card_lang))
