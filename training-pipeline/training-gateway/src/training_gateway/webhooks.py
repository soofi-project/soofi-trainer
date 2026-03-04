"""Webhook endpoints for training container callbacks."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException

from training_gateway import db
from training_gateway.models import (
    CompletedPayload,
    FailedPayload,
    PhaseTransitionPayload,
    ProgressPayload,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/job-progress")
async def webhook_job_progress(payload: ProgressPayload) -> dict[str, Any]:
    """Update progress for a specific phase of a training job."""
    try:
        await db.update_job_progress(
            job_id=payload.job_id,
            phase=payload.phase,
            progress=payload.progress,
            metrics=payload.metrics,
        )
    except db.JobNotFoundError:
        raise HTTPException(status_code=404, detail=f"Job '{payload.job_id}' not found")
    except db.JobNotRunningError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    logger.info("Job %s: %s progress=%d%%", payload.job_id, payload.phase, payload.progress)
    return {"status": "ok", "job_id": payload.job_id}


@router.post("/job-phase-transition")
async def webhook_job_phase_transition(payload: PhaseTransitionPayload) -> dict[str, Any]:
    """Transition a training job from one phase to the next."""
    try:
        await db.update_job_phase(
            job_id=payload.job_id,
            from_phase=payload.from_phase,
            to_phase=payload.to_phase,
        )
    except db.JobNotFoundError:
        raise HTTPException(status_code=404, detail=f"Job '{payload.job_id}' not found")
    except db.JobNotRunningError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    logger.info("Job %s: phase %s → %s", payload.job_id, payload.from_phase, payload.to_phase)
    return {"status": "ok", "job_id": payload.job_id}


@router.post("/job-completed")
async def webhook_job_completed(payload: CompletedPayload) -> dict[str, Any]:
    """Mark a training job as completed."""
    try:
        await db.complete_job(job_id=payload.job_id, result=payload.result)
    except db.JobNotFoundError:
        raise HTTPException(status_code=404, detail=f"Job '{payload.job_id}' not found")
    except db.JobNotRunningError as e:
        raise HTTPException(status_code=409, detail=str(e))
    logger.info("Job %s completed", payload.job_id)
    return {"status": "ok", "job_id": payload.job_id}


@router.post("/job-failed")
async def webhook_job_failed(payload: FailedPayload) -> dict[str, Any]:
    """Mark a training job as failed."""
    try:
        await db.fail_job(job_id=payload.job_id, error=payload.error)
    except db.JobNotFoundError:
        raise HTTPException(status_code=404, detail=f"Job '{payload.job_id}' not found")
    except db.JobNotRunningError as e:
        raise HTTPException(status_code=409, detail=str(e))
    logger.error("Job %s failed: %s", payload.job_id, payload.error)
    return {"status": "ok", "job_id": payload.job_id}
