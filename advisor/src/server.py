"""FastAPI server exposing an OpenAI-compatible chat completions API."""

import json
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage

from .graph import build_graph
from .tools import mcp_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL_NAME = os.environ["ADVISOR_NAME"]

# Initialized at startup
graph = None


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
            "choices": [{"index": 0, "delta": delta, "finish_reason": None}],
        }
        yield f"data: {json.dumps(data)}\n\n"

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
    return {"status": "ok"}
