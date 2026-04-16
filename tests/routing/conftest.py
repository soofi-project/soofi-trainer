"""Conftest for routing integration tests.

Skips the entire test session if the interaction agent is not reachable.
Run with: pytest tests/routing/ -m integration
"""

import httpx
import pytest

AGENT_BASE_URL = "https://localhost:3001"
HEALTH_URL = f"{AGENT_BASE_URL}/api/health"


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "integration: requires the full Soofi stack to be running (docker compose up)",
    )


@pytest.fixture(scope="session", autouse=True)
def require_stack() -> None:
    """Skip all tests in this module if the interaction agent is not reachable."""
    try:
        resp = httpx.get(HEALTH_URL, timeout=5.0, verify=False)
        resp.raise_for_status()
    except Exception as exc:
        pytest.skip(f"Soofi stack not reachable at {HEALTH_URL}: {exc}")
