"""Integration tests for webhook endpoints."""

import pytest
from httpx import AsyncClient

from training_gateway import db
from training_gateway.models import JobResult, JobStatus, PhaseStatus, TrainingMethod


@pytest.mark.integration
class TestHealthEndpoint:
    @pytest.mark.asyncio
    async def test_health(self, async_client: AsyncClient):
        resp = await async_client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["service"] == "training-gateway"


@pytest.mark.integration
class TestJobProgress:
    @pytest.mark.asyncio
    async def test_valid(self, async_client: AsyncClient):
        job = await db.create_job(TrainingMethod.lora, "ds", "m")
        resp = await async_client.post(
            "/webhooks/job-progress",
            json={"job_id": job.id, "phase": "data_preparation", "progress": 42},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    @pytest.mark.asyncio
    async def test_nonexistent_job(self, async_client: AsyncClient):
        resp = await async_client.post(
            "/webhooks/job-progress",
            json={"job_id": "nonexistent", "phase": "training", "progress": 50},
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_invalid_phase(self, async_client: AsyncClient):
        job = await db.create_job(TrainingMethod.lora, "ds", "m")
        resp = await async_client.post(
            "/webhooks/job-progress",
            json={"job_id": job.id, "phase": "nonexistent_phase", "progress": 50},
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_not_running(self, async_client: AsyncClient):
        job = await db.create_job(TrainingMethod.lora, "ds", "m")
        await db.complete_job(job.id, JobResult(model_ref="m:v1"))
        resp = await async_client.post(
            "/webhooks/job-progress",
            json={"job_id": job.id, "phase": "data_preparation", "progress": 50},
        )
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_missing_field_422(self, async_client: AsyncClient):
        resp = await async_client.post(
            "/webhooks/job-progress",
            json={"job_id": "abc", "phase": "training"},  # missing progress
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_updates_db(self, async_client: AsyncClient):
        job = await db.create_job(TrainingMethod.lora, "ds", "m")
        await async_client.post(
            "/webhooks/job-progress",
            json={
                "job_id": job.id,
                "phase": "data_preparation",
                "progress": 75,
                "metrics": {"files": 100},
            },
        )
        updated = await db.get_job(job.id)
        phase = next(p for p in updated.phases if p.name == "data_preparation")
        assert phase.progress == 75


@pytest.mark.integration
class TestPhaseTransition:
    @pytest.mark.asyncio
    async def test_valid(self, async_client: AsyncClient):
        job = await db.create_job(TrainingMethod.lora, "ds", "m")
        resp = await async_client.post(
            "/webhooks/job-phase-transition",
            json={
                "job_id": job.id,
                "from_phase": "data_preparation",
                "to_phase": "training",
            },
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_invalid_phase(self, async_client: AsyncClient):
        job = await db.create_job(TrainingMethod.lora, "ds", "m")
        resp = await async_client.post(
            "/webhooks/job-phase-transition",
            json={
                "job_id": job.id,
                "from_phase": "invalid",
                "to_phase": "training",
            },
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_updates_db(self, async_client: AsyncClient):
        job = await db.create_job(TrainingMethod.lora, "ds", "m")
        await async_client.post(
            "/webhooks/job-phase-transition",
            json={
                "job_id": job.id,
                "from_phase": "data_preparation",
                "to_phase": "training",
            },
        )
        updated = await db.get_job(job.id)
        assert updated.current_phase == "training"
        dp = next(p for p in updated.phases if p.name == "data_preparation")
        assert dp.status == PhaseStatus.completed


@pytest.mark.integration
class TestJobCompleted:
    @pytest.mark.asyncio
    async def test_valid(self, async_client: AsyncClient):
        job = await db.create_job(TrainingMethod.lora, "ds", "m")
        resp = await async_client.post(
            "/webhooks/job-completed",
            json={
                "job_id": job.id,
                "result": {"model_ref": "registry/model:v1", "metrics": {"loss": 0.2}},
            },
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_updates_status(self, async_client: AsyncClient):
        job = await db.create_job(TrainingMethod.lora, "ds", "m")
        await async_client.post(
            "/webhooks/job-completed",
            json={"job_id": job.id, "result": {"model_ref": "m:v1"}},
        )
        updated = await db.get_job(job.id)
        assert updated.status == JobStatus.completed

    @pytest.mark.asyncio
    async def test_nonexistent_job(self, async_client: AsyncClient):
        resp = await async_client.post(
            "/webhooks/job-completed",
            json={"job_id": "nonexistent", "result": {"model_ref": "m:v1"}},
        )
        assert resp.status_code == 404


@pytest.mark.integration
class TestJobFailed:
    @pytest.mark.asyncio
    async def test_valid(self, async_client: AsyncClient):
        job = await db.create_job(TrainingMethod.sft, "ds", "m")
        resp = await async_client.post(
            "/webhooks/job-failed",
            json={"job_id": job.id, "error": "CUDA OOM"},
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_updates_status_and_error(self, async_client: AsyncClient):
        job = await db.create_job(TrainingMethod.sft, "ds", "m")
        await async_client.post(
            "/webhooks/job-failed",
            json={"job_id": job.id, "error": "CUDA OOM at epoch 3"},
        )
        updated = await db.get_job(job.id)
        assert updated.status == JobStatus.failed
        assert updated.error == "CUDA OOM at epoch 3"

    @pytest.mark.asyncio
    async def test_nonexistent_job(self, async_client: AsyncClient):
        resp = await async_client.post(
            "/webhooks/job-failed",
            json={"job_id": "nonexistent", "error": "fail"},
        )
        assert resp.status_code == 404
