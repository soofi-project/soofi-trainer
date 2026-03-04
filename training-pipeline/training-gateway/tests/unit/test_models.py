"""Unit tests for Pydantic models and enums."""

import pytest
from pydantic import ValidationError

from training_gateway.models import (
    DEFAULT_PHASES,
    CompletedPayload,
    FailedPayload,
    JobPhase,
    JobResult,
    JobStatus,
    PhaseStatus,
    PhaseTransitionPayload,
    ProgressPayload,
    TrainingMethod,
)


@pytest.mark.unit
class TestEnums:
    def test_job_status_values(self):
        assert {s.value for s in JobStatus} == {
            "queued", "running", "completed", "failed", "cancelled"
        }

    def test_phase_status_values(self):
        assert {s.value for s in PhaseStatus} == {
            "pending", "running", "completed", "failed"
        }

    def test_training_method_values(self):
        assert {m.value for m in TrainingMethod} == {
            "sft", "lora", "qlora", "rag", "distillation",
            "cpt", "instruction", "dpo", "rlhf",
        }
        assert len(TrainingMethod) == 9


@pytest.mark.unit
class TestDefaultPhases:
    def test_all_methods_have_phases(self):
        for method in TrainingMethod:
            assert method in DEFAULT_PHASES

    def test_sft_has_three_phases(self):
        assert DEFAULT_PHASES[TrainingMethod.sft] == [
            "data_preparation", "training", "model_upload"
        ]

    def test_rag_skips_training(self):
        phases = DEFAULT_PHASES[TrainingMethod.rag]
        assert phases == ["data_preparation", "model_upload"]
        assert "training" not in phases

    def test_lora_has_three_phases(self):
        assert len(DEFAULT_PHASES[TrainingMethod.lora]) == 3


@pytest.mark.unit
class TestJobPhase:
    def test_valid_progress(self):
        phase = JobPhase(name="training", progress=50)
        assert phase.progress == 50

    def test_progress_upper_bound(self):
        with pytest.raises(ValidationError):
            JobPhase(name="training", progress=101)

    def test_progress_lower_bound(self):
        with pytest.raises(ValidationError):
            JobPhase(name="training", progress=-1)

    def test_defaults(self):
        phase = JobPhase(name="data_preparation")
        assert phase.status == PhaseStatus.pending
        assert phase.progress == 0
        assert phase.started_at is None


@pytest.mark.unit
class TestJobResult:
    def test_defaults(self):
        result = JobResult()
        assert result.model_ref is None
        assert result.metrics == {}

    def test_with_values(self):
        result = JobResult(model_ref="registry/model:v1", metrics={"loss": 0.23})
        assert result.model_ref == "registry/model:v1"
        assert result.metrics["loss"] == 0.23


@pytest.mark.unit
class TestWebhookPayloads:
    def test_progress_payload_valid(self):
        p = ProgressPayload(job_id="abc", phase="training", progress=42)
        assert p.progress == 42

    def test_progress_payload_bounds(self):
        with pytest.raises(ValidationError):
            ProgressPayload(job_id="abc", phase="training", progress=150)

    def test_phase_transition_payload(self):
        p = PhaseTransitionPayload(
            job_id="abc", from_phase="data_preparation", to_phase="training"
        )
        assert p.from_phase == "data_preparation"

    def test_completed_payload_default_result(self):
        p = CompletedPayload(job_id="abc")
        assert p.result.model_ref is None
        assert p.result.metrics == {}

    def test_failed_payload(self):
        p = FailedPayload(job_id="abc", error="CUDA OOM")
        assert p.error == "CUDA OOM"
