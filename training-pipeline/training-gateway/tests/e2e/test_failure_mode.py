"""E2E test: SFT training failure during training phase."""

import pytest
from httpx import AsyncClient

from training_gateway import mcp_tools

start_training_job = mcp_tools.start_training_job.fn
get_job_status = mcp_tools.get_job_status.fn


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_sft_failure_during_training(async_client: AsyncClient):
    """Complete data_preparation → partial training → fail → verify state."""
    # 1. Create SFT job
    result = await start_training_job(
        method="sft",
        dataset_ref="s3://datasets/large.jsonl",
        base_model="meta-llama/Llama-3.1-8B",
    )
    job_id = result["job_id"]

    # 2. Complete data_preparation
    for pct in (50, 100):
        await async_client.post(
            "/webhooks/job-progress",
            json={"job_id": job_id, "phase": "data_preparation", "progress": pct},
        )

    await async_client.post(
        "/webhooks/job-phase-transition",
        json={"job_id": job_id, "from_phase": "data_preparation", "to_phase": "training"},
    )

    # 3. Partial training progress — stop at 45%
    for pct in (10, 25, 45):
        await async_client.post(
            "/webhooks/job-progress",
            json={
                "job_id": job_id,
                "phase": "training",
                "progress": pct,
                "metrics": {"loss": round(2.5 - pct * 0.01, 2)},
            },
        )

    # 4. Trigger failure
    resp = await async_client.post(
        "/webhooks/job-failed",
        json={"job_id": job_id, "error": "CUDA out of memory at epoch 2"},
    )
    assert resp.status_code == 200

    # 5. Verify final state
    final = await get_job_status(job_id)

    assert final["status"] == "failed"
    assert final["error"] == "CUDA out of memory at epoch 2"
    assert final["result"] is None

    phases = {p["name"]: p for p in final["phases"]}

    # data_preparation was completed before the failure
    assert phases["data_preparation"]["status"] == "completed"
    assert phases["data_preparation"]["progress"] == 100

    # training failed at 45%
    assert phases["training"]["status"] == "failed"
    assert phases["training"]["progress"] == 45

    # model_upload was never reached
    assert phases["model_upload"]["status"] == "pending"
    assert phases["model_upload"]["progress"] == 0
