"""FastAPI server exposing an OpenAI-compatible chat completions API and A2A protocol."""

import json
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from a2a.server.apps import A2AFastAPIApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage
from langgraph.graph.state import CompiledStateGraph

from langchain_mcp_adapters.tools import load_mcp_tools

from .a2a_handler import AdvisorAgentExecutor
from .graph import build_graph
from .tools import mcp_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL_NAME = os.getenv("ADVISOR_NAME")
if not MODEL_NAME:
    raise RuntimeError("ADVISOR_NAME env var required.")

# Initialized at startup
graph: CompiledStateGraph | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load MCP tools and build the graph on startup."""
    global graph
    async with mcp_client.session("knowledge") as session:
        tools = await load_mcp_tools(session)
        logger.info(f"Loaded {len(tools)} MCP tools: {[t.name for t in tools]}")
        graph = build_graph(tools)
        yield


app = FastAPI(title="Soofi Advisor", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# A2A server (mounted as sub-app; graph is resolved lazily at request time)
# ---------------------------------------------------------------------------

_ADVISOR_I18N = {
    "description": {
        "de": (
            "Fachberater für LLM-Spezialisierung — analysiert Anwendungsfälle "
            "und empfiehlt Methoden wie RAG, LoRA oder QLoRA"
        ),
        "en": (
            "Domain expert for LLM specialization — analyzes use cases "
            "and recommends methods like RAG, LoRA, or QLoRA"
        ),
    },
    "skill_name": {"de": "LLM-Spezialisierung", "en": "LLM Specialization"},
    "skill_desc": {
        "de": "Analysiert Anwendungsfälle und empfiehlt Spezialisierungsmethoden",
        "en": "Analyzes use cases and recommends specialization methods",
    },
}


def _build_agent_card(lang: str = "de") -> AgentCard:
    t = _ADVISOR_I18N
    lc = "en" if lang == "en" else "de"
    return AgentCard(
        name="Soofi Advisor",
        description=t["description"][lc],
        url="http://advisor:8000/a2a/",
        version="0.1.0",
        capabilities=AgentCapabilities(streaming=True),
        skills=[
            AgentSkill(
                id="llm_specialization",
                name=t["skill_name"][lc],
                description=t["skill_desc"][lc],
                tags=["llm", "rag", "lora", "fine-tuning"],
            )
        ],
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
    )


# Default DE card for A2A mount (protocol requires a static card)
agent_card = _build_agent_card("de")

_a2a_handler = DefaultRequestHandler(
    agent_executor=AdvisorAgentExecutor(lambda: graph),
    task_store=InMemoryTaskStore(),
)
# Register the i18n agent card route BEFORE mounting the A2A sub-app,
# so Starlette matches this specific path before the /a2a/ prefix mount.
@app.get("/a2a/.well-known/agent-card.json")
async def agent_card_i18n(lang: str = Query("de")) -> JSONResponse:
    card = _build_agent_card(lang)
    return JSONResponse(card.model_dump(by_alias=True, exclude_none=True))


_a2a_app = A2AFastAPIApplication(agent_card, _a2a_handler).build()
app.mount("/a2a", _a2a_app)


# ---------------------------------------------------------------------------
# OpenAI-compatible /v1/chat/completions (streaming)
# ---------------------------------------------------------------------------


async def _stream_completion(messages: list[dict]) -> AsyncGenerator[str, None]:
    """Stream LangGraph output as OpenAI-compatible SSE chunks."""
    completion_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
    created = int(time.time())

    # Convert OpenAI message format to LangChain messages
    lc_messages = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content") or ""
        if role == "user":
            lc_messages.append(HumanMessage(content=content))
        elif role == "assistant":
            lc_messages.append(AIMessage(content=content))

    # Stream the graph
    try:
        async for event in graph.astream_events(
            {"messages": lc_messages},
            version="v2",
        ):
            kind = event["event"]

            if kind == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                if isinstance(chunk, AIMessageChunk) and chunk.content:
                    delta = {"role": "assistant", "content": chunk.content}
                    data = {
                        "id": completion_id,
                        "object": "chat.completion.chunk",
                        "created": created,
                        "model": MODEL_NAME,
                        "choices": [{"index": 0, "delta": delta, "finish_reason": None}],
                    }
                    yield f"data: {json.dumps(data)}\n\n"
    except Exception:
        logger.exception("Error during graph streaming")
        delta = {"role": "assistant", "content": "\n\n[Fehler bei der Verarbeitung]"}
        data = {
            "id": completion_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": MODEL_NAME,
            "choices": [{"index": 0, "delta": delta, "finish_reason": "stop"}],
        }
        yield f"data: {json.dumps(data)}\n\n"
        yield "data: [DONE]\n\n"
        return

    # Final chunk with finish_reason
    data = {
        "id": completion_id,
        "object": "chat.completion.chunk",
        "created": created,
        "model": MODEL_NAME,
        "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
    }
    yield f"data: {json.dumps(data)}\n\n"
    yield "data: [DONE]\n\n"


@app.post("/v1/chat/completions")
async def chat_completions(request: Request) -> StreamingResponse:
    body = await request.json()
    messages = body.get("messages", [])

    return StreamingResponse(
        _stream_completion(messages),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# /v1/models — Model discovery for Open WebUI
# ---------------------------------------------------------------------------


@app.get("/v1/models")
async def list_models() -> dict:
    return {
        "object": "list",
        "data": [
            {
                "id": MODEL_NAME,
                "object": "model",
                "created": 0,
                "owned_by": "soofi",
            }
        ],
    }


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@app.get("/health")
async def health() -> dict:
    if graph is None:
        return {"status": "error", "detail": "Graph not initialized"}
    return {"status": "ok"}
