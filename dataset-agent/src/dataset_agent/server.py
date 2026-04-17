"""FastAPI server exposing the Dataset Agent via A2A protocol."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from a2a.server.apps import A2AFastAPIApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from langgraph.graph.state import CompiledStateGraph

from .a2a_handler import DatasetAgentExecutor
from .graph import build_graph
from .tools import mcp_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

graph: CompiledStateGraph | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Load MCP tools and build the graph on startup.

    Uses ``get_tools`` (session-per-call) so tool invocations survive EDC or
    HuggingFace MCP restarts — a bound session would go stale on the other
    side.
    """
    global graph
    edc_tools = await mcp_client.get_tools(server_name="edc")
    logger.info("Loaded %d EDC MCP tools: %s", len(edc_tools), [t.name for t in edc_tools])

    hf_tools = await mcp_client.get_tools(server_name="huggingface")
    logger.info(
        "Loaded %d HuggingFace MCP tools: %s", len(hf_tools), [t.name for t in hf_tools]
    )

    graph = build_graph(edc_tools + hf_tools)
    logger.info("Dataset agent graph built successfully")
    yield


app = FastAPI(title="Soofi Dataset Agent", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_DATASET_I18N = {
    "description": {
        "de": (
            "Datensatzberater — sucht öffentliche Datensätze über HuggingFace "
            "und Eclipse Dataspace (EDC)"
        ),
        "en": (
            "Dataset advisor — searches public datasets via HuggingFace "
            "and Eclipse Dataspace (EDC)"
        ),
    },
    "skill_name": {"de": "Datensatzsuche", "en": "Dataset Search"},
    "skill_desc": {
        "de": "Findet passende Datensätze für Domäne, Aufgabe, Sprache und Lizenz",
        "en": "Finds matching datasets for domain, task, language, and license",
    },
}


def _build_agent_card(lang: str = "de") -> AgentCard:
    t = _DATASET_I18N
    lc = "en" if lang == "en" else "de"
    return AgentCard(
        name="Soofi Dataset Agent",
        description=t["description"][lc],
        url="http://dataset-agent:8000/a2a/",
        version="0.1.0",
        capabilities=AgentCapabilities(streaming=True),
        skills=[
            AgentSkill(
                id="dataset_search",
                name=t["skill_name"][lc],
                description=t["skill_desc"][lc],
                tags=["datasets", "huggingface", "edc", "dataspace"],
            )
        ],
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
    )


agent_card = _build_agent_card("de")

_a2a_handler = DefaultRequestHandler(
    agent_executor=DatasetAgentExecutor(lambda: graph),
    task_store=InMemoryTaskStore(),
)


@app.get("/a2a/.well-known/agent-card.json")
async def agent_card_i18n(lang: str = Query("de")) -> JSONResponse:
    card = _build_agent_card(lang)
    return JSONResponse(card.model_dump(by_alias=True, exclude_none=True))


_a2a_app = A2AFastAPIApplication(agent_card, _a2a_handler).build()
app.mount("/a2a", _a2a_app)


@app.get("/health")
async def health() -> dict[str, str]:
    if graph is None:
        return {"status": "error", "detail": "Graph not initialized"}
    return {"status": "ok"}
