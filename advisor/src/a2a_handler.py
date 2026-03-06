"""A2A AgentExecutor that delegates to the LangGraph advisor graph."""

import json
import logging
from typing import Callable

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import Task, TaskState, TaskStatus, TaskStatusUpdateEvent
from a2a.utils.message import new_agent_text_message
from langchain_core.messages import AIMessageChunk, HumanMessage
from langgraph.graph.state import CompiledStateGraph

logger = logging.getLogger(__name__)

# Protocol constants for the soofi event envelope shared with interaction-agent/graph.py
_SOOFI_EVENT_KEY = "__soofi_event"
_EVENT_SEARCH_STATUS = "search_status"


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

        user_text = context.message.parts[0].root.text
        thread_id = context.context_id or context.task_id
        logger.info("A2A request (thread=%s): %s", thread_id, user_text[:200])

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
        config = {"configurable": {"thread_id": thread_id}}
        collected: list[str] = []
        try:
            async for event in graph.astream_events(
                {"messages": [HumanMessage(content=user_text)]},
                version="v2",
                config=config,
            ):
                if event["event"] == "on_tool_start" and "search_documents" in event.get("name", ""):
                    status_json = json.dumps(
                        {_SOOFI_EVENT_KEY: _EVENT_SEARCH_STATUS, "text": "Suche in der Wissensdatenbank"},
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
                            "Internal error during processing.",
                            context.context_id,
                            context.task_id,
                        ),
                    ),
                )
            )
            return

        response_text = "".join(collected) or "No response generated."
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
