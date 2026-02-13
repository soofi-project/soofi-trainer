"""Unit tests for database layer."""

import pytest

from training_gateway import db
from training_gateway.models import JobResult, JobStatus, PhaseStatus, TrainingMethod


@pytest.mark.unit
class TestCreateJob:
    @pytest.mark.asyncio
    async def test_lora_creates_three_phases(self, init_db):
        job = await db.create_job(TrainingMethod.lora, "ds.jsonl", "llama-3.1-8B")
        assert job.id is not None
        assert job.method == TrainingMethod.lora
        assert job.status == JobStatus.running
        assert len(job.phases) == 3
        assert [p.name for p in job.phases] == [
            "data_preparation", "training", "model_upload"
        ]

    @pytest.mark.asyncio
    async def test_rag_creates_two_phases(self, init_db):
        job = await db.create_job(TrainingMethod.rag, "docs/", "n/a")
        assert len(job.phases) == 2
        assert "training" not in [p.name for p in job.phases]

    @pytest.mark.asyncio
    async def test_first_phase_is_running(self, init_db):
        job = await db.create_job(TrainingMethod.sft, "ds", "model")
        assert job.phases[0].status == PhaseStatus.running
        assert job.phases[0].started_at is not None
        assert job.phases[1].status == PhaseStatus.pending

    @pytest.mark.asyncio
    async def test_with_config(self, init_db):
        job = await db.create_job(
            TrainingMethod.lora, "ds", "model", config={"rank": 16}
        )
        assert job.config["rank"] == 16


@pytest.mark.unit
class TestGetJob:
    @pytest.mark.asyncio
    async def test_existing(self, init_db):
        created = await db.create_job(TrainingMethod.sft, "ds", "model")
        fetched = await db.get_job(created.id)
        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.method == TrainingMethod.sft

    @pytest.mark.asyncio
    async def test_nonexistent(self, init_db):
        assert await db.get_job("nonexistent") is None


@pytest.mark.unit
class TestListJobs:
    @pytest.mark.asyncio
    async def test_empty(self, init_db):
        assert await db.list_jobs() == []

    @pytest.mark.asyncio
    async def test_multiple(self, init_db):
        await db.create_job(TrainingMethod.lora, "ds1", "m1")
        await db.create_job(TrainingMethod.sft, "ds2", "m2")
        assert len(await db.list_jobs()) == 2

    @pytest.mark.asyncio
    async def test_filter_by_status(self, init_db):
        job1 = await db.create_job(TrainingMethod.lora, "ds1", "m1")
        await db.create_job(TrainingMethod.sft, "ds2", "m2")
        await db.complete_job(job1.id, JobResult(model_ref="m:v1"))

        running = await db.list_jobs(status=JobStatus.running)
        assert len(running) == 1

        completed = await db.list_jobs(status=JobStatus.completed)
        assert len(completed) == 1
        assert completed[0].id == job1.id


@pytest.mark.unit
class TestUpdateProgress:
    @pytest.mark.asyncio
    async def test_updates_progress(self, init_db):
        job = await db.create_job(TrainingMethod.lora, "ds", "m")
        updated = await db.update_job_progress(job.id, "data_preparation", 75)
        phase = next(p for p in updated.phases if p.name == "data_preparation")
        assert phase.progress == 75

    @pytest.mark.asyncio
    async def test_with_metrics(self, init_db):
        job = await db.create_job(TrainingMethod.lora, "ds", "m")
        updated = await db.update_job_progress(
            job.id, "data_preparation", 50, metrics={"files": 42}
        )
        assert updated.config["phase_metrics"]["data_preparation"]["files"] == 42


@pytest.mark.unit
class TestPhaseTransition:
    @pytest.mark.asyncio
    async def test_transition(self, init_db):
        job = await db.create_job(TrainingMethod.lora, "ds", "m")
        updated = await db.update_job_phase(job.id, "data_preparation", "training")

        assert updated.current_phase == "training"
        dp = next(p for p in updated.phases if p.name == "data_preparation")
        assert dp.status == PhaseStatus.completed
        assert dp.progress == 100
        tr = next(p for p in updated.phases if p.name == "training")
        assert tr.status == PhaseStatus.running


@pytest.mark.unit
class TestCompleteJob:
    @pytest.mark.asyncio
    async def test_complete(self, init_db):
        job = await db.create_job(TrainingMethod.lora, "ds", "m")
        result = JobResult(model_ref="registry/lora:v1", metrics={"loss": 0.23})
        completed = await db.complete_job(job.id, result)

        assert completed.status == JobStatus.completed
        assert completed.result.model_ref == "registry/lora:v1"


@pytest.mark.unit
class TestFailJob:
    @pytest.mark.asyncio
    async def test_fail(self, init_db):
        job = await db.create_job(TrainingMethod.sft, "ds", "m")
        failed = await db.fail_job(job.id, "CUDA OOM")

        assert failed.status == JobStatus.failed
        assert failed.error == "CUDA OOM"
        assert failed.phases[0].status == PhaseStatus.failed


@pytest.mark.unit
class TestCancelJob:
    @pytest.mark.asyncio
    async def test_cancel_running(self, init_db):
        job = await db.create_job(TrainingMethod.lora, "ds", "m")
        cancelled = await db.cancel_job(job.id)
        assert cancelled.status == JobStatus.cancelled

    @pytest.mark.asyncio
    async def test_cancel_terminal_is_noop(self, init_db):
        job = await db.create_job(TrainingMethod.lora, "ds", "m")
        await db.complete_job(job.id, JobResult(model_ref="m:v1"))
        result = await db.cancel_job(job.id)
        assert result.status == JobStatus.completed


@pytest.mark.unit
class TestPersistence:
    @pytest.mark.asyncio
    async def test_survives_reconnect(self, init_db):
        job = await db.create_job(TrainingMethod.lora, "ds", "m")
        job_id = job.id

        await db.close_db()
        db._db = None
        await db.init_db()

        fetched = await db.get_job(job_id)
        assert fetched is not None
        assert fetched.method == TrainingMethod.lora
