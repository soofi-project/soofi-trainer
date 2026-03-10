"""FastAPI server exposing the Training Agent via A2A protocol."""

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from a2a.server.apps import A2AFastAPIApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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

_TRAINING_I18N = {
    "description": {
        "de": (
            "Trainingsmanager — startet, überwacht und bricht LLM-Trainingsjobs ab "
            "(LoRA, QLoRA, SFT, DPO) über das Training Gateway"
        ),
        "en": (
            "Training manager — starts, monitors, and cancels LLM training jobs "
            "(LoRA, QLoRA, SFT, DPO) via the Training Gateway"
        ),
    },
    "skill_name": {"de": "Trainingsverwaltung", "en": "Training Management"},
    "skill_desc": {
        "de": "Trainingsjobs starten, überwachen und abbrechen",
        "en": "Start, monitor, and cancel training jobs",
    },
}


def _build_agent_card(lang: str = "de") -> AgentCard:
    t = _TRAINING_I18N
    lc = "en" if lang == "en" else "de"
    return AgentCard(
        name="Soofi Training Agent",
        description=t["description"][lc],
        url="http://training-agent:8000/a2a/",
        version="0.1.0",
        capabilities=AgentCapabilities(streaming=True),
        skills=[
            AgentSkill(
                id="training_management",
                name=t["skill_name"][lc],
                description=t["skill_desc"][lc],
                tags=["training", "lora", "qlora", "fine-tuning", "jobs"],
            )
        ],
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
    )


# Default DE card for A2A mount
agent_card = _build_agent_card("de")

_a2a_handler = DefaultRequestHandler(
    agent_executor=TrainingAgentExecutor(lambda: graph),
    task_store=InMemoryTaskStore(),
)
# Register the i18n agent card route BEFORE mounting the A2A sub-app,
# so Starlette matches this specific path before the /a2a/ prefix mount.
@app.get("/a2a/.well-known/agent-card.json")
async def agent_card_i18n(lang: str = Query("de")) -> JSONResponse:
    card = _build_agent_card(lang)
    return JSONResponse(card.model_dump(by_alias=True, exclude_none=True))


_a2a_app = A2AFastAPIApplication(agent_card, _a2a_handler).build()
app.mount("/a2a", _a2a_app)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@app.get("/health")
async def health() -> dict:
    if graph is None:
        return {"status": "error", "detail": "Graph not initialized"}
    return {"status": "ok"}
