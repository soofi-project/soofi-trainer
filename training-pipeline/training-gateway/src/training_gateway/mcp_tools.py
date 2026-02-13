"""MCP tool definitions for the Training Gateway."""

from __future__ import annotations

import logging
from typing import Any

from fastmcp import FastMCP

from training_gateway import db
from training_gateway.models import JobStatus, TrainingMethod

logger = logging.getLogger(__name__)

mcp = FastMCP("soofi-training-gateway")


@mcp.tool()
async def start_training_job(
    method: str,
    dataset_ref: str,
    base_model: str,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Start a new training job for the given specialization method.

    Args:
        method: Training method (lora, sft, qlora, rag, distillation, cpt, instruction, dpo, rlhf)
        dataset_ref: Reference to the training dataset
        base_model: Base model name (e.g. meta-llama/Llama-3.1-8B)
        config: Optional configuration overrides for the training job

    Returns:
        Job details including the job_id for tracking
    """
    try:
        training_method = TrainingMethod(method)
    except ValueError:
        valid = [m.value for m in TrainingMethod]
        return {"error": f"Unknown method '{method}'. Valid methods: {valid}"}

    job = await db.create_job(
        method=training_method,
        dataset_ref=dataset_ref,
        base_model=base_model,
        config=config,
    )

    return {
        "job_id": job.id,
        "method": job.method.value,
        "status": job.status.value,
        "current_phase": job.current_phase,
        "phases": [p.name for p in job.phases],
        "message": f"Training job started (method={method})",
    }


@mcp.tool()
async def get_job_status(job_id: str) -> dict[str, Any]:
    """
    Get the current status of a training job.

    Args:
        job_id: The UUID of the training job

    Returns:
        Full job state including phases, progress, and metrics
    """
    job = await db.get_job(job_id)
    if job is None:
        return {"error": f"Job '{job_id}' not found"}

    return job.model_dump(mode="json")


@mcp.tool()
async def list_training_jobs(status: str | None = None) -> dict[str, Any]:
    """
    List all training jobs, optionally filtered by status.

    Args:
        status: Optional filter (queued, running, completed, failed, cancelled)

    Returns:
        List of jobs with their current status
    """
    status_filter = None
    if status:
        try:
            status_filter = JobStatus(status)
        except ValueError:
            valid = [s.value for s in JobStatus]
            return {"error": f"Unknown status '{status}'. Valid: {valid}"}

    jobs = await db.list_jobs(status=status_filter)

    return {
        "jobs": [
            {
                "id": j.id,
                "method": j.method.value,
                "status": j.status.value,
                "current_phase": j.current_phase,
                "created_at": j.created_at.isoformat(),
                "updated_at": j.updated_at.isoformat(),
            }
            for j in jobs
        ],
        "total": len(jobs),
    }


@mcp.tool()
async def cancel_training_job(job_id: str) -> dict[str, Any]:
    """
    Cancel a running or queued training job.

    Args:
        job_id: The UUID of the training job to cancel

    Returns:
        Updated job status
    """
    job = await db.get_job(job_id)
    if job is None:
        return {"error": f"Job '{job_id}' not found"}

    if job.status in (JobStatus.completed, JobStatus.failed, JobStatus.cancelled):
        return {
            "error": f"Job '{job_id}' is already {job.status.value} and cannot be cancelled",
            "job_id": job_id,
            "status": job.status.value,
        }

    job = await db.cancel_job(job_id)
    return {
        "job_id": job.id,
        "status": job.status.value,
        "message": "Job cancelled",
    }
