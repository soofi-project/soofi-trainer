"""Shared pytest fixtures for training-gateway tests."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Generator
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from training_gateway import backends, db


@pytest.fixture(autouse=True)
def _temp_db(tmp_path: Path) -> Generator[None, None, None]:
    """Redirect the DB to a temporary file for every test, then clean up."""
    db_path = str(tmp_path / "test.db")
    original = db.DB_PATH
    db.DB_PATH = db_path
    yield
    db.DB_PATH = original


@pytest.fixture
async def init_db() -> AsyncGenerator[None, None]:
    """Initialize a fresh test database and tear it down after."""
    await db.init_db()
    # Provide a mock backend so MCP tools can call start/stop container
    mock = AsyncMock(spec=backends.TrainingBackend)
    mock.start_container.return_value = "mock-container-123"
    backends._backend = mock
    yield
    backends._backend = None
    await db.close_db()
    db._db = None


@pytest.fixture
async def async_client(init_db: None) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client against the FastAPI app (no real server needed)."""
    # Import app lazily so DB_PATH is already patched
    from training_gateway.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
