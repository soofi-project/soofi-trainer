"""Docker backend — runs training containers via Docker API."""

from __future__ import annotations

import logging

import aiodocker

from training_gateway.backends.base import (
    BackendError,
    ContainerInfo,
    ContainerStatus,
    TrainingBackend,
)
from training_gateway.backends.config import BackendConfig
from training_gateway.models import Job

logger = logging.getLogger(__name__)


class DockerBackend(TrainingBackend):
    """Run training containers via remote (or local) Docker daemon."""

    def __init__(self, config: BackendConfig) -> None:
        self._config = config
        self._docker: aiodocker.Docker | None = None

    async def _get_docker(self) -> aiodocker.Docker:
        """Lazy-connect to Docker daemon."""
        if self._docker is None:
            url = self._config.docker_host
            self._docker = aiodocker.Docker(url=url)
            try:
                await self._docker.version()
            except Exception as e:
                self._docker = None
                raise BackendError(
                    f"Cannot connect to Docker at {url or 'default socket'}: {e}"
                ) from e
            logger.info("Connected to Docker at %s", url or "default socket")
        return self._docker

    async def start_container(self, job: Job) -> str:
        """Create and start a Docker container for the training job."""
        docker = await self._get_docker()

        cmd = [
            "--method", job.method.value,
            "--dataset", job.dataset_ref,
            "--base-model", job.base_model,
            "--webhook-url", self._config.gateway_url,
            "--job-id", job.id,
            "--duration", str(self._config.default_duration),
        ]
        fail_prob = job.config.get("fail_probability", 0.0)
        if fail_prob > 0:
            cmd.extend(["--fail-probability", str(fail_prob)])

        container_config: dict = {
            "Image": self._config.training_image,
            "Cmd": cmd,
            "Labels": {
                "soofi.job_id": job.id,
                "soofi.method": job.method.value,
                "managed-by": "soofi-training-gateway",
            },
            "HostConfig": {
                "AutoRemove": True,
                "NetworkMode": self._config.container_network,
            },
        }

        # GPU allocation
        if self._config.gpu_device:
            device_ids = (
                None
                if self._config.gpu_device == "all"
                else [self._config.gpu_device]
            )
            container_config["HostConfig"]["DeviceRequests"] = [
                {
                    "Driver": "nvidia",
                    "Count": -1 if device_ids is None else 0,
                    "DeviceIDs": device_ids or [],
                    "Capabilities": [["gpu"]],
                }
            ]

        container_name = f"soofi-training-{job.id[:12]}"

        try:
            container = await docker.containers.create_or_replace(
                name=container_name,
                config=container_config,
            )
            await container.start()
        except Exception as e:
            raise BackendError(
                f"Failed to start Docker container for job {job.id}: {e}"
            ) from e

        container_id = container.id
        logger.info(
            "Started Docker container %s (%s) for job %s",
            container_name,
            container_id[:12],
            job.id,
        )
        return container_id

    async def stop_container(self, container_id: str) -> None:
        """Stop and remove a Docker container."""
        docker = await self._get_docker()
        try:
            container = await docker.containers.get(container_id)
            await container.stop()
            try:
                await container.delete(force=True)
            except aiodocker.exceptions.DockerError:
                pass  # AutoRemove already cleaned it up
        except aiodocker.exceptions.DockerError as e:
            if "404" in str(e) or "No such container" in str(e):
                logger.warning(
                    "Container %s not found (already removed?)", container_id[:12]
                )
            else:
                raise BackendError(
                    f"Failed to stop container {container_id}: {e}"
                ) from e

    async def get_container_status(self, container_id: str) -> ContainerInfo:
        """Inspect a Docker container's status."""
        docker = await self._get_docker()
        try:
            container = await docker.containers.get(container_id)
            info = await container.show()
            state = info.get("State", {})
            running = state.get("Running", False)
            exit_code = state.get("ExitCode")

            return ContainerInfo(
                container_id=container_id,
                status=ContainerStatus.running if running else ContainerStatus.exited,
                exit_code=exit_code,
            )
        except aiodocker.exceptions.DockerError:
            return ContainerInfo(
                container_id=container_id,
                status=ContainerStatus.not_found,
            )

    async def close(self) -> None:
        """Close the Docker client connection."""
        if self._docker is not None:
            await self._docker.close()
            self._docker = None
            logger.info("Docker client closed")
