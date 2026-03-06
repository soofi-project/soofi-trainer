"""AG-UI backend for the Soofi Interaction Agent (LangGraph + A2A)."""

import asyncio
import json
import logging
import os
import re
import uuid
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage, ToolMessage
from langgraph.graph.state import CompiledStateGraph
from .constants import ADVISOR_KEY_CHUNK, ADVISOR_KEY_SEARCH_STATUS
from .graph import build_graph, set_advisor_context_id

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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


# ---------------------------------------------------------------------------
# Speech text extraction — generates speakable prose for TTS from responses
# ---------------------------------------------------------------------------


_RE_MD_LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_RE_MD_FORMAT = re.compile(r"[*_`]+")
_RE_WHITESPACE = re.compile(r"\s+")
_SPEECH_MIN_CHARS = 15  # don't speak trivially short responses
_RE_SENTENCE_END = re.compile(r"(?<![A-Z0-9])[.!?]\s")  # sentence boundary for early TTS trigger
# Lines that start a structured markdown block — stop collecting intro before these
_RE_STRUCTURE_LINE = re.compile(r"^\s*(?:#{1,6}\s|[-*]\s|\d+\.\s)")
# Spoken when the response starts directly with structure (no intro prose)
_SPEECH_FALLBACK = "Ich habe folgendes gefunden."
_SPEECH_MAX_CHARS = 200  # upper limit to avoid reading very long intros


def _generate_speech_text(text: str) -> str:
    """Extract speakable intro prose from a Markdown response for TTS.

    - Collects lines up to the first structural element (header, bullet, list)
    - If the whole response is structural, returns a static fallback phrase
    - Reads all intro sentences; stops and converts a colon-ending sentence
      (which would introduce a list) to a period so it sounds natural
    """
    # Collect only the intro lines before any structural markdown
    intro_lines: list[str] = []
    for line in text.splitlines():
        if _RE_STRUCTURE_LINE.match(line):
            break
        intro_lines.append(line)

    intro = "\n".join(intro_lines).strip()

    # Whole response starts with structure — give a short spoken acknowledgement
    if not intro or len(intro) < _SPEECH_MIN_CHARS:
        return _SPEECH_FALLBACK

    # Strip inline markdown
    intro = _RE_MD_LINK.sub(r"\1", intro)
    intro = _RE_MD_FORMAT.sub("", intro)
    intro = _RE_WHITESPACE.sub(" ", intro).strip()

    # Collect sentences; rules:
    # - Only include sentences that end with proper punctuation (.!?) — trailing
    #   fragments without punctuation are incomplete (early-emission artifact)
    # - When a sentence ends with ":" it introduces a list: replace colon with
    #   "." and stop so list items are not read out
    sentences = re.split(r"(?<=[.!?])\s+", intro)
    result: list[str] = []
    for sentence in sentences:
        s = sentence.strip()
        if not s:
            continue
        if s.endswith(":"):
            result.append(s[:-1] + ".")
            break
        if not re.search(r"[.!?]$", s):
            break  # incomplete fragment — stop here
        result.append(s)
        if sum(len(x) for x in result) >= _SPEECH_MAX_CHARS:
            break

    return " ".join(result).strip()



# ---------------------------------------------------------------------------
# AG-UI SSE streaming
# ---------------------------------------------------------------------------

STREAM_DELAY = 0.02  # seconds between text chunks


def _sse(event: dict[str, Any]) -> str:
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


def _extract_a2ui_from_tool_results(messages: list[Any]) -> list[dict[str, Any]] | None:
    """Check tool messages for A2UI surface data."""
    for msg in reversed(messages):
        if not isinstance(msg, ToolMessage):
            continue
        try:
            data = json.loads(msg.content)
            if "a2ui" in data:
                return data["a2ui"]
        except (json.JSONDecodeError, TypeError):
            continue
    return None


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


