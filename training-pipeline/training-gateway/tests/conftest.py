"""Shared pytest fixtures for training-gateway tests."""

from __future__ import annotations

import os
import tempfile
from collections.abc import AsyncGenerator, Generator
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from training_gateway import db


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
    yield
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
