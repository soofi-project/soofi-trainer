"""Backend configuration from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class BackendConfig:
    """Configuration for the training backend."""

    backend_type: str  # "docker" | "local"

    # Docker-specific
    docker_host: str | None
    training_image_name: str
    training_image_version: str
    gpu_device: str
    container_network: str

    # Shared
    gateway_url: str
    default_duration: int

    # Local-specific
    simulate_script_path: str | None


def load_config() -> BackendConfig:
    """Load backend configuration from environment variables."""
    return BackendConfig(
        backend_type=os.getenv("TRAINING_BACKEND", "local"),
        docker_host=os.getenv("TRAINING_DOCKER_HOST"),
        training_image_name=os.getenv(
            "TRAINING_IMAGE_NAME", "soofi/training-container"
        ),
        training_image_version=os.getenv(
            "SOOFI_TRAINER_VERSION"
        ),
        gpu_device=os.getenv("TRAINING_GPU_DEVICE", "all"),
        container_network="soofi-training-network",  #os.getenv(
        #    "TRAINING_CONTAINER_NETWORK", "soofi-trainer_soofi-network"
        #),
        gateway_url=os.getenv(
            "TRAINING_GATEWAY_URL", "http://training-gateway:8000/webhooks"
        ),
        default_duration=int(os.getenv("TRAINING_DEFAULT_DURATION", "120")),
        simulate_script_path=os.getenv("TRAINING_SIMULATE_SCRIPT"),
    )
