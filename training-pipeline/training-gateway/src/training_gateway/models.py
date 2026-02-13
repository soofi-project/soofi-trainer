"""Pydantic models for the Training Gateway."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class PhaseStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class TrainingMethod(str, Enum):
    sft = "sft"
    lora = "lora"
    qlora = "qlora"
    rag = "rag"
    distillation = "distillation"
    cpt = "cpt"
    instruction = "instruction"
    dpo = "dpo"
    rlhf = "rlhf"


# Default phases per method
DEFAULT_PHASES: dict[TrainingMethod, list[str]] = {
    TrainingMethod.sft: ["data_preparation", "training", "model_upload"],
    TrainingMethod.lora: ["data_preparation", "training", "model_upload"],
    TrainingMethod.qlora: ["data_preparation", "training", "model_upload"],
    TrainingMethod.rag: ["data_preparation", "model_upload"],  # no training phase
    TrainingMethod.distillation: ["data_preparation", "training", "model_upload"],
    TrainingMethod.cpt: ["data_preparation", "training", "model_upload"],
    TrainingMethod.instruction: ["data_preparation", "training", "model_upload"],
    TrainingMethod.dpo: ["data_preparation", "training", "model_upload"],
    TrainingMethod.rlhf: ["data_preparation", "training", "model_upload"],
}


# --- Job Models ---


class JobPhase(BaseModel):
    name: str
    status: PhaseStatus = PhaseStatus.pending
    progress: int = Field(default=0, ge=0, le=100)
    started_at: datetime | None = None
    completed_at: datetime | None = None


class JobResult(BaseModel):
    model_ref: str | None = None
    metrics: dict[str, Any] = Field(default_factory=dict)


class Job(BaseModel):
    id: str
    method: TrainingMethod
    dataset_ref: str
    base_model: str
    config: dict[str, Any] = Field(default_factory=dict)
    status: JobStatus = JobStatus.queued
    current_phase: str | None = None
    phases: list[JobPhase] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    error: str | None = None
    result: JobResult | None = None


# --- Webhook Payload Models ---


class ProgressPayload(BaseModel):
    job_id: str
    phase: str
    progress: int = Field(ge=0, le=100)
    metrics: dict[str, Any] | None = None


class PhaseTransitionPayload(BaseModel):
    job_id: str
    from_phase: str
    to_phase: str


class CompletedPayload(BaseModel):
    job_id: str
    result: JobResult = Field(default_factory=JobResult)


class FailedPayload(BaseModel):
    job_id: str
    error: str
