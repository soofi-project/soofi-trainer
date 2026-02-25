"""Abstract base for training container backends."""

from __future__ import annotations

import abc
from enum import Enum

from pydantic import BaseModel

from training_gateway.models import Job


class ContainerStatus(str, Enum):
    running = "running"
    exited = "exited"
    not_found = "not_found"


class ContainerInfo(BaseModel):
    container_id: str
    status: ContainerStatus
    exit_code: int | None = None


class BackendError(Exception):
    """Raised when a backend operation fails."""


class TrainingBackend(abc.ABC):
    """Abstract interface for training container orchestration."""

    @abc.abstractmethod
    async def start_container(self, job: Job) -> str:
        """Start a training container for the given job.

        Returns a container_id string for tracking.
        Raises BackendError if the container could not be started.
        """

    @abc.abstractmethod
    async def stop_container(self, container_id: str) -> None:
        """Stop and remove a running training container.

        Idempotent: does not raise if container is already stopped/removed.
        """

    @abc.abstractmethod
    async def get_container_status(self, container_id: str) -> ContainerInfo:
        """Get the current status of a container."""

    async def close(self) -> None:
        """Clean up resources (connections, etc). Called on shutdown."""
