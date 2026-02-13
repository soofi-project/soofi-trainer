"""Unit tests for training backend abstraction."""

import pytest

from training_gateway.backends.base import (
    BackendError,
    ContainerInfo,
    ContainerStatus,
)
from training_gateway.backends.config import BackendConfig, load_config


def _make_config(**overrides) -> BackendConfig:
    """Helper to create a BackendConfig with defaults."""
    defaults = {
        "backend_type": "local",
        "docker_host": None,
        "training_image": "test:latest",
        "gpu_device": "all",
        "container_network": "test-net",
        "gateway_url": "http://localhost:8000/webhooks",
        "default_duration": 10,
        "simulate_script_path": "/path/to/simulate.py",
    }
    defaults.update(overrides)
    return BackendConfig(**defaults)


@pytest.mark.unit
class TestBackendConfig:
    def test_load_defaults(self):
        config = load_config()
        assert config.backend_type == "local"
        assert config.docker_host is None
        assert config.default_duration == 120
        assert config.gateway_url == "http://training-gateway:8000/webhooks"

    def test_load_from_env(self, monkeypatch):
        monkeypatch.setenv("TRAINING_BACKEND", "docker")
        monkeypatch.setenv("TRAINING_DOCKER_HOST", "ssh://user@gpu")
        monkeypatch.setenv("TRAINING_DEFAULT_DURATION", "60")
        monkeypatch.setenv("TRAINING_IMAGE", "my-image:v2")
        config = load_config()
        assert config.backend_type == "docker"
        assert config.docker_host == "ssh://user@gpu"
        assert config.default_duration == 60
        assert config.training_image == "my-image:v2"

    def test_config_is_frozen(self):
        config = _make_config()
        with pytest.raises(AttributeError):
            config.backend_type = "docker"


@pytest.mark.unit
class TestBackendFactory:
    def test_create_local(self):
        from training_gateway.backends import _create_backend
        from training_gateway.backends.local_backend import LocalBackend

        config = _make_config()
        backend = _create_backend(config)
        assert isinstance(backend, LocalBackend)

    def test_create_docker(self):
        from training_gateway.backends import _create_backend
        from training_gateway.backends.docker_backend import DockerBackend

        config = _make_config(backend_type="docker")
        backend = _create_backend(config)
        assert isinstance(backend, DockerBackend)

    def test_invalid_type_raises(self):
        from training_gateway.backends import _create_backend

        config = _make_config(backend_type="kubernetes")
        with pytest.raises(BackendError, match="Unknown backend type"):
            _create_backend(config)


@pytest.mark.unit
class TestContainerInfo:
    def test_running(self):
        info = ContainerInfo(
            container_id="abc123",
            status=ContainerStatus.running,
        )
        assert info.status == ContainerStatus.running
        assert info.exit_code is None

    def test_exited_with_code(self):
        info = ContainerInfo(
            container_id="abc123",
            status=ContainerStatus.exited,
            exit_code=0,
        )
        assert info.exit_code == 0

    def test_not_found(self):
        info = ContainerInfo(
            container_id="missing",
            status=ContainerStatus.not_found,
        )
        assert info.status == ContainerStatus.not_found


@pytest.mark.unit
class TestContainerStatus:
    def test_values(self):
        assert ContainerStatus.running == "running"
        assert ContainerStatus.exited == "exited"
        assert ContainerStatus.not_found == "not_found"


@pytest.mark.unit
class TestBackendError:
    def test_is_exception(self):
        err = BackendError("something broke")
        assert isinstance(err, Exception)
        assert str(err) == "something broke"
