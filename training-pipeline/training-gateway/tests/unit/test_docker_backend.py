"""Unit tests for DockerBackend with mocked aiodocker."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from training_gateway.backends.base import BackendError, ContainerStatus
from training_gateway.backends.config import BackendConfig
from training_gateway.backends.docker_backend import DockerBackend
from training_gateway.models import Job, JobPhase, JobStatus, PhaseStatus, TrainingMethod


def _make_config(**overrides) -> BackendConfig:
    defaults = {
        "backend_type": "docker",
        "docker_host": "tcp://gpu-server:2376",
        "training_image": "soofi/training-container:latest",
        "gpu_device": "all",
        "container_network": "soofi-trainer_soofi-network",
        "gateway_url": "http://training-gateway:8000/webhooks",
        "default_duration": 30,
        "simulate_script_path": None,
    }
    defaults.update(overrides)
    return BackendConfig(**defaults)


def _make_job(**overrides) -> Job:
    from datetime import datetime, timezone

    defaults = {
        "id": "test-job-1234-5678",
        "method": TrainingMethod.lora,
        "dataset_ref": "s3://datasets/sample.jsonl",
        "base_model": "meta-llama/Llama-3.1-8B",
        "config": {},
        "status": JobStatus.running,
        "current_phase": "data_preparation",
        "phases": [
            JobPhase(name="data_preparation", status=PhaseStatus.running),
            JobPhase(name="training", status=PhaseStatus.pending),
            JobPhase(name="model_upload", status=PhaseStatus.pending),
        ],
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    defaults.update(overrides)
    return Job(**defaults)


@pytest.mark.unit
class TestDockerBackendStart:
    @pytest.mark.asyncio
    async def test_start_creates_container(self):
        config = _make_config()
        backend = DockerBackend(config)

        mock_container = AsyncMock()
        mock_container.id = "docker-abc123"
        mock_docker = AsyncMock()
        mock_docker.containers.create_or_replace.return_value = mock_container
        mock_docker.version.return_value = {"Version": "24.0"}
        backend._docker = mock_docker

        job = _make_job()
        container_id = await backend.start_container(job)

        assert container_id == "docker-abc123"
        mock_docker.containers.create_or_replace.assert_called_once()
        mock_container.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_passes_correct_cmd(self):
        config = _make_config(default_duration=60)
        backend = DockerBackend(config)

        mock_container = AsyncMock()
        mock_container.id = "docker-abc123"
        mock_docker = AsyncMock()
        mock_docker.containers.create_or_replace.return_value = mock_container
        backend._docker = mock_docker

        job = _make_job()
        await backend.start_container(job)

        call_kwargs = mock_docker.containers.create_or_replace.call_args
        container_config = call_kwargs.kwargs.get("config", call_kwargs[1].get("config", {}))
        cmd = container_config["Cmd"]

        assert "--method" in cmd
        assert "lora" in cmd
        assert "--job-id" in cmd
        assert job.id in cmd
        assert "--duration" in cmd
        assert "60" in cmd

    @pytest.mark.asyncio
    async def test_start_sets_gpu_device_requests(self):
        config = _make_config(gpu_device="0")
        backend = DockerBackend(config)

        mock_container = AsyncMock()
        mock_container.id = "docker-abc123"
        mock_docker = AsyncMock()
        mock_docker.containers.create_or_replace.return_value = mock_container
        backend._docker = mock_docker

        job = _make_job()
        await backend.start_container(job)

        call_kwargs = mock_docker.containers.create_or_replace.call_args
        container_config = call_kwargs.kwargs.get("config", call_kwargs[1].get("config", {}))
        device_requests = container_config["HostConfig"]["DeviceRequests"]

        assert len(device_requests) == 1
        assert device_requests[0]["DeviceIDs"] == ["0"]
        assert device_requests[0]["Capabilities"] == [["gpu"]]

    @pytest.mark.asyncio
    async def test_start_sets_network_mode(self):
        config = _make_config(container_network="my-network")
        backend = DockerBackend(config)

        mock_container = AsyncMock()
        mock_container.id = "docker-abc123"
        mock_docker = AsyncMock()
        mock_docker.containers.create_or_replace.return_value = mock_container
        backend._docker = mock_docker

        job = _make_job()
        await backend.start_container(job)

        call_kwargs = mock_docker.containers.create_or_replace.call_args
        container_config = call_kwargs.kwargs.get("config", call_kwargs[1].get("config", {}))

        assert container_config["HostConfig"]["NetworkMode"] == "my-network"

    @pytest.mark.asyncio
    async def test_start_sets_labels(self):
        config = _make_config()
        backend = DockerBackend(config)

        mock_container = AsyncMock()
        mock_container.id = "docker-abc123"
        mock_docker = AsyncMock()
        mock_docker.containers.create_or_replace.return_value = mock_container
        backend._docker = mock_docker

        job = _make_job()
        await backend.start_container(job)

        call_kwargs = mock_docker.containers.create_or_replace.call_args
        container_config = call_kwargs.kwargs.get("config", call_kwargs[1].get("config", {}))
        labels = container_config["Labels"]

        assert labels["soofi.job_id"] == job.id
        assert labels["soofi.method"] == "lora"
        assert labels["managed-by"] == "soofi-training-gateway"

    @pytest.mark.asyncio
    async def test_start_failure_raises_backend_error(self):
        config = _make_config()
        backend = DockerBackend(config)

        mock_docker = AsyncMock()
        mock_docker.containers.create_or_replace.side_effect = Exception("image not found")
        backend._docker = mock_docker

        job = _make_job()
        with pytest.raises(BackendError, match="Failed to start Docker container"):
            await backend.start_container(job)


@pytest.mark.unit
class TestDockerBackendStop:
    @pytest.mark.asyncio
    async def test_stop_calls_stop_and_delete(self):
        config = _make_config()
        backend = DockerBackend(config)

        mock_container = AsyncMock()
        mock_docker = AsyncMock()
        mock_docker.containers.get.return_value = mock_container
        backend._docker = mock_docker

        await backend.stop_container("docker-abc123")

        mock_container.stop.assert_called_once()
        mock_container.delete.assert_called_once_with(force=True)

    @pytest.mark.asyncio
    async def test_stop_handles_not_found(self):
        import aiodocker.exceptions

        config = _make_config()
        backend = DockerBackend(config)

        mock_docker = AsyncMock()
        mock_docker.containers.get.side_effect = aiodocker.exceptions.DockerError(
            404, "No such container"
        )
        backend._docker = mock_docker

        # Should not raise
        await backend.stop_container("missing-container")


@pytest.mark.unit
class TestDockerBackendStatus:
    @pytest.mark.asyncio
    async def test_running_container(self):
        config = _make_config()
        backend = DockerBackend(config)

        mock_container = AsyncMock()
        mock_container.show.return_value = {
            "State": {"Running": True, "ExitCode": 0}
        }
        mock_docker = AsyncMock()
        mock_docker.containers.get.return_value = mock_container
        backend._docker = mock_docker

        info = await backend.get_container_status("docker-abc123")
        assert info.status == ContainerStatus.running

    @pytest.mark.asyncio
    async def test_exited_container(self):
        config = _make_config()
        backend = DockerBackend(config)

        mock_container = AsyncMock()
        mock_container.show.return_value = {
            "State": {"Running": False, "ExitCode": 1}
        }
        mock_docker = AsyncMock()
        mock_docker.containers.get.return_value = mock_container
        backend._docker = mock_docker

        info = await backend.get_container_status("docker-abc123")
        assert info.status == ContainerStatus.exited
        assert info.exit_code == 1

    @pytest.mark.asyncio
    async def test_not_found_container(self):
        import aiodocker.exceptions

        config = _make_config()
        backend = DockerBackend(config)

        mock_docker = AsyncMock()
        mock_docker.containers.get.side_effect = aiodocker.exceptions.DockerError(
            404, "No such container"
        )
        backend._docker = mock_docker

        info = await backend.get_container_status("missing")
        assert info.status == ContainerStatus.not_found


@pytest.mark.unit
class TestDockerBackendClose:
    @pytest.mark.asyncio
    async def test_close_closes_client(self):
        config = _make_config()
        backend = DockerBackend(config)

        mock_docker = AsyncMock()
        backend._docker = mock_docker

        await backend.close()

        mock_docker.close.assert_called_once()
        assert backend._docker is None

    @pytest.mark.asyncio
    async def test_close_when_not_connected(self):
        config = _make_config()
        backend = DockerBackend(config)

        # Should not raise
        await backend.close()
