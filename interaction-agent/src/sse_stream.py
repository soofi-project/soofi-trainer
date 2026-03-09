"""AG-UI SSE streaming state machine — generic over any number of tool-stream trackers."""

import asyncio
import copy
import json
import logging
import re
import uuid
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator

from langchain_core.messages import AIMessageChunk, ToolMessage
from langgraph.graph.state import CompiledStateGraph

from .constants import CONTROL_DOC_VIEWER_TOOL, DOC_VIEWER_KEY
from .speech import RE_SENTENCE_END, generate_speech_text

logger = logging.getLogger(__name__)

STREAM_DELAY = 0.02  # seconds between direct-LLM text chunks

# Strip domains the LLM may prepend to /docs/ URLs (e.g. https://www.dfki.de/docs/...)
_RE_DOCS_URL = re.compile(r"https?://[^/\s)]+(/docs/)")
# Hold back partial markdown links at end of buffer so the UI never shows
# broken fragments like "[lor", "[lora](https://www.dfki" while streaming.
# Buffers from "[" until the closing ")" of the link URL.
# Matches: [text  |  [text]  |  [text](  |  [text](url  |  https://partial
_RE_PARTIAL = re.compile(r"\[[^\]]*(?:\](?:\([^)]*)?)?$|https?://[^\s)]*$")


def _sse(event: dict[str, Any]) -> str:
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


def _compute_tail(full_output: str, streamed: str) -> str:
    """Return the tail of full_output that wasn't streamed, or '' if no safe tail."""
    if not full_output or len(full_output) <= len(streamed):
        return ""
    if full_output.startswith(streamed):
        return full_output[len(streamed) :]
    # The streamed text has URL-cleaned /docs/ links (domains stripped), so the raw
    # full_output won't match as a prefix.  Apply the same cleaning before comparing.
    cleaned_output = _RE_DOCS_URL.sub(r"\1", full_output)
    if cleaned_output.startswith(streamed):
        return cleaned_output[len(streamed) :]
    logger.warning(
        "Tail compensation prefix mismatch: streamed %d chars, full output %d chars "
        "(cleaned %d chars)",
        len(streamed),
        len(full_output),
        len(cleaned_output),
    )
    return ""


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


# ---------------------------------------------------------------------------
# Per-tool state tracker
# ---------------------------------------------------------------------------


@dataclass
class ToolStreamTracker:
    """Per-tool streaming state machine: IDLE -> SEARCHING -> STREAMING -> DONE."""

    tool_name: str  # e.g. "ask_advisor_tool"
    chunk_key: str  # custom-event key for text chunks
    status_keys: list[str] = field(default_factory=list)  # custom-event keys for status labels
    capture_keys: dict[str, str] = field(default_factory=dict)  # event_key -> snapshot field name
    component_name: str = ""  # if set, emit STATE_SNAPSHOT with captured values post-stream
    on_start_label: str = ""  # SEARCH_STATUS label emitted on tool start
    on_start_delay: float = 0.0  # delay (seconds) before emitting the start label

    # Mutable per invocation — reset before each stream
    searching: bool = field(default=False, init=False)
    streamed: bool = field(default=False, init=False)
    tool_output: str = field(default="", init=False)
    captured: dict[str, Any] = field(default_factory=dict, init=False)

    def reset(self) -> None:
        self.searching = False
        self.streamed = False
        self.tool_output = ""
        self.captured = {}


# ---------------------------------------------------------------------------
# SSE stream class
# ---------------------------------------------------------------------------


