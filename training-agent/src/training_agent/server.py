"""FastAPI server exposing the Training Agent via A2A protocol."""

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from a2a.server.apps import A2AFastAPIApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.graph.state import CompiledStateGraph

from .a2a_handler import TrainingAgentExecutor
from .graph import build_graph
from .tools import mcp_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialized at startup
graph: CompiledStateGraph | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Load MCP tools and build the graph on startup."""
    global graph
    async with mcp_client.session("training") as session:
        tools = await load_mcp_tools(session)
        logger.info(f"Loaded {len(tools)} MCP tools: {[t.name for t in tools]}")
        graph = build_graph(tools)
        logger.info("Training agent graph built successfully")
        yield


app = FastAPI(title="Soofi Training Agent", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# A2A server
# ---------------------------------------------------------------------------

agent_card = AgentCard(
    name="Soofi Training Agent",
    description=(
        "Training job manager — starts, monitors and cancels LLM training jobs "
        "(LoRA, QLoRA, SFT, DPO) via the Training Gateway (language: German)"
    ),
    url="http://training-agent:8000/a2a/",
    version="0.1.0",
    capabilities=AgentCapabilities(streaming=True),
    skills=[
        AgentSkill(
            id="training_management",
            name="Training Management",
            description="Start, monitor and cancel LLM training jobs",
            tags=["training", "lora", "qlora", "fine-tuning", "jobs"],
        )
    ],
    default_input_modes=["text/plain"],
    default_output_modes=["text/plain"],
)

_a2a_handler = DefaultRequestHandler(
    agent_executor=TrainingAgentExecutor(lambda: graph),
    task_store=InMemoryTaskStore(),
)
app.mount("/a2a", A2AFastAPIApplication(agent_card, _a2a_handler).build())


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@app.get("/health")
async def health() -> dict[str, str]:
    if graph is None:
        return {"status": "error", "detail": "Graph not initialized"}
    return {"status": "ok"}
