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
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage
from langgraph.graph.state import CompiledStateGraph

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
    tools = await mcp_client.get_tools()
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

agent_card = AgentCard(
    name="Soofi Advisor",
    description=(
        "LLM specialization advisor — analyzes use cases and recommends "
        "methods such as RAG, LoRA, or QLoRA (language: German)"
    ),
    url="http://advisor:8000/a2a/",
    version="0.1.0",
    capabilities=AgentCapabilities(streaming=True),
    skills=[
        AgentSkill(
            id="llm_specialization",
            name="LLM Specialization",
            description=(
                "Analyzes use cases and recommends "
                "LLM specialization methods"
            ),
            tags=["llm", "rag", "lora", "fine-tuning"],
        )
    ],
    default_input_modes=["text/plain"],
    default_output_modes=["text/plain"],
)

_a2a_handler = DefaultRequestHandler(
    agent_executor=AdvisorAgentExecutor(lambda: graph),
    task_store=InMemoryTaskStore(),
)
app.mount("/a2a", A2AFastAPIApplication(agent_card, _a2a_handler).build())


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
