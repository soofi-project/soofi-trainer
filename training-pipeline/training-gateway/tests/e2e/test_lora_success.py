"""E2E test: LoRA full success path (3 phases)."""

import pytest
from httpx import AsyncClient

from training_gateway import mcp_tools

start_training_job = mcp_tools.start_training_job.fn
get_job_status = mcp_tools.get_job_status.fn


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_lora_success_path(async_client: AsyncClient):
    """Create LoRA job → progress all 3 phases → complete → verify final state."""
    # 1. Create job
    result = await start_training_job(
        method="lora",
        dataset_ref="s3://datasets/sample.jsonl",
        base_model="meta-llama/Llama-3.1-8B",
        config={"rank": 16},
    )
    job_id = result["job_id"]
    assert result["status"] == "running"
    assert result["phases"] == ["data_preparation", "training", "model_upload"]

    # 2. data_preparation phase
    for pct in (10, 50, 100):
        resp = await async_client.post(
            "/webhooks/job-progress",
            json={"job_id": job_id, "phase": "data_preparation", "progress": pct},
        )
        assert resp.status_code == 200

    # Transition → training
    resp = await async_client.post(
        "/webhooks/job-phase-transition",
        json={"job_id": job_id, "from_phase": "data_preparation", "to_phase": "training"},
    )
    assert resp.status_code == 200

    # 3. training phase
    for pct in (5, 25, 50, 75, 100):
        resp = await async_client.post(
            "/webhooks/job-progress",
            json={
                "job_id": job_id,
                "phase": "training",
                "progress": pct,
                "metrics": {"loss": round(2.5 * (1 - pct / 100), 2), "epoch": pct // 33},
            },
        )
        assert resp.status_code == 200

    # Transition → model_upload
    resp = await async_client.post(
        "/webhooks/job-phase-transition",
        json={"job_id": job_id, "from_phase": "training", "to_phase": "model_upload"},
    )
    assert resp.status_code == 200

    # 4. model_upload phase
    for pct in (20, 60, 100):
        resp = await async_client.post(
            "/webhooks/job-progress",
            json={"job_id": job_id, "phase": "model_upload", "progress": pct},
        )
        assert resp.status_code == 200

    # 5. Mark completed
    resp = await async_client.post(
        "/webhooks/job-completed",
        json={
            "job_id": job_id,
            "result": {
                "model_ref": f"registry/soofi-lora:{job_id[:8]}",
                "metrics": {"trainable_params": "18.7M", "rank": 16},
            },
        },
    )
    assert resp.status_code == 200

    # 6. Verify final state
    final = await get_job_status(job_id)
    assert final["status"] == "completed"
    assert len(final["phases"]) == 3

    for phase in final["phases"]:
        assert phase["status"] == "completed"
        assert phase["progress"] == 100

    assert final["result"] is not None
    assert "registry/soofi-lora" in final["result"]["model_ref"]
    assert final["result"]["metrics"]["trainable_params"] == "18.7M"
