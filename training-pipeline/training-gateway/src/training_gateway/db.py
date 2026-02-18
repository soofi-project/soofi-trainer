"""SQLite persistence layer for training jobs."""

from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timezone

import aiosqlite

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

_db: aiosqlite.Connection | None = None


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
    # Add container_id column if it doesn't exist (migration for existing DBs)
    try:
        await db.execute("ALTER TABLE jobs ADD COLUMN container_id TEXT")
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


def _serialize_job(job: Job) -> dict:
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
    }


def _deserialize_job(row: aiosqlite.Row) -> Job:
    """Deserialize a SQLite row to a Job."""
    return Job(
        id=row["id"],
        method=TrainingMethod(row["method"]),
        dataset_ref=row["dataset_ref"],
        base_model=row["base_model"],
        config=json.loads(row["config"]),
        status=JobStatus(row["status"]),
        current_phase=row["current_phase"],
        phases=[JobPhase(**p) for p in json.loads(row["phases"])],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
        error=row["error"],
        result=JobResult(**json.loads(row["result"])) if row["result"] else None,
        container_id=row["container_id"],
    )


async def create_job(
    method: TrainingMethod,
    dataset_ref: str,
    base_model: str,
    config: dict | None = None,
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
                          container_id)
        VALUES (:id, :method, :dataset_ref, :base_model, :config, :status,
                :current_phase, :phases, :created_at, :updated_at, :error, :result,
                :container_id)
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
    metrics: dict | None = None,
) -> Job | None:
    """Update progress for a specific phase."""
    job = await get_job(job_id)
    if job is None:
        return None

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
) -> Job | None:
    """Transition from one phase to another."""
    job = await get_job(job_id)
    if job is None:
        return None

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


async def complete_job(job_id: str, result: JobResult | None = None) -> Job | None:
    """Mark a job as completed."""
    job = await get_job(job_id)
    if job is None:
        return None

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


async def fail_job(job_id: str, error: str) -> Job | None:
    """Mark a job as failed."""
    job = await get_job(job_id)
    if job is None:
        return None

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
            container_id = :container_id
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
