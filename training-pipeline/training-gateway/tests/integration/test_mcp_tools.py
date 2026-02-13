"""Integration tests for MCP tool functions."""

import pytest

from training_gateway import db
from training_gateway import mcp_tools
from training_gateway.models import JobResult, TrainingMethod

# @mcp.tool() wraps functions in FunctionTool objects; access the original via .fn
start_training_job = mcp_tools.start_training_job.fn
get_job_status = mcp_tools.get_job_status.fn
list_training_jobs = mcp_tools.list_training_jobs.fn
cancel_training_job = mcp_tools.cancel_training_job.fn


@pytest.mark.integration
class TestStartTrainingJob:
    @pytest.mark.asyncio
    async def test_lora(self, init_db):
        result = await start_training_job("lora", "ds.jsonl", "llama-3.1-8B")
        assert "job_id" in result
        assert result["method"] == "lora"
        assert result["status"] == "running"
        assert result["current_phase"] == "data_preparation"
        assert result["phases"] == ["data_preparation", "training", "model_upload"]

    @pytest.mark.asyncio
    async def test_invalid_method(self, init_db):
        result = await start_training_job("invalid", "ds", "m")
        assert "error" in result
        assert "Unknown method" in result["error"]

    @pytest.mark.asyncio
    async def test_with_config(self, init_db):
        result = await start_training_job(
            "lora", "ds", "m", config={"rank": 16, "alpha": 32}
        )
        job = await db.get_job(result["job_id"])
        assert job.config["rank"] == 16
        assert job.config["alpha"] == 32

    @pytest.mark.asyncio
    async def test_rag_phases(self, init_db):
        result = await start_training_job("rag", "docs/", "n/a")
        assert result["phases"] == ["data_preparation", "model_upload"]


@pytest.mark.integration
class TestGetJobStatus:
    @pytest.mark.asyncio
    async def test_existing(self, init_db):
        job = await db.create_job(TrainingMethod.lora, "ds", "m")
        result = await get_job_status(job.id)
        assert result["id"] == job.id
        assert result["method"] == "lora"
        assert result["status"] == "running"

    @pytest.mark.asyncio
    async def test_nonexistent(self, init_db):
        result = await get_job_status("nonexistent")
        assert "error" in result
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_phases_structure(self, init_db):
        job = await db.create_job(TrainingMethod.lora, "ds", "m")
        result = await get_job_status(job.id)
        assert len(result["phases"]) == 3
        assert result["phases"][0]["name"] == "data_preparation"
        assert result["phases"][0]["status"] == "running"
        assert result["phases"][0]["progress"] == 0


@pytest.mark.integration
class TestListTrainingJobs:
    @pytest.mark.asyncio
    async def test_empty(self, init_db):
        result = await list_training_jobs()
        assert result["jobs"] == []
        assert result["total"] == 0

    @pytest.mark.asyncio
    async def test_multiple(self, init_db):
        await db.create_job(TrainingMethod.lora, "ds1", "m1")
        await db.create_job(TrainingMethod.sft, "ds2", "m2")
        result = await list_training_jobs()
        assert result["total"] == 2

    @pytest.mark.asyncio
    async def test_filter_by_status(self, init_db):
        job1 = await db.create_job(TrainingMethod.lora, "ds1", "m1")
        await db.create_job(TrainingMethod.sft, "ds2", "m2")
        await db.complete_job(job1.id, JobResult(model_ref="m:v1"))

        running = await list_training_jobs(status="running")
        assert running["total"] == 1

        completed = await list_training_jobs(status="completed")
        assert completed["total"] == 1
        assert completed["jobs"][0]["id"] == job1.id


@pytest.mark.integration
class TestCancelTrainingJob:
    @pytest.mark.asyncio
    async def test_cancel_running(self, init_db):
        job = await db.create_job(TrainingMethod.lora, "ds", "m")
        result = await cancel_training_job(job.id)
        assert result["status"] == "cancelled"
        assert result["job_id"] == job.id

    @pytest.mark.asyncio
    async def test_cancel_completed_fails(self, init_db):
        job = await db.create_job(TrainingMethod.lora, "ds", "m")
        await db.complete_job(job.id, JobResult(model_ref="m:v1"))
        result = await cancel_training_job(job.id)
        assert "error" in result
        assert "cannot be cancelled" in result["error"]

    @pytest.mark.asyncio
    async def test_cancel_nonexistent(self, init_db):
        result = await cancel_training_job("nonexistent")
        assert "error" in result
        assert "not found" in result["error"]
