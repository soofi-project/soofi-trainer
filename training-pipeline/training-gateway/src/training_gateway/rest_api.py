"""REST API endpoints for the Training Gateway."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from training_gateway import backends, db
from training_gateway.models import JobStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("")
async def list_jobs(status: str | None = None) -> list[dict]:
    """List all training jobs, optionally filtered by status."""
    status_filter = None
    if status:
        try:
            status_filter = JobStatus(status)
        except ValueError:
            valid = [s.value for s in JobStatus]
            raise HTTPException(400, f"Unknown status '{status}'. Valid: {valid}")

    jobs = await db.list_jobs(status=status_filter)
    return [j.model_dump(mode="json") for j in jobs]


@router.delete("")
async def delete_all_jobs() -> dict:
    """Cancel all active jobs, stop their containers, and delete all jobs from the DB."""
    jobs = await db.list_jobs()
    stopped = 0
    stop_errors: list[str] = []
    for job in jobs:
        if job.status in (JobStatus.running, JobStatus.queued) and job.container_id:
            try:
                await backends.get_backend().stop_container(job.container_id)
                stopped += 1
            except backends.BackendError as e:
                logger.error(
                    "Failed to stop container %s for job %s: %s",
                    job.container_id,
                    job.id,
                    e,
                )
                stop_errors.append(f"job {job.id} (container {job.container_id}): {e}")

    if stop_errors:
        raise HTTPException(
            status_code=500,
            detail=f"Could not stop all containers — DB not cleared to avoid orphans. "
            f"Failures: {'; '.join(stop_errors)}",
        )

    deleted = await db.delete_all_jobs()
    return {"deleted": deleted, "containers_stopped": stopped}


@router.get("/{job_id}")
async def get_job(job_id: str) -> dict:
    """Get a single training job by ID."""
    job = await db.get_job(job_id)
    if job is None:
        raise HTTPException(404, f"Job '{job_id}' not found")
    return job.model_dump(mode="json")


@router.delete("/{job_id}")
async def cancel_job(job_id: str) -> dict:
    """Cancel a running or queued training job."""
    job = await db.get_job(job_id)
    if job is None:
        raise HTTPException(404, f"Job '{job_id}' not found")

    if job.status in (JobStatus.completed, JobStatus.failed, JobStatus.cancelled):
        raise HTTPException(
            409, f"Job '{job_id}' is already {job.status.value} and cannot be cancelled"
        )

    # Stop the container if one is running
    if job.container_id:
        try:
            await backends.get_backend().stop_container(job.container_id)
        except backends.BackendError as e:
            logger.warning(
                "Failed to stop container %s for job %s: %s",
                job.container_id,
                job_id,
                e,
            )

    cancelled_job = await db.cancel_job(job_id)
    if cancelled_job is None:
        raise HTTPException(404, f"Job '{job_id}' not found during cancellation")
    return cancelled_job.model_dump(mode="json")
