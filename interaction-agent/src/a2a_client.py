"""A2A client wrapper for calling the Advisor and Training Agent."""

import asyncio
import logging
import os
import uuid
from typing import AsyncGenerator

import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    Message,
    MessageSendParams,
    Part,
    Role,
    SendMessageRequest,
    Task,
    TaskState,
    TaskStatusUpdateEvent,
    TextPart,
)

logger = logging.getLogger(__name__)

ADVISOR_A2A_URL = os.getenv("ADVISOR_A2A_URL", "http://advisor:8000")
TRAINING_AGENT_A2A_URL = os.getenv("TRAINING_AGENT_A2A_URL", "http://training-agent:8000")
DATASET_AGENT_A2A_URL = os.getenv("DATASET_AGENT_A2A_URL", "http://dataset-agent:8000")

# Advisor client — resolved once and reused across calls
_client: A2AClient | None = None
_httpx_client: httpx.AsyncClient | None = None
_init_lock = asyncio.Lock()

# Training agent client — lazy-init with own globals
_training_client: A2AClient | None = None
_training_httpx_client: httpx.AsyncClient | None = None
_training_init_lock = asyncio.Lock()

# Dataset agent client — lazy-init with own globals
_dataset_client: A2AClient | None = None
_dataset_httpx_client: httpx.AsyncClient | None = None
_dataset_init_lock = asyncio.Lock()


async def _get_client() -> A2AClient:
    """Return a reusable A2A client, resolving the agent card on first call."""
    global _client, _httpx_client

    if _client is not None:
        return _client

    async with _init_lock:
        if _client is not None:
            return _client

        base_url = f"{ADVISOR_A2A_URL}/a2a/"
        logger.info("Resolving advisor agent card at %s", base_url)

        _httpx_client = httpx.AsyncClient(timeout=120.0)
        resolver = A2ACardResolver(_httpx_client, base_url)
        agent_card = await resolver.get_agent_card()
        _client = A2AClient(httpx_client=_httpx_client, agent_card=agent_card)
        return _client


def _build_request(question: str, context_id: str | None) -> SendMessageRequest:
    return SendMessageRequest(
        id=str(uuid.uuid4()),
        params=MessageSendParams(
            message=Message(
                role=Role.user,
                message_id=str(uuid.uuid4()),
                context_id=context_id,
                parts=[Part(root=TextPart(text=question))],
            ),
        ),
    )


async def stream_advisor(
    question: str, context_id: str | None = None
) -> AsyncGenerator[str, None]:
    """Stream tokens from the Advisor via A2A streaming.

    Yields text chunks as they arrive from the Advisor's LangGraph stream.
    Returns an empty generator if the initial connection fails.
    Raises on mid-stream errors so the caller can distinguish between
    no content (fallback possible) and truncated content (fallback would duplicate).
    """
    try:
        client = await _get_client()
    except Exception:
        logger.exception("Failed to connect to advisor A2A server")
        return

    request = _build_request(question, context_id)
    logger.info("Streaming A2A request to advisor: %s", question[:200])

    try:
        async for chunk in client.send_message_streaming(request):
            result = chunk.root
            if not hasattr(result, "result"):
                continue
            event = result.result
            if (
                isinstance(event, TaskStatusUpdateEvent)
                and event.status.state == TaskState.working
                and event.status.message
                and event.status.message.parts
            ):
                text = event.status.message.parts[0].root.text
                if text:
                    yield text
    except Exception:
        logger.exception("Error during A2A streaming from advisor")
        raise


async def _get_training_client() -> A2AClient:
    """Return a reusable A2A client for the training agent, resolving the card on first call."""
    global _training_client, _training_httpx_client

    if _training_client is not None:
        return _training_client

    async with _training_init_lock:
        if _training_client is not None:
            return _training_client

        base_url = f"{TRAINING_AGENT_A2A_URL}/a2a/"
        logger.info("Resolving training agent card at %s", base_url)

        _training_httpx_client = httpx.AsyncClient(timeout=120.0)
        resolver = A2ACardResolver(_training_httpx_client, base_url)
        agent_card = await resolver.get_agent_card()
        _training_client = A2AClient(httpx_client=_training_httpx_client, agent_card=agent_card)
        return _training_client


async def _get_dataset_client() -> A2AClient:
    """Return a reusable A2A client for the dataset agent, resolving the card on first call."""
    global _dataset_client, _dataset_httpx_client

    if _dataset_client is not None:
        return _dataset_client

    async with _dataset_init_lock:
        if _dataset_client is not None:
            return _dataset_client

        base_url = f"{DATASET_AGENT_A2A_URL}/a2a/"
        logger.info("Resolving dataset agent card at %s", base_url)

        _dataset_httpx_client = httpx.AsyncClient(timeout=120.0)
        resolver = A2ACardResolver(_dataset_httpx_client, base_url)
        agent_card = await resolver.get_agent_card()
        _dataset_client = A2AClient(httpx_client=_dataset_httpx_client, agent_card=agent_card)
        return _dataset_client


