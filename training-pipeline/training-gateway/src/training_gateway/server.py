"""Training Gateway server — FastAPI + FastMCP."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from training_gateway import backends, db
from training_gateway.mcp_tools import mcp
from training_gateway.rest_api import router as rest_router
from training_gateway.webhooks import router as webhooks_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Build MCP ASGI app (must happen before lifespan to access its lifespan)
mcp_app = mcp.http_app(path="/mcp")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize gateway resources and MCP session manager."""
    await db.init_db()
    await backends.init_backend()
    logger.info(
        "Training Gateway started (backend=%s)", backends.get_config().backend_type
    )
    # Run the MCP app's lifespan to initialize its session manager
    async with mcp_app.lifespan(app):
        yield
    await backends.close_backend()
    await db.close_db()
    logger.info("Training Gateway stopped")


app = FastAPI(
    title="Soofi Training Gateway",
    description="Training job management with MCP tools and webhook callbacks.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Health check (must be registered before the catch-all MCP mount)
@app.get("/health")
async def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok", "service": "training-gateway"}


# Job REST endpoints (must be before the catch-all MCP mount)
app.include_router(rest_router)

# Webhook REST endpoints
app.include_router(webhooks_router)

# Mount MCP server last (catch-all — FastMCP exposes its endpoint at /mcp internally)
app.mount("", mcp_app)


def main() -> None:
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")


if __name__ == "__main__":
    main()
