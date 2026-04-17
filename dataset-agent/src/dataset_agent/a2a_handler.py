"""A2A AgentExecutor that delegates to the LangGraph dataset agent graph."""

import json
import logging
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

_SOOFI_EVENT_KEY = "__soofi_event"
_EVENT_SEARCH_STATUS = "search_status"
_RE_LANG_TAG = re.compile(r"\[LANG:(de|en)\]\s*$")

# HuggingFace listings must be single-line per entry (see system_de.md §8).
# The LLM regularly ignores this and adds indented sub-bullets ("   - **Beschreibung:**",
# "   - **Tags:**" etc.). This filter strips them in-flight. Top-level bullets
# (no indent) stay intact — those are used by EDC listings and HF detail view.
_RE_FORBIDDEN_HF_SUBBULLET = re.compile(
    r"^\s{2,}[-*]\s+\*\*(?:"
    r"Beschreibung|Tags|Autor|Lizenz|License|"
    r"Erstellungsdatum|Aktualisiert|Datum|"
    r"Trending[- ]?Score|"
    r"Task[-_\s]*Kategorien?|Task[-_\s]*Categories|"
    r"Größe|Groesse|Size|Size[-_\s]*Categor\w*|"
    r"Sprache|Language|"
    r"Format|Modalit\w*|"
    r"Downloads|Likes"
    r")\b",
    re.IGNORECASE,
)


class _HfSubBulletFilter:
    """Line-buffered filter that drops forbidden HuggingFace sub-bullet metadata
    lines from the streamed dataset-agent response. Buffers until newline so a
    forbidden line is never partially emitted."""

    def __init__(self) -> None:
        self._buf = ""

    def feed(self, chunk: str) -> str:
        if not chunk:
            return ""
        self._buf += chunk
        out: list[str] = []
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            if not _RE_FORBIDDEN_HF_SUBBULLET.match(line):
                out.append(line + "\n")
        return "".join(out)

    def flush(self) -> str:
        remaining = self._buf
        self._buf = ""
        if remaining and _RE_FORBIDDEN_HF_SUBBULLET.match(remaining):
            return ""
        return remaining


class DatasetAgentExecutor(AgentExecutor):
    """Wraps the LangGraph dataset graph as an A2A AgentExecutor."""

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
                            "Dataset agent graph not initialized yet.",
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

        lang: Language = "de"
        lang_match = _RE_LANG_TAG.search(raw_text)
        if lang_match:
            lang = lang_match.group(1)  # type: ignore[assignment]
            raw_text = raw_text[: lang_match.start()].rstrip()

        user_text = raw_text
        thread_id = context.context_id or context.task_id
        logger.info("A2A request (thread=%s, lang=%s): %s", thread_id, lang, user_text[:200])

        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                task_id=context.task_id,
                context_id=context.context_id,
                status=TaskStatus(state=TaskState.working),
                final=False,
            )
        )

        system_prompt = SYSTEM_PROMPT_EN if lang == "en" else SYSTEM_PROMPT_DE
        config = {"configurable": {"thread_id": thread_id, "system_prompt": system_prompt}}
        collected: list[str] = []
        subbullet_filter = _HfSubBulletFilter()

        try:
            async for event in graph.astream_events(
                {"messages": [HumanMessage(content=user_text)]},
                version="v2",
                config=config,
            ):
                if event["event"] == "on_tool_start":
                    tool_name = event.get("name", "")
                    status_json = json.dumps(
                        {
                            _SOOFI_EVENT_KEY: _EVENT_SEARCH_STATUS,
                            "text": tr("searching_datasets", lang),
                            "tool": tool_name,
                        },
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

                elif event["event"] == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    if isinstance(chunk, AIMessageChunk) and chunk.content:
                        raw = (
                            chunk.content
                            if isinstance(chunk.content, str)
                            else str(chunk.content)
                        )
                        filtered = subbullet_filter.feed(raw)
                        if filtered:
                            collected.append(filtered)
                            await event_queue.enqueue_event(
                                TaskStatusUpdateEvent(
                                    task_id=context.task_id,
                                    context_id=context.context_id,
                                    status=TaskStatus(
                                        state=TaskState.working,
                                        message=new_agent_text_message(
                                            filtered,
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

        tail = subbullet_filter.flush()
        if tail:
            collected.append(tail)
            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    task_id=context.task_id,
                    context_id=context.context_id,
                    status=TaskStatus(
                        state=TaskState.working,
                        message=new_agent_text_message(
                            tail,
                            context.context_id,
                            context.task_id,
                        ),
                    ),
                    final=False,
                )
            )

        response_text = "".join(collected) or tr("no_response", lang)
        logger.info("A2A response: %s", response_text[:200])

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
