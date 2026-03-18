import uvicorn
from contextlib import asynccontextmanager
from fastmcp import FastMCP
from fastmcp.server.middleware.logging import LoggingMiddleware
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from edc_mcp.tools import register_tools
from edc_mcp.api.federated_catalog import start_background_refresh

import logging

logging.basicConfig(level=logging.DEBUG)


@asynccontextmanager
async def lifespan(_app):
    """Application lifespan manager for startup and shutdown events."""
    logging.info("Starting federated catalog background refresh...")
    start_background_refresh()
    yield


mcp = FastMCP("edc", lifespan=lifespan)
mcp.add_middleware(LoggingMiddleware(
    include_payloads=True,
    max_payload_length=1000
))

register_tools(mcp)

if __name__ == "__main__":
    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
            allow_headers=[
                "mcp-protocol-version",
                "mcp-session-id",
                "Authorization",
                "Content-Type",
            ],
            expose_headers=["mcp-session-id"],
        )
    ]

    app = mcp.http_app(middleware=middleware)
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8081,
        timeout_graceful_shutdown=3
    )
