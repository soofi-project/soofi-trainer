"""A2A AgentExecutor that delegates to the LangGraph advisor graph."""

import json
import logging
import os
import re
from typing import Callable

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import Task, TaskState, TaskStatus, TaskStatusUpdateEvent
from a2a.utils.message import new_agent_text_message
from langchain_core.messages import AIMessageChunk, HumanMessage
from langgraph.graph.state import CompiledStateGraph

from .i18n import Language, tr
from .prompts import SYSTEM_PROMPT_DE, SYSTEM_PROMPT_EN

logger = logging.getLogger(__name__)

# Protocol constants for the soofi event envelope shared with interaction-agent/graph.py
_SOOFI_EVENT_KEY = "__soofi_event"
_EVENT_SEARCH_STATUS = "search_status"
_EVENT_RAG_SOURCES = "rag_sources"
_RE_LANG_TAG = re.compile(r"\[LANG:(de|en)\]\s*$")

_min_score_env = os.getenv("ADVISOR_MIN_SOURCE_SCORE")
if _min_score_env is None:
    raise RuntimeError("ADVISOR_MIN_SOURCE_SCORE env var required.")
_MIN_SOURCE_SCORE = float(_min_score_env)


class AdvisorAgentExecutor(AgentExecutor):
    """Wraps the LangGraph advisor graph as an A2A AgentExecutor.

    Accepts a callable that returns the graph, so the executor can be
    instantiated before the graph is built (during module-level setup).
    """

    def __init__(self, graph_provider: Callable[[], CompiledStateGraph | None]) -> None:
        self._graph_provider = graph_provider

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        graph = self._graph_provider()
        if graph is None:
            await event_queue.enqueue_event(
                Task(
                    id=context.task_id,
                    context_id=context.context_id,
                    status=TaskStatus(
                        state=TaskState.failed,
                        message=new_agent_text_message(
                            "Advisor graph not initialized yet.",
                            context.context_id,
                            context.task_id,
                        ),
                    ),
                )
            )
            return

        if not context.message or not context.message.parts:
            await event_queue.enqueue_event(
                Task(
                    id=context.task_id,
                    context_id=context.context_id,
                    status=TaskStatus(
                        state=TaskState.completed,
                        message=new_agent_text_message(
                            "No message received.",
                            context.context_id,
                            context.task_id,
                        ),
                    ),
                )
            )
            return

        raw_text = context.message.parts[0].root.text

        # Extract [LANG:xx] tag from the end of the message
        lang: Language = "de"
        lang_match = _RE_LANG_TAG.search(raw_text)
        if lang_match:
            lang = lang_match.group(1)  # type: ignore[assignment]
            raw_text = raw_text[: lang_match.start()].rstrip()

        user_text = raw_text
        thread_id = context.context_id or context.task_id
        logger.info("A2A request (thread=%s, lang=%s): %s", thread_id, lang, user_text[:200])

        # Signal that we're working
        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                task_id=context.task_id,
                context_id=context.context_id,
                status=TaskStatus(state=TaskState.working),
                final=False,
            )
        )

        # Run the LangGraph agent with thread_id for conversation memory.
        # Stream each LLM token as a TaskStatusUpdateEvent so the client
        # can display partial results in real time.
        system_prompt = SYSTEM_PROMPT_EN if lang == "en" else SYSTEM_PROMPT_DE
        config = {"configurable": {"thread_id": thread_id, "system_prompt": system_prompt}}
        collected: list[str] = []
        try:
            async for event in graph.astream_events(
                {"messages": [HumanMessage(content=user_text)]},
                version="v2",
                config=config,
            ):
                if event["event"] == "on_tool_start" and "search_documents" in event.get("name", ""):
                    status_json = json.dumps(
                        {_SOOFI_EVENT_KEY: _EVENT_SEARCH_STATUS, "text": tr("search_status", lang)},
                        ensure_ascii=False,
                    )
                    await event_queue.enqueue_event(
                        TaskStatusUpdateEvent(
                            task_id=context.task_id,
                            context_id=context.context_id,
                            status=TaskStatus(
                                state=TaskState.working,
                                message=new_agent_text_message(
                                    status_json, context.context_id, context.task_id
                                ),
                            ),
                            final=False,
                        )
                    )

                elif (
                    event["event"] == "on_tool_end"
                    and "search_documents" in event.get("name", "")
                ):
                    raw_output = event.get("data", {}).get("output", "")
                    # MCP tools return ToolMessage with .content as list of parts
                    if hasattr(raw_output, "content"):
                        raw_output = raw_output.content
                    if isinstance(raw_output, list):
                        text_parts = []
                        for p in raw_output:
                            if isinstance(p, dict) and p.get("type") == "text":
                                text_parts.append(p["text"])
                            elif hasattr(p, "text"):
                                text_parts.append(p.text)
                        raw_output = text_parts[0] if text_parts else ""
                    try:
                        tool_result = (
                            json.loads(raw_output)
                            if isinstance(raw_output, str)
                            else raw_output
                        )
                    except (json.JSONDecodeError, TypeError):
                        tool_result = None
                    if isinstance(tool_result, dict):
                        seen: dict[tuple[str, str], int] = {}
                        sources = []
                        for r in tool_result.get("results", []):
                            score = r.get("reranker_score")
                            if score is None or score < _MIN_SOURCE_SCORE:
                                continue
                            file = r.get("source_file", "")
                            section = r.get("section_title", "")
                            key = (file, section)
                            if key in seen:
                                # Keep the one with the higher score
                                prev_idx = seen[key]
                                if score > sources[prev_idx]["score"]:
                                    sources[prev_idx] = {
                                        "file": file,
                                        "section": section,
                                        "score": score,
                                        "url": r.get("metadata", {}).get("source", ""),
                                    }
                                continue
                            seen[key] = len(sources)
                            sources.append({
                                "file": file,
                                "section": section,
                                "score": score,
                                "url": r.get("metadata", {}).get("source", ""),
                            })
                        if sources:
                            sources_json = json.dumps(
                                {_SOOFI_EVENT_KEY: _EVENT_RAG_SOURCES, "sources": sources},
                                ensure_ascii=False,
                            )
                            await event_queue.enqueue_event(
                                TaskStatusUpdateEvent(
                                    task_id=context.task_id,
                                    context_id=context.context_id,
                                    status=TaskStatus(
                                        state=TaskState.working,
                                        message=new_agent_text_message(
                                            sources_json,
                                            context.context_id,
                                            context.task_id,
                                        ),
                                    ),
                                    final=False,
                                )
                            )

                elif event["event"] == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    if isinstance(chunk, AIMessageChunk) and chunk.content:
                        collected.append(chunk.content)
                        await event_queue.enqueue_event(
                            TaskStatusUpdateEvent(
                                task_id=context.task_id,
                                context_id=context.context_id,
                                status=TaskStatus(
                                    state=TaskState.working,
                                    message=new_agent_text_message(
                                        chunk.content,
                                        context.context_id,
                                        context.task_id,
                                    ),
                                ),
                                final=False,
                            )
                        )
        except Exception:
            logger.exception("Error during A2A graph execution")
            await event_queue.enqueue_event(
                Task(
                    id=context.task_id,
                    context_id=context.context_id,
                    status=TaskStatus(
                        state=TaskState.failed,
                        message=new_agent_text_message(
                            tr("processing_error", lang),
                            context.context_id,
                            context.task_id,
                        ),
                    ),
                )
            )
            return

        response_text = "".join(collected) or tr("no_response", lang)
        logger.info("A2A response: %s", response_text[:1000])

        await event_queue.enqueue_event(
            Task(
                id=context.task_id,
                context_id=context.context_id,
                status=TaskStatus(
                    state=TaskState.completed,
                    message=new_agent_text_message(
                        response_text,
                        context.context_id,
                        context.task_id,
                    ),
                ),
            )
        )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        await event_queue.enqueue_event(
            Task(
                id=context.task_id,
                context_id=context.context_id,
                status=TaskStatus(state=TaskState.canceled),
            )
        )
