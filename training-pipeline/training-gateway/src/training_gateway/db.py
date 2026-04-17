"""SQLite persistence layer for training jobs."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime, timezone

import aiosqlite
from typing import Any

from training_gateway.models import (
    DEFAULT_PHASES,
    Job,
    JobPhase,
    JobResult,
    JobStatus,
    PhaseStatus,
    TrainingMethod,
)

logger = logging.getLogger(__name__)

DB_PATH = os.getenv("TRAINING_DB_PATH", "./training.db")


class JobNotFoundError(Exception):
    def __init__(self, job_id: str) -> None:
        super().__init__(f"Job '{job_id}' not found")
        self.job_id = job_id


class JobNotRunningError(Exception):
    def __init__(self, job_id: str, actual_status: JobStatus) -> None:
        super().__init__(f"Job '{job_id}' is {actual_status.value}, not running")
        self.job_id = job_id
        self.actual_status = actual_status

_db: aiosqlite.Connection | None = None
_write_lock = asyncio.Lock()


async def get_db() -> aiosqlite.Connection:
    """Get or create the database connection."""
    global _db
    if _db is None:
        db_dir = os.path.dirname(os.path.abspath(DB_PATH))
        os.makedirs(db_dir, exist_ok=True)
        _db = await aiosqlite.connect(DB_PATH)
        _db.row_factory = aiosqlite.Row
        await _db.execute("PRAGMA journal_mode=WAL")
    return _db


async def init_db() -> None:
    """Create tables if they don't exist."""
    db = await get_db()
    await db.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            method TEXT NOT NULL,
            dataset_ref TEXT NOT NULL,
            base_model TEXT NOT NULL,
            config TEXT NOT NULL DEFAULT '{}',
            status TEXT NOT NULL DEFAULT 'queued',
            current_phase TEXT,
            phases TEXT NOT NULL DEFAULT '[]',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            error TEXT,
            result TEXT
        )
    """)
    await db.commit()
    # Migrations: add columns if they don't exist yet
    for column_def in [
        "container_id TEXT",
        "aas_submodel_id TEXT",
        "aas_push_error TEXT",
    ]:
        try:
            await db.execute(f"ALTER TABLE jobs ADD COLUMN {column_def}")
            await db.commit()
        except Exception:
            pass  # Column already exists
    logger.info("Database initialized at %s", DB_PATH)


async def close_db() -> None:
    """Close the database connection."""
    global _db
    if _db is not None:
        await _db.close()
        _db = None


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _serialize_job(job: Job) -> dict[str, Any]:
    """Serialize a Job to a dict for SQLite storage."""
    return {
        "id": job.id,
        "method": job.method.value,
        "dataset_ref": job.dataset_ref,
        "base_model": job.base_model,
        "config": json.dumps(job.config),
        "status": job.status.value,
        "current_phase": job.current_phase,
        "phases": json.dumps([p.model_dump(mode="json") for p in job.phases]),
        "created_at": job.created_at.isoformat(),
        "updated_at": job.updated_at.isoformat(),
        "error": job.error,
        "result": json.dumps(job.result.model_dump()) if job.result else None,
        "container_id": job.container_id,
        "aas_submodel_id": job.aas_submodel_id,
        "aas_push_error": job.aas_push_error,
    }


def _deserialize_job(row: aiosqlite.Row) -> Job:
    """Deserialize a SQLite row to a Job."""
    row_dict = dict(row)
    return Job(
        id=row_dict["id"],
        method=TrainingMethod(row_dict["method"]),
        dataset_ref=row_dict["dataset_ref"],
        base_model=row_dict["base_model"],
        config=json.loads(row_dict["config"]),
        status=JobStatus(row_dict["status"]),
        current_phase=row_dict["current_phase"],
        phases=[JobPhase(**p) for p in json.loads(row_dict["phases"])],
        created_at=datetime.fromisoformat(row_dict["created_at"]),
        updated_at=datetime.fromisoformat(row_dict["updated_at"]),
        error=row_dict["error"],
        result=JobResult(**json.loads(row_dict["result"])) if row_dict["result"] else None,
        container_id=row_dict.get("container_id"),
        aas_submodel_id=row_dict.get("aas_submodel_id"),
        aas_push_error=row_dict.get("aas_push_error"),
    )


async def create_job(
    method: TrainingMethod,
    dataset_ref: str,
    base_model: str,
    config: dict[str, Any] | None = None,
) -> Job:
    """Create a new training job with initial phases."""
    now = _now()
    phase_names = DEFAULT_PHASES[method]
    phases = []
    for i, name in enumerate(phase_names):
        phases.append(
            JobPhase(
                name=name,
                status=PhaseStatus.running if i == 0 else PhaseStatus.pending,
                progress=0,
                started_at=now if i == 0 else None,
            )
        )

    job = Job(
        id=str(uuid.uuid4()),
        method=method,
        dataset_ref=dataset_ref,
        base_model=base_model,
        config=config or {},
        status=JobStatus.running,
        current_phase=phase_names[0],
        phases=phases,
        created_at=now,
        updated_at=now,
    )

    db = await get_db()
    data = _serialize_job(job)
    await db.execute(
        """
        INSERT INTO jobs (id, method, dataset_ref, base_model, config, status,
                          current_phase, phases, created_at, updated_at, error, result,
                          container_id, aas_submodel_id, aas_push_error)
        VALUES (:id, :method, :dataset_ref, :base_model, :config, :status,
                :current_phase, :phases, :created_at, :updated_at, :error, :result,
                :container_id, :aas_submodel_id, :aas_push_error)
        """,
        data,
    )
    await db.commit()
    logger.info("Created job %s (method=%s)", job.id, method.value)
    return job


async def get_job(job_id: str) -> Job | None:
    """Fetch a job by ID."""
    db = await get_db()
    cursor = await db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
    row = await cursor.fetchone()
    if row is None:
        return None
    return _deserialize_job(row)


async def list_jobs(status: JobStatus | None = None) -> list[Job]:
    """List all jobs, optionally filtered by status."""
    db = await get_db()
    if status:
        cursor = await db.execute(
            "SELECT * FROM jobs WHERE status = ? ORDER BY created_at DESC",
            (status.value,),
        )
    else:
        cursor = await db.execute("SELECT * FROM jobs ORDER BY created_at DESC")
    rows = await cursor.fetchall()
    return [_deserialize_job(row) for row in rows]


async def update_job_progress(
    job_id: str,
    phase: str,
    progress: int,
    metrics: dict[str, Any] | None = None,
) -> Job:
    """Update progress for a specific phase."""
    async with _write_lock:
        job = await get_job(job_id)
        if job is None:
            raise JobNotFoundError(job_id)
        if job.status != JobStatus.running:
            raise JobNotRunningError(job_id, job.status)

        phase_names = [p.name for p in job.phases]
        if phase not in phase_names:
            raise ValueError(f"Phase '{phase}' not found. Valid: {phase_names}")

        now = _now()
        for p in job.phases:
            if p.name == phase:
                p.progress = progress
                if metrics:
                    # Store metrics in job config under the phase key
                    job.config.setdefault("phase_metrics", {})[phase] = metrics
                if p.status == PhaseStatus.pending:
                    p.status = PhaseStatus.running
                    p.started_at = now
                break

        job.updated_at = now
        await _save_job(job)
        return job


async def update_job_phase(
    job_id: str,
    from_phase: str,
    to_phase: str,
) -> Job:
    """Transition from one phase to another."""
    async with _write_lock:
        job = await get_job(job_id)
        if job is None:
            raise JobNotFoundError(job_id)
        if job.status != JobStatus.running:
            raise JobNotRunningError(job_id, job.status)

        phase_names = [p.name for p in job.phases]
        if from_phase not in phase_names:
            raise ValueError(f"Phase '{from_phase}' not found. Valid: {phase_names}")
        if to_phase not in phase_names:
            raise ValueError(f"Phase '{to_phase}' not found. Valid: {phase_names}")

        now = _now()
        for p in job.phases:
            if p.name == from_phase:
                p.status = PhaseStatus.completed
                p.progress = 100
                p.completed_at = now
            elif p.name == to_phase:
                p.status = PhaseStatus.running
                p.started_at = now

        job.current_phase = to_phase
        job.updated_at = now
        await _save_job(job)
        logger.info("Job %s: %s → %s", job_id, from_phase, to_phase)
        return job


async def complete_job(job_id: str, result: JobResult | None = None) -> Job:
    """Mark a job as completed."""
    async with _write_lock:
        job = await get_job(job_id)
        if job is None:
            raise JobNotFoundError(job_id)
        if job.status != JobStatus.running:
            raise JobNotRunningError(job_id, job.status)

        now = _now()
        # Mark the last running phase as completed
        for p in job.phases:
            if p.status == PhaseStatus.running:
                p.status = PhaseStatus.completed
                p.progress = 100
                p.completed_at = now

        job.status = JobStatus.completed
        job.result = result
        job.updated_at = now
        await _save_job(job)
        logger.info("Job %s completed", job_id)
        return job


async def fail_job(job_id: str, error: str) -> Job:
    """Mark a job as failed."""
    async with _write_lock:
        job = await get_job(job_id)
        if job is None:
            raise JobNotFoundError(job_id)
        if job.status != JobStatus.running:
            raise JobNotRunningError(job_id, job.status)

        now = _now()
        for p in job.phases:
            if p.status == PhaseStatus.running:
                p.status = PhaseStatus.failed
                p.completed_at = now

        job.status = JobStatus.failed
        job.error = error
        job.updated_at = now
        await _save_job(job)
        logger.error("Job %s failed: %s", job_id, error)
        return job


async def cancel_job(job_id: str) -> Job | None:
    """Mark a job as cancelled."""
    async with _write_lock:
        job = await get_job(job_id)
        if job is None:
            return None

        if job.status in (JobStatus.completed, JobStatus.failed, JobStatus.cancelled):
            return job  # Already in terminal state

        now = _now()
        for p in job.phases:
            if p.status == PhaseStatus.running:
                p.status = PhaseStatus.pending
                p.completed_at = now

        job.status = JobStatus.cancelled
        job.updated_at = now
        await _save_job(job)
        logger.info("Job %s cancelled", job_id)
        return job


async def delete_all_jobs() -> int:
    """Delete all jobs from the database. Returns the number of deleted rows."""
    async with _write_lock:
        conn = await get_db()
        cursor = await conn.execute("SELECT COUNT(*) FROM jobs")
        row = await cursor.fetchone()
        count = row[0] if row else 0
        await conn.execute("DELETE FROM jobs")
        await conn.commit()
        logger.info("Deleted all %d jobs", count)
        return count


async def _save_job(job: Job) -> None:
    """Update an existing job in the database."""
    db = await get_db()
    data = _serialize_job(job)
    await db.execute(
        """
        UPDATE jobs SET
            method = :method, dataset_ref = :dataset_ref, base_model = :base_model,
            config = :config, status = :status, current_phase = :current_phase,
            phases = :phases, updated_at = :updated_at, error = :error, result = :result,
            container_id = :container_id, aas_submodel_id = :aas_submodel_id,
            aas_push_error = :aas_push_error
        WHERE id = :id
        """,
        data,
    )
    await db.commit()


async def update_job_container_id(job_id: str, container_id: str) -> None:
    """Store the container ID for a job."""
    conn = await get_db()
    now = _now()
    await conn.execute(
        "UPDATE jobs SET container_id = ?, updated_at = ? WHERE id = ?",
        (container_id, now.isoformat(), job_id),
    )
    await conn.commit()


async def update_job_aas_info(job_id: str, aas_submodel_id: str) -> None:
    """Store the AAS submodel ID after a successful push."""
    conn = await get_db()
    now = _now()
    await conn.execute(
        "UPDATE jobs SET aas_submodel_id = ?, aas_push_error = NULL, updated_at = ? WHERE id = ?",
        (aas_submodel_id, now.isoformat(), job_id),
    )
    await conn.commit()
    logger.info("Job %s: AAS submodel ID saved (%s)", job_id, aas_submodel_id)


async def update_job_aas_error(job_id: str, error: str) -> None:
    """Store an AAS push error without changing the job status."""
    conn = await get_db()
    now = _now()
    await conn.execute(
        "UPDATE jobs SET aas_push_error = ?, updated_at = ? WHERE id = ?",
        (error, now.isoformat(), job_id),
    )
    await conn.commit()
    logger.error("Job %s: AAS push error saved: %s", job_id, error)
