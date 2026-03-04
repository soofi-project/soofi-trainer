"""A2A client wrapper for calling the Advisor agent."""

import asyncio
import logging
import os
import uuid

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
    TextPart,
)

logger = logging.getLogger(__name__)

ADVISOR_A2A_URL = os.getenv("ADVISOR_A2A_URL", "http://advisor:8000")

# Resolved once and reused across calls
_client: A2AClient | None = None
_httpx_client: httpx.AsyncClient | None = None
_init_lock = asyncio.Lock()


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


async def ask_advisor(question: str, context_id: str | None = None) -> str:
    """Send a question to the Advisor via A2A and return the response text.

    Args:
        question: The domain question to send (in German).
        context_id: Optional conversation context ID for multi-turn memory.
    """
    try:
        client = await _get_client()
    except Exception:
        logger.exception("Failed to connect to advisor A2A server")
        return "Error: Could not connect to advisor agent."

    request = SendMessageRequest(
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

    logger.info("Sending A2A message to advisor: %s", question[:200])

    try:
        response = await client.send_message(request)
        result = response.root

        # Check for JSON-RPC error
        if hasattr(result, "error"):
            logger.error("A2A JSON-RPC error: %s", result.error)
            return f"Error from advisor: {result.error.message}"

        # Extract text from the result (Task or Message)
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