class SSEStream:
    """Runs a LangGraph agent and yields AG-UI SSE events."""

    def __init__(
        self,
        graph: CompiledStateGraph,
        trackers: list[ToolStreamTracker],
    ) -> None:
        self._graph = graph
        # Deep-copy so concurrent requests don't share mutable tracker state
        self._trackers = {t.tool_name: copy.deepcopy(t) for t in trackers}
        self._msg_id = ""
        self._response_text = ""
        self._chunk_buffer = ""
        self._speech_emitted = False
        self._result_messages: list[Any] = []

    # -- public entry point --------------------------------------------------

    async def stream(
        self,
        messages: list[Any],
    ) -> AsyncGenerator[str, None]:
        thread_id = str(uuid.uuid4())
        run_id = str(uuid.uuid4())
        self._msg_id = str(uuid.uuid4())
        self._response_text = ""
        self._chunk_buffer = ""
        self._speech_emitted = False
        self._result_messages = []

        for t in self._trackers.values():
            t.reset()

        yield _sse({"type": "RUN_STARTED", "threadId": thread_id, "runId": run_id})
        yield _sse({"type": "TEXT_MESSAGE_START", "messageId": self._msg_id, "role": "assistant"})

        try:
            async for event in self._graph.astream_events(
                {"messages": messages}, version="v2"
            ):
                kind = event["event"]
                if kind == "on_tool_start":
                    async for sse in self._handle_tool_start(event):
                        yield sse
                elif kind == "on_custom_event":
                    async for sse in self._handle_custom_event(event):
                        yield sse
                elif kind == "on_tool_end":
                    async for sse in self._handle_tool_end(event):
                        yield sse
                elif kind == "on_chat_model_stream":
                    async for sse in self._handle_chat_stream(event):
                        yield sse
                elif kind == "on_chain_end":
                    output = event.get("data", {}).get("output", {})
                    if isinstance(output, dict) and "messages" in output:
                        self._result_messages = output["messages"]
        except Exception:
            logger.exception("Error during agent execution")
            yield _sse(
                {
                    "type": "TEXT_MESSAGE_CONTENT",
                    "messageId": self._msg_id,
                    "delta": "\n\n[Fehler bei der Verarbeitung]",
                }
            )

        # Flush any buffered partial URL
        for sse in self._flush_buffer():
            yield sse

        # Tail compensation for all trackers
        for sse in self._emit_tails():
            yield sse

        yield _sse({"type": "TEXT_MESSAGE_END", "messageId": self._msg_id})

        # Fallback speech if no sentence boundary was hit during streaming
        if self._response_text and not self._speech_emitted:
            speech = generate_speech_text(
                self._response_text, has_search_results=self._has_search_results()
            )
            if speech:
                yield _sse({"type": "SPEECH_TEXT", "text": speech})

        # A2UI surface data
        surface = _extract_a2ui_from_tool_results(self._result_messages)
        if surface is not None:
            yield _sse({"type": "STATE_SNAPSHOT", "snapshot": {"a2ui": surface}})

        # Custom component triggers from captured values
        for tracker in self._trackers.values():
            if tracker.component_name and tracker.captured:
                yield _sse(
                    {
                        "type": "STATE_SNAPSHOT",
                        "snapshot": {
                            "custom_component": tracker.component_name,
                            **tracker.captured,
                        },
                    }
                )

        yield _sse({"type": "RUN_FINISHED", "threadId": thread_id, "runId": run_id})

    # -- event handlers ------------------------------------------------------

    async def _handle_tool_start(self, event: dict[str, Any]) -> AsyncGenerator[str, None]:
        tool_name = event.get("name")
        tracker = self._trackers.get(tool_name) if tool_name else None
        if tracker and not tracker.searching:
            tracker.searching = True
            tracker.streamed = False
            yield _sse({"type": "TOOL_CALL_START", "tool": tracker.tool_name})
            if tracker.on_start_delay > 0:
                await asyncio.sleep(tracker.on_start_delay)
            if tracker.on_start_label:
                yield _sse({"type": "SEARCH_STATUS", "label": tracker.on_start_label})

    async def _handle_custom_event(self, event: dict[str, Any]) -> AsyncGenerator[str, None]:
        data = event.get("data", {})

        for tracker in self._trackers.values():
            # Status keys
            for status_key in tracker.status_keys:
                status = data.get(status_key)
                if status:
                    yield _sse({"type": "SEARCH_STATUS", "label": status})

            # Capture keys (e.g. job_started_id)
            for event_key, attr_name in tracker.capture_keys.items():
                value = data.get(event_key)
                if value:
                    tracker.captured[attr_name] = value

            # Chunk key — the main text stream
            chunk = data.get(tracker.chunk_key)
            if chunk:
                async for sse in self._accept_chunk(tracker, chunk):
                    yield sse

    async def _accept_chunk(
        self, tracker: ToolStreamTracker, chunk: str
    ) -> AsyncGenerator[str, None]:
        """Handle an incoming text chunk from a tool stream."""
        if not tracker.streamed:
            tracker.streamed = True
            tracker.searching = False
            yield _sse({"type": "TOOL_CALL_END", "tool": tracker.tool_name})
        async for sse in self._emit_text(chunk):
            yield sse

    async def _handle_tool_end(self, event: dict[str, Any]) -> AsyncGenerator[str, None]:
        tool_name = event.get("name")

        # Doc viewer commands are returned as JSON from the tool
        if tool_name == CONTROL_DOC_VIEWER_TOOL:
            raw = event.get("data", {}).get("output", "")
            content = raw.content if hasattr(raw, "content") else raw
            try:
                data = json.loads(content) if isinstance(content, str) else {}
                doc_cmd = data.get(DOC_VIEWER_KEY)
                if doc_cmd:
                    logger.info("Emitting DOC_VIEWER event: %s", doc_cmd)
                    yield _sse({"type": "DOC_VIEWER", **doc_cmd})
            except (json.JSONDecodeError, TypeError):
                pass
            return

        tracker = self._trackers.get(tool_name) if tool_name else None
        if not tracker:
            return
        # Capture full tool output for tail compensation
        raw = event.get("data", {}).get("output", "")
        if isinstance(raw, str):
            tracker.tool_output = raw
        elif hasattr(raw, "content"):
            tracker.tool_output = raw.content if isinstance(raw.content, str) else ""
        logger.info("on_tool_end %s output: %d chars", tracker.tool_name, len(tracker.tool_output))
        # Fallback: if streaming yielded nothing, emit TOOL_CALL_END here
        if tracker.searching:
            tracker.searching = False
            yield _sse({"type": "TOOL_CALL_END", "tool": tracker.tool_name})

    async def _handle_chat_stream(self, event: dict[str, Any]) -> AsyncGenerator[str, None]:
        chunk = event["data"]["chunk"]
        if not (
            isinstance(chunk, AIMessageChunk)
            and chunk.content
            and not chunk.tool_calls
            and not chunk.tool_call_chunks
        ):
            return
        # Suppress direct-LLM output if any tracker already streamed
        if any(t.streamed for t in self._trackers.values()):
            return
        async for sse in self._emit_text(chunk.content):
            yield sse
        await asyncio.sleep(STREAM_DELAY)

    # -- URL-safe text emission -----------------------------------------------

    async def _emit_text(self, chunk: str) -> AsyncGenerator[str, None]:
        """Buffer-aware text emission that fixes /docs/ URLs across chunk boundaries."""
        self._chunk_buffer += chunk
        # Apply the URL fix on the combined buffer
        cleaned = _RE_DOCS_URL.sub(r"\1", self._chunk_buffer)
        # Check if the buffer ends with a partial link/URL that might continue
        m = _RE_PARTIAL.search(cleaned)
        if m:
            # Hold back the partial URL, emit everything before it
            emit = cleaned[: m.start()]
            self._chunk_buffer = cleaned[m.start() :]
        else:
            emit = cleaned
            self._chunk_buffer = ""
        if emit:
            self._response_text += emit
            yield _sse(
                {
                    "type": "TEXT_MESSAGE_CONTENT",
                    "messageId": self._msg_id,
                    "delta": emit,
                }
            )
            for sse in self._maybe_emit_speech():
                yield sse

    def _flush_buffer(self) -> list[str]:
        """Flush any remaining buffered text (e.g. at end of stream)."""
        if not self._chunk_buffer:
            return []
        # Buffer already contains URL-cleaned text from _emit_text
        remaining = self._chunk_buffer
        self._chunk_buffer = ""
        self._response_text += remaining
        return [
            _sse(
                {
                    "type": "TEXT_MESSAGE_CONTENT",
                    "messageId": self._msg_id,
                    "delta": remaining,
                }
            )
        ]

    # -- helpers -------------------------------------------------------------

    def _has_search_results(self) -> bool:
        return any(t.streamed for t in self._trackers.values())

    def _maybe_emit_speech(self) -> list[str]:
        if self._speech_emitted:
            return []
        if not RE_SENTENCE_END.search(self._response_text):
            return []
        speech = generate_speech_text(
            self._response_text, has_search_results=self._has_search_results()
        )
        if not speech:
            return []
        self._speech_emitted = True
        return [_sse({"type": "SPEECH_TEXT", "text": speech})]

    def _emit_tails(self) -> list[str]:
        result: list[str] = []
        for tracker in self._trackers.values():
            tail = _compute_tail(tracker.tool_output, self._response_text)
            if tail:
                logger.info(
                    "Emitting %d missed %s tail chars from on_tool_end",
                    len(tail),
                    tracker.tool_name,
                )
                self._response_text += tail
                result.append(
                    _sse(
                        {
                            "type": "TEXT_MESSAGE_CONTENT",
                            "messageId": self._msg_id,
                            "delta": tail,
                        }
                    )
                )
        return result
