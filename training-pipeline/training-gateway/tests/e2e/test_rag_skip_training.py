"""E2E test: RAG job skips the training phase (only 2 phases)."""

import pytest
from httpx import AsyncClient

from training_gateway import mcp_tools

start_training_job = mcp_tools.start_training_job.fn
get_job_status = mcp_tools.get_job_status.fn


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_rag_skip_training(async_client: AsyncClient):
    """Create RAG job → 2 phases only → complete → verify no training phase."""
    # 1. Create RAG job
    result = await start_training_job(
        method="rag",
        dataset_ref="s3://datasets/knowledge.txt",
        base_model="sentence-transformers/all-MiniLM-L6-v2",
    )
    job_id = result["job_id"]
    assert result["status"] == "running"
    assert result["phases"] == ["data_preparation", "model_upload"]
    assert "training" not in result["phases"]

    # 2. data_preparation (indexing)
    for pct in (25, 50, 75, 100):
        resp = await async_client.post(
            "/webhooks/job-progress",
            json={
                "job_id": job_id,
                "phase": "data_preparation",
                "progress": pct,
                "metrics": {"step": "chunking" if pct < 50 else "indexing"},
            },
        )
        assert resp.status_code == 200

    # Transition directly → model_upload
    resp = await async_client.post(
        "/webhooks/job-phase-transition",
        json={"job_id": job_id, "from_phase": "data_preparation", "to_phase": "model_upload"},
    )
    assert resp.status_code == 200

    # 3. model_upload
    for pct in (50, 100):
        resp = await async_client.post(
            "/webhooks/job-progress",
            json={"job_id": job_id, "phase": "model_upload", "progress": pct},
        )
        assert resp.status_code == 200

    # 4. Complete
    resp = await async_client.post(
        "/webhooks/job-completed",
        json={
            "job_id": job_id,
            "result": {
                "model_ref": f"registry/soofi-rag:{job_id[:8]}",
                "metrics": {"index_type": "HNSW", "chunks": 1000},
            },
        },
    )
    assert resp.status_code == 200

    # 5. Verify
    final = await get_job_status(job_id)
    assert final["status"] == "completed"
    assert len(final["phases"]) == 2

    phase_names = [p["name"] for p in final["phases"]]
    assert "training" not in phase_names
    assert "data_preparation" in phase_names
    assert "model_upload" in phase_names

    for phase in final["phases"]:
        assert phase["status"] == "completed"
        assert phase["progress"] == 100