async def _stream_ag_ui_events(
    messages: list[dict[str, str]],
    session_id: str | None = None,
) -> AsyncGenerator[str, None]:
    """Run the LangGraph agent and yield AG-UI SSE events."""
    assert graph is not None

    thread_id = str(uuid.uuid4())
    run_id = str(uuid.uuid4())
    msg_id = str(uuid.uuid4())

    set_advisor_context_id(session_id)
    lc_messages = _build_lc_messages(messages)

    yield _sse({"type": "RUN_STARTED", "threadId": thread_id, "runId": run_id})
    yield _sse({"type": "TEXT_MESSAGE_START", "messageId": msg_id, "role": "assistant"})

    result_messages: list[Any] = []
    advisor_searching = False
    advisor_streamed = False  # True once advisor chunks have been forwarded to browser
    response_text = ""  # Accumulated full response text for SPEECH_TEXT generation
    speech_emitted = False  # True once SPEECH_TEXT has been emitted for this response

    try:
        async for event in graph.astream_events(
            {"messages": lc_messages}, version="v2"
        ):
            kind = event["event"]

            if kind == "on_tool_start" and not advisor_searching:
                if event.get("name") == "ask_advisor_tool":
                    advisor_searching = True
                    advisor_streamed = False
                    yield _sse({"type": "TOOL_CALL_START", "tool": "ask_advisor_tool"})
                    # Advisor always calls search_documents — on_custom_event does not
                    # propagate write() calls from ToolNode, so emit SEARCH_STATUS directly.
                    # Brief pause so the A2A edge animation is visible before transitioning.
                    await asyncio.sleep(0.6)
                    yield _sse({"type": "SEARCH_STATUS", "label": "Suche in der Wissensdatenbank"})

            elif kind == "on_custom_event":
                # Stream-Delegation: advisor chunks and status events arrive here
                data = event.get("data", {})

                search_status = data.get(ADVISOR_KEY_SEARCH_STATUS)
                if search_status:
                    yield _sse({"type": "SEARCH_STATUS", "label": search_status})

                chunk = data.get(ADVISOR_KEY_CHUNK)
                if chunk:
                    response_text += chunk
                    if not advisor_streamed:
                        # First chunk — hide the searching indicator
                        advisor_streamed = True
                        advisor_searching = False
                        yield _sse({"type": "TOOL_CALL_END", "tool": "ask_advisor_tool"})
                    yield _sse(
                        {
                            "type": "TEXT_MESSAGE_CONTENT",
                            "messageId": msg_id,
                            "delta": chunk,
                        }
                    )
                    # Emit SPEECH_TEXT as soon as the first sentence is complete
                    if not speech_emitted and _RE_SENTENCE_END.search(response_text):
                        speech = _generate_speech_text(response_text)
                        if speech:
                            speech_emitted = True
                            yield _sse({"type": "SPEECH_TEXT", "text": speech})

            elif kind == "on_tool_end":
                # Fallback: if streaming yielded nothing, emit TOOL_CALL_END here
                if event.get("name") == "ask_advisor_tool" and advisor_searching:
                    advisor_searching = False
                    yield _sse({"type": "TOOL_CALL_END", "tool": "ask_advisor_tool"})

            elif kind == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                if (
                    isinstance(chunk, AIMessageChunk)
                    and chunk.content
                    and not chunk.tool_calls
                    and not chunk.tool_call_chunks
                    and not advisor_streamed  # suppress if advisor already streamed
                ):
                    response_text += chunk.content
                    yield _sse(
                        {
                            "type": "TEXT_MESSAGE_CONTENT",
                            "messageId": msg_id,
                            "delta": chunk.content,
                        }
                    )
                    await asyncio.sleep(STREAM_DELAY)
                    # Emit SPEECH_TEXT as soon as the first sentence is complete
                    if not speech_emitted and _RE_SENTENCE_END.search(response_text):
                        speech = _generate_speech_text(response_text)
                        if speech:
                            speech_emitted = True
                            yield _sse({"type": "SPEECH_TEXT", "text": speech})

            elif kind == "on_chain_end":
                output = event.get("data", {}).get("output", {})
                if isinstance(output, dict) and "messages" in output:
                    result_messages = output["messages"]

    except Exception:
        logger.exception("Error during agent execution")
        yield _sse(
            {
                "type": "TEXT_MESSAGE_CONTENT",
                "messageId": msg_id,
                "delta": "\n\n[Fehler bei der Verarbeitung]",
            }
        )

    yield _sse({"type": "TEXT_MESSAGE_END", "messageId": msg_id})

    # Fallback: emit SPEECH_TEXT after stream if no sentence boundary was hit during streaming
    if response_text and not speech_emitted:
        speech_text = _generate_speech_text(response_text)
        if speech_text:
            yield _sse({"type": "SPEECH_TEXT", "text": speech_text})

    surface = _extract_a2ui_from_tool_results(result_messages)
    if surface is not None:
        yield _sse({"type": "STATE_SNAPSHOT", "snapshot": {"a2ui": surface}})

    yield _sse({"type": "RUN_FINISHED", "threadId": thread_id, "runId": run_id})


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.post("/agent")
async def agent_endpoint(request: Request) -> StreamingResponse:
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

    return StreamingResponse(
        _stream_ag_ui_events(messages, session_id=session_id),
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