async def stream_training_agent(
    question: str, context_id: str | None = None
) -> AsyncGenerator[str, None]:
    """Stream tokens from the Training Agent via A2A streaming."""
    try:
        client = await _get_training_client()
    except Exception:
        logger.exception("Failed to connect to training agent A2A server")
        return

    request = _build_request(question, context_id)
    logger.info("Streaming A2A request to training agent: %s", question[:200])

    try:
        async for chunk in client.send_message_streaming(request):
            result = chunk.root
            if not hasattr(result, "result"):
                continue
            event = result.result
            if (
                isinstance(event, TaskStatusUpdateEvent)
                and event.status.state == TaskState.working
                and event.status.message
                and event.status.message.parts
            ):
                text = event.status.message.parts[0].root.text
                if text:
                    yield text
    except Exception:
        logger.exception("Error during A2A streaming from training agent")
        raise


async def stream_dataset_agent(
    question: str, context_id: str | None = None
) -> AsyncGenerator[str, None]:
    """Stream tokens from the Dataset Agent via A2A streaming."""
    try:
        client = await _get_dataset_client()
    except Exception:
        logger.exception("Failed to connect to dataset agent A2A server")
        return

    request = _build_request(question, context_id)
    logger.info("Streaming A2A request to dataset agent: %s", question[:200])

    try:
        async for chunk in client.send_message_streaming(request):
            result = chunk.root
            if not hasattr(result, "result"):
                continue
            event = result.result
            if (
                isinstance(event, TaskStatusUpdateEvent)
                and event.status.state == TaskState.working
                and event.status.message
                and event.status.message.parts
            ):
                text = event.status.message.parts[0].root.text
                if text:
                    yield text
    except Exception:
        logger.exception("Error during A2A streaming from dataset agent")
        raise


async def ask_training_agent(question: str, context_id: str | None = None) -> str:
    """Send a question to the Training Agent via A2A (blocking). Used as fallback."""
    try:
        client = await _get_training_client()
    except Exception:
        logger.exception("Failed to connect to training agent A2A server")
        return "Error: Could not connect to training agent."

    request = _build_request(question, context_id)
    logger.info("Sending A2A message to training agent: %s", question[:200])

    try:
        response = await client.send_message(request)
        result = response.root

        if hasattr(result, "error"):
            logger.error("A2A JSON-RPC error: %s", result.error)
            return f"Error from training agent: {result.error.message}"

        task_or_message = result.result
        if isinstance(task_or_message, Task):
            status = task_or_message.status
            if status and status.state == TaskState.failed:
                logger.error("Training agent task failed")
            if status and status.message and status.message.parts:
                text = status.message.parts[0].root.text
                logger.info("Training agent response: %s", text[:200])
                return text
        elif isinstance(task_or_message, Message):
            if task_or_message.parts:
                text = task_or_message.parts[0].root.text
                logger.info("Training agent response: %s", text[:200])
                return text

        logger.warning("No text found in A2A response from training agent")
        return "No response received from training agent."

    except Exception:
        logger.exception("Error during A2A communication with training agent")
        return "Error: Communication with training agent failed."


async def ask_advisor(question: str, context_id: str | None = None) -> str:
    """Send a question to the Advisor via A2A (blocking). Used as fallback."""
    try:
        client = await _get_client()
    except Exception:
        logger.exception("Failed to connect to advisor A2A server")
        return "Error: Could not connect to advisor agent."

    request = _build_request(question, context_id)
    logger.info("Sending A2A message to advisor: %s", question[:200])

    try:
        response = await client.send_message(request)
        result = response.root

        if hasattr(result, "error"):
            logger.error("A2A JSON-RPC error: %s", result.error)
            return f"Error from advisor: {result.error.message}"

        task_or_message = result.result
        if isinstance(task_or_message, Task):
            status = task_or_message.status
            if status and status.state == TaskState.failed:
                logger.error("Advisor task failed")
            if status and status.message and status.message.parts:
                text = status.message.parts[0].root.text
                logger.info("Advisor response: %s", text[:200])
                return text
        elif isinstance(task_or_message, Message):
            if task_or_message.parts:
                text = task_or_message.parts[0].root.text
                logger.info("Advisor response: %s", text[:200])
                return text

        logger.warning("No text found in A2A response")
        return "No response received from advisor."

    except Exception:
        logger.exception("Error during A2A communication with advisor")
        return "Error: Communication with advisor agent failed."


async def ask_dataset_agent(question: str, context_id: str | None = None) -> str:
    """Send a question to the Dataset Agent via A2A (blocking). Used as fallback."""
    try:
        client = await _get_dataset_client()
    except Exception:
        logger.exception("Failed to connect to dataset agent A2A server")
        return "Error: Could not connect to dataset agent."

    request = _build_request(question, context_id)
    logger.info("Sending A2A message to dataset agent: %s", question[:200])

    try:
        response = await client.send_message(request)
        result = response.root

        if hasattr(result, "error"):
            logger.error("A2A JSON-RPC error: %s", result.error)
            return f"Error from dataset agent: {result.error.message}"

        task_or_message = result.result
        if isinstance(task_or_message, Task):
            status = task_or_message.status
            if status and status.state == TaskState.failed:
                logger.error("Dataset agent task failed")
            if status and status.message and status.message.parts:
                text = status.message.parts[0].root.text
                logger.info("Dataset agent response: %s", text[:200])
                return text
        elif isinstance(task_or_message, Message):
            if task_or_message.parts:
                text = task_or_message.parts[0].root.text
                logger.info("Dataset agent response: %s", text[:200])
                return text

        logger.warning("No text found in A2A response from dataset agent")
        return "No response received from dataset agent."

    except Exception:
        logger.exception("Error during A2A communication with dataset agent")
        return "Error: Communication with dataset agent failed."
