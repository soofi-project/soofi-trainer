"""Webhook endpoints for training container callbacks."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from training_gateway import db
from training_gateway.models import (
    CompletedPayload,
    FailedPayload,
    JobStatus,
    PhaseTransitionPayload,
    ProgressPayload,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/job-progress")
async def webhook_job_progress(payload: ProgressPayload) -> dict:
    """Update progress for a specific phase of a training job."""
    job = await db.get_job(payload.job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job '{payload.job_id}' not found")

    if job.status != JobStatus.running:
        raise HTTPException(
            status_code=400,
            detail=f"Job '{payload.job_id}' is {job.status.value}, not running",
        )

    # Validate phase exists in this job
    phase_names = [p.name for p in job.phases]
    if payload.phase not in phase_names:
        raise HTTPException(
            status_code=400,
            detail=f"Phase '{payload.phase}' not found. Valid: {phase_names}",
        )

    job = await db.update_job_progress(
        job_id=payload.job_id,
        phase=payload.phase,
        progress=payload.progress,
        metrics=payload.metrics,
    )
    logger.info("Job %s: %s progress=%d%%", payload.job_id, payload.phase, payload.progress)
    return {"status": "ok", "job_id": payload.job_id}


@router.post("/job-phase-transition")
async def webhook_job_phase_transition(payload: PhaseTransitionPayload) -> dict:
    """Transition a training job from one phase to the next."""
    job = await db.get_job(payload.job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job '{payload.job_id}' not found")

    if job.status != JobStatus.running:
        raise HTTPException(
            status_code=400,
            detail=f"Job '{payload.job_id}' is {job.status.value}, not running",
        )

    phase_names = [p.name for p in job.phases]
    if payload.from_phase not in phase_names:
        raise HTTPException(
            status_code=400,
            detail=f"Phase '{payload.from_phase}' not found. Valid: {phase_names}",
        )
    if payload.to_phase not in phase_names:
        raise HTTPException(
            status_code=400,
            detail=f"Phase '{payload.to_phase}' not found. Valid: {phase_names}",
        )

    job = await db.update_job_phase(
        job_id=payload.job_id,
        from_phase=payload.from_phase,
        to_phase=payload.to_phase,
    )
    logger.info("Job %s: phase %s → %s", payload.job_id, payload.from_phase, payload.to_phase)
    return {"status": "ok", "job_id": payload.job_id}


@router.post("/job-completed")
async def webhook_job_completed(payload: CompletedPayload) -> dict:
    """Mark a training job as completed."""
    job = await db.get_job(payload.job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job '{payload.job_id}' not found")

    if job.status != JobStatus.running:
        raise HTTPException(
            status_code=400,
            detail=f"Job '{payload.job_id}' is {job.status.value}, not running",
        )

    job = await db.complete_job(job_id=payload.job_id, result=payload.result)
    logger.info("Job %s completed", payload.job_id)
    return {"status": "ok", "job_id": payload.job_id}


@router.post("/job-failed")
async def webhook_job_failed(payload: FailedPayload) -> dict:
    """Mark a training job as failed."""
    job = await db.get_job(payload.job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job '{payload.job_id}' not found")

    if job.status != JobStatus.running:
        raise HTTPException(
            status_code=400,
            detail=f"Job '{payload.job_id}' is {job.status.value}, not running",
        )

    job = await db.fail_job(job_id=payload.job_id, error=payload.error)
    logger.error("Job %s failed: %s", payload.job_id, payload.error)
    return {"status": "ok", "job_id": payload.job_id}
