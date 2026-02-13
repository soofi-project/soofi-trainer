"""Local backend — runs training as a subprocess (no Docker required)."""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

from training_gateway.backends.base import (
    BackendError,
    ContainerInfo,
    ContainerStatus,
    TrainingBackend,
)
from training_gateway.backends.config import BackendConfig
from training_gateway.models import Job

logger = logging.getLogger(__name__)


class LocalBackend(TrainingBackend):
    """Run training simulations as local subprocesses."""

    def __init__(self, config: BackendConfig) -> None:
        self._config = config
        self._processes: dict[str, asyncio.subprocess.Process] = {}
        self._script_path = self._resolve_script_path()

    def _resolve_script_path(self) -> str:
        """Find simulate.py. Check config override, then common locations."""
        if self._config.simulate_script_path:
            return self._config.simulate_script_path

        # Walk up from this file to find the dummy-training-container
        candidates = [
            Path(__file__).parents[4] / "dummy-training-container" / "simulate.py",
            Path("training-pipeline/dummy-training-container/simulate.py"),
        ]
        for candidate in candidates:
            if candidate.is_file():
                return str(candidate.resolve())

        raise BackendError(
            "Cannot find simulate.py. Set TRAINING_SIMULATE_SCRIPT env var."
        )

    async def start_container(self, job: Job) -> str:
        """Start simulate.py as an async subprocess."""
        cmd = [
            sys.executable,
            self._script_path,
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

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except Exception as e:
            raise BackendError(f"Failed to start subprocess: {e}") from e

        container_id = f"local-{process.pid}"
        self._processes[container_id] = process
        logger.info(
            "Started local process %s (pid=%d) for job %s",
            container_id,
            process.pid,
            job.id,
        )
        return container_id

    async def stop_container(self, container_id: str) -> None:
        """Terminate the subprocess if still running."""
        process = self._processes.pop(container_id, None)
        if process is None:
            logger.warning("Process %s not found (already stopped?)", container_id)
            return

        if process.returncode is None:
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
            logger.info("Stopped local process %s", container_id)

    async def get_container_status(self, container_id: str) -> ContainerInfo:
        """Check subprocess status."""
        process = self._processes.get(container_id)
        if process is None:
            return ContainerInfo(
                container_id=container_id,
                status=ContainerStatus.not_found,
            )

        if process.returncode is None:
            return ContainerInfo(
                container_id=container_id,
                status=ContainerStatus.running,
            )

        return ContainerInfo(
            container_id=container_id,
            status=ContainerStatus.exited,
            exit_code=process.returncode,
        )

    async def close(self) -> None:
        """Terminate all tracked subprocesses."""
        for cid in list(self._processes):
            await self.stop_container(cid)
