"""Training backend management — singleton pattern matching db.py."""

from __future__ import annotations

import logging

from training_gateway.backends.base import (
    BackendError,
    ContainerInfo,
    ContainerStatus,
    TrainingBackend,
)
from training_gateway.backends.config import BackendConfig, load_config

logger = logging.getLogger(__name__)

_backend: TrainingBackend | None = None
_config: BackendConfig | None = None

__all__ = [
    "BackendError",
    "ContainerInfo",
    "ContainerStatus",
    "TrainingBackend",
    "init_backend",
    "close_backend",
    "get_backend",
    "get_config",
]


def _create_backend(config: BackendConfig) -> TrainingBackend:
    """Factory: instantiate the correct backend from config."""
    if config.backend_type == "local":
        from training_gateway.backends.local_backend import LocalBackend

        return LocalBackend(config)
    elif config.backend_type == "docker":
        from training_gateway.backends.docker_backend import DockerBackend

        return DockerBackend(config)
    else:
        raise BackendError(
            f"Unknown backend type '{config.backend_type}'. Valid: local, docker"
        )


async def init_backend(config: BackendConfig | None = None) -> None:
    """Initialize the training backend singleton."""
    global _backend, _config
    _config = config or load_config()
    _backend = _create_backend(_config)
    logger.info("Training backend initialized: %s", _config.backend_type)


async def close_backend() -> None:
    """Shut down the training backend and release resources."""
    global _backend, _config
    if _backend is not None:
        await _backend.close()
        _backend = None
        _config = None
        logger.info("Training backend closed")


def get_backend() -> TrainingBackend:
    """Get the initialized backend. Raises if not initialized."""
    if _backend is None:
        raise RuntimeError(
            "Training backend not initialized. Call init_backend() first."
        )
    return _backend


def get_config() -> BackendConfig:
    """Get the current backend configuration."""
    if _config is None:
        raise RuntimeError("Backend config not loaded. Call init_backend() first.")
    return _config
