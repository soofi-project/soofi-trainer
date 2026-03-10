"""A2A AgentExecutor that delegates to the LangGraph training agent graph."""

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

# Protocol constants for the soofi event envelope shared with interaction-agent
_SOOFI_EVENT_KEY = "__soofi_event"
_EVENT_JOB_STARTED = "job_started"
_EVENT_SEARCH_STATUS = "search_status"
_RE_LANG_TAG = re.compile(r"\[LANG:(de|en)\]\s*$")

# Tool name that signals a training job was started
_START_TRAINING_TOOL = "start_training_job"

# MCP tool names — emit status event when these start
_MCP_TOOLS = {"start_training_job", "get_job_status", "list_training_jobs", "cancel_training_job"}


class TrainingAgentExecutor(AgentExecutor):
    """Wraps the LangGraph training agent graph as an A2A AgentExecutor.

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
                            "Training agent graph not initialized yet.",
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

        system_prompt = SYSTEM_PROMPT_EN if lang == "en" else SYSTEM_PROMPT_DE
        config = {"configurable": {"thread_id": thread_id, "system_prompt": system_prompt}}
        collected: list[str] = []

        try:
            async for event in graph.astream_events(
                {"messages": [HumanMessage(content=user_text)]},
                version="v2",
                config=config,
            ):
                if event["event"] == "on_tool_start" and event.get("name") in _MCP_TOOLS:
                    status_json = json.dumps(
                        {_SOOFI_EVENT_KEY: _EVENT_SEARCH_STATUS, "text": tr("calling_gateway", lang)},
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

                elif event["event"] == "on_tool_end":
                    # Emit job_started envelope when start_training_job completes successfully
                    if event.get("name") == _START_TRAINING_TOOL:
                        output = event.get("data", {}).get("output")
                        if output:
                            try:
                                result = json.loads(output) if isinstance(output, str) else output
                            except (json.JSONDecodeError, ValueError):
                                result = None

                            job_id = result.get("job_id") if isinstance(result, dict) else None
                            failed = result.get("status") == "failed" if isinstance(result, dict) else False

                            if job_id and not failed:
                                envelope = json.dumps(
                                    {_SOOFI_EVENT_KEY: _EVENT_JOB_STARTED, "job_id": job_id},
                                    ensure_ascii=False,
                                )
                                await event_queue.enqueue_event(
                                    TaskStatusUpdateEvent(
                                        task_id=context.task_id,
                                        context_id=context.context_id,
                                        status=TaskStatus(
                                            state=TaskState.working,
                                            message=new_agent_text_message(
                                                envelope, context.context_id, context.task_id
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
