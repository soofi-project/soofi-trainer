"""Integration tests for LocalBackend — runs actual subprocesses."""

import asyncio
from pathlib import Path

import pytest

from training_gateway import backends, db
from training_gateway.backends.base import ContainerStatus
from training_gateway.backends.config import BackendConfig
from training_gateway.backends.local_backend import LocalBackend
from training_gateway.models import TrainingMethod

# Resolve simulate.py path relative to this test file
_SIMULATE_SCRIPT = str(
    (Path(__file__).parents[3] / "training-container" / "simulate.py").resolve()
)


def _make_local_config(**overrides) -> BackendConfig:
    defaults = {
        "backend_type": "local",
        "docker_host": None,
        "training_image": "unused",
        "gpu_device": "all",
        "container_network": "unused",
        "gateway_url": "http://localhost:9999/webhooks",  # unreachable, but that's ok
        "default_duration": 5,
        "simulate_script_path": _SIMULATE_SCRIPT,
    }
    defaults.update(overrides)
    return BackendConfig(**defaults)


@pytest.fixture
async def local_backend(init_db):
    """Initialize a local backend with short duration for testing."""
    config = _make_local_config()
    await backends.init_backend(config)
    yield backends.get_backend()
    await backends.close_backend()


@pytest.mark.integration
class TestLocalBackendStart:
    @pytest.mark.asyncio
    async def test_start_returns_local_id(self, local_backend):
        job = await db.create_job(TrainingMethod.lora, "ds", "m")
        container_id = await local_backend.start_container(job)
        assert container_id.startswith("local-")
        # Clean up
        await local_backend.stop_container(container_id)

    @pytest.mark.asyncio
    async def test_status_running_after_start(self, local_backend):
        job = await db.create_job(TrainingMethod.lora, "ds", "m")
        container_id = await local_backend.start_container(job)
        info = await local_backend.get_container_status(container_id)
        assert info.status == ContainerStatus.running
        # Clean up
        await local_backend.stop_container(container_id)


@pytest.mark.integration
class TestLocalBackendStop:
    @pytest.mark.asyncio
    async def test_stop_terminates(self, local_backend):
        job = await db.create_job(TrainingMethod.lora, "ds", "m")
        container_id = await local_backend.start_container(job)
        await local_backend.stop_container(container_id)
        info = await local_backend.get_container_status(container_id)
        assert info.status == ContainerStatus.not_found

    @pytest.mark.asyncio
    async def test_stop_nonexistent_is_noop(self, local_backend):
        # Should not raise
        await local_backend.stop_container("local-99999")


@pytest.mark.integration
class TestLocalBackendStatus:
    @pytest.mark.asyncio
    async def test_not_found_for_unknown(self, local_backend):
        info = await local_backend.get_container_status("local-nonexistent")
        assert info.status == ContainerStatus.not_found


@pytest.mark.integration
class TestLocalBackendClose:
    @pytest.mark.asyncio
    async def test_close_stops_all_processes(self, init_db):
        config = _make_local_config()
        backend = LocalBackend(config)

        job1 = await db.create_job(TrainingMethod.lora, "ds1", "m1")
        job2 = await db.create_job(TrainingMethod.sft, "ds2", "m2")
        cid1 = await backend.start_container(job1)
        cid2 = await backend.start_container(job2)

        assert len(backend._processes) == 2

        await backend.close()

        assert len(backend._processes) == 0
