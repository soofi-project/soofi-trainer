"""Unit tests for the dummy training simulator."""

from __future__ import annotations

import argparse
import sys
from unittest.mock import MagicMock, call, patch

import pytest

# simulate.py lives one level up; make it importable
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

import simulate  # noqa: E402


# ---------------------------------------------------------------------------
# Data / constants
# ---------------------------------------------------------------------------

class TestMethodPhases:
    """Verify the METHOD_PHASES lookup table."""

    EXPECTED_METHODS = {
        "sft", "lora", "qlora", "rag", "distillation",
        "cpt", "instruction", "dpo", "rlhf",
    }

    def test_all_methods_present(self):
        assert set(simulate.METHOD_PHASES.keys()) == self.EXPECTED_METHODS

    @pytest.mark.parametrize("method", EXPECTED_METHODS - {"rag"})
    def test_standard_methods_have_three_phases(self, method):
        phases = simulate.METHOD_PHASES[method]
        assert len(phases) == 3
        names = [p[0] for p in phases]
        assert names == ["data_preparation", "training", "model_upload"]

    def test_rag_skips_training(self):
        names = [p[0] for p in simulate.METHOD_PHASES["rag"]]
        assert "training" not in names
        assert names == ["data_preparation", "model_upload"]

    @pytest.mark.parametrize("method", EXPECTED_METHODS)
    def test_phase_ratios_sum_to_one(self, method):
        total = sum(ratio for _, ratio in simulate.METHOD_PHASES[method])
        assert total == pytest.approx(1.0)


class TestMethodMetrics:
    """Verify the METHOD_METRICS lookup table."""

    def test_all_methods_have_metrics(self):
        for method in simulate.METHOD_PHASES:
            assert method in simulate.METHOD_METRICS


class TestProgressSteps:
    """Verify PROGRESS_STEPS defaults."""

    def test_training_step_is_5(self):
        assert simulate.PROGRESS_STEPS["training"] == 5

    def test_data_preparation_step_is_10(self):
        assert simulate.PROGRESS_STEPS["data_preparation"] == 10

    def test_model_upload_step_is_20(self):
        assert simulate.PROGRESS_STEPS["model_upload"] == 20


# ---------------------------------------------------------------------------
# simulated_loss
# ---------------------------------------------------------------------------

class TestSimulatedLoss:
    """Test the loss-curve generation function."""

    def test_returns_positive(self):
        for progress in range(0, 101, 10):
            loss = simulate.simulated_loss(progress, "sft")
            assert loss >= 0.01

    def test_loss_decreases_overall(self):
        start = simulate.simulated_loss(0, "sft")
        end = simulate.simulated_loss(100, "sft")
        assert start > end

    def test_dpo_lower_than_sft(self):
        """DPO/RLHF applies a 0.8 factor, so on average it should be lower."""
        samples = 200
        sft_avg = sum(simulate.simulated_loss(50, "sft") for _ in range(samples)) / samples
        dpo_avg = sum(simulate.simulated_loss(50, "dpo") for _ in range(samples)) / samples
        assert dpo_avg < sft_avg

    def test_returns_rounded_float(self):
        loss = simulate.simulated_loss(50, "lora")
        # should be rounded to 4 decimal places
        assert loss == round(loss, 4)


# ---------------------------------------------------------------------------
# post_webhook
# ---------------------------------------------------------------------------

class TestPostWebhook:

    @patch("simulate.requests.post")
    def test_success(self, mock_post):
        mock_post.return_value = MagicMock(status_code=200)
        result = simulate.post_webhook("http://gw:8000", "job-progress", {"job_id": "abc"})
        assert result is True
        mock_post.assert_called_once_with(
            "http://gw:8000/job-progress",
            json={"job_id": "abc"},
            timeout=10,
        )

    @patch("simulate.requests.post", side_effect=__import__("requests").ConnectionError("connection refused"))
    def test_failure_returns_false(self, mock_post):
        result = simulate.post_webhook("http://gw:8000", "job-progress", {"job_id": "abc"})
        assert result is False


# ---------------------------------------------------------------------------
# simulate_phase
# ---------------------------------------------------------------------------

class TestSimulatePhase:

    @patch("simulate.time.sleep")
    @patch("simulate.post_webhook")
    def test_sends_correct_number_of_progress_updates(self, mock_webhook, mock_sleep):
        simulate.simulate_phase(
            phase_name="training",
            duration=10.0,
            job_id="test-job-123",
            method="sft",
            webhook_url="http://gw:8000",
        )
        # training step=5 → progress at 5,10,...,100 → 20 calls
        assert mock_webhook.call_count == 20
        # last call should be at 100%
        last_payload = mock_webhook.call_args_list[-1][0][2]
        assert last_payload["progress"] == 100

    @patch("simulate.time.sleep")
    @patch("simulate.post_webhook")
    def test_data_preparation_uses_step_10(self, mock_webhook, mock_sleep):
        simulate.simulate_phase(
            phase_name="data_preparation",
            duration=5.0,
            job_id="test-job-123",
            method="lora",
            webhook_url="http://gw:8000",
        )
        # step=10 → progress at 10,20,...,100 → 10 calls
        assert mock_webhook.call_count == 10

    @patch("simulate.time.sleep")
    @patch("simulate.post_webhook")
    def test_model_upload_uses_step_20(self, mock_webhook, mock_sleep):
        simulate.simulate_phase(
            phase_name="model_upload",
            duration=3.0,
            job_id="test-job-123",
            method="sft",
            webhook_url="http://gw:8000",
        )
        # step=20 → progress at 20,40,60,80,100 → 5 calls
        assert mock_webhook.call_count == 5

    @patch("simulate.time.sleep")
    @patch("simulate.post_webhook")
    def test_max_progress_limits_updates(self, mock_webhook, mock_sleep):
        simulate.simulate_phase(
            phase_name="data_preparation",
            duration=2.0,
            job_id="test-job-123",
            method="sft",
            webhook_url="http://gw:8000",
            max_progress=30,
        )
        # step=10 → progress at 10, 20, 30 → 3 calls
        assert mock_webhook.call_count == 3
        last_payload = mock_webhook.call_args_list[-1][0][2]
        assert last_payload["progress"] == 30

    @patch("simulate.time.sleep")
    @patch("simulate.post_webhook")
    def test_training_phase_includes_loss_metrics(self, mock_webhook, mock_sleep):
        simulate.simulate_phase(
            phase_name="training",
            duration=1.0,
            job_id="test-job-123",
            method="sft",
            webhook_url="http://gw:8000",
        )
        payload = mock_webhook.call_args_list[0][0][2]
        assert "metrics" in payload
        assert "loss" in payload["metrics"]
        assert "epoch" in payload["metrics"]

    @patch("simulate.time.sleep")
    @patch("simulate.post_webhook")
    def test_lora_training_includes_learning_rate(self, mock_webhook, mock_sleep):
        simulate.simulate_phase(
            phase_name="training",
            duration=1.0,
            job_id="test-job-123",
            method="lora",
            webhook_url="http://gw:8000",
        )
        payload = mock_webhook.call_args_list[0][0][2]
        assert "learning_rate" in payload["metrics"]

    @patch("simulate.time.sleep")
    @patch("simulate.post_webhook")
    def test_model_upload_includes_uploaded_mb(self, mock_webhook, mock_sleep):
        simulate.simulate_phase(
            phase_name="model_upload",
            duration=1.0,
            job_id="test-job-123",
            method="sft",
            webhook_url="http://gw:8000",
        )
        payload = mock_webhook.call_args_list[0][0][2]
        assert "uploaded_mb" in payload["metrics"]


# ---------------------------------------------------------------------------
# run_simulation
# ---------------------------------------------------------------------------

class TestRunSimulation:

    @staticmethod
    def _make_args(**overrides) -> argparse.Namespace:
        defaults = dict(
            job_id="test-job-00000000",
            method="sft",
            dataset="test-dataset",
            base_model="llama-3.1-8B",
            duration=1,
            fail_probability=0.0,
            webhook_url="http://gw:8000",
        )
        defaults.update(overrides)
        return argparse.Namespace(**defaults)

    @patch("simulate.time.sleep")
    @patch("simulate.post_webhook")
    def test_successful_run_returns_zero(self, mock_webhook, mock_sleep):
        args = self._make_args()
        rc = simulate.run_simulation(args)
        assert rc == 0

    @patch("simulate.time.sleep")
    @patch("simulate.post_webhook")
    def test_successful_run_sends_completed(self, mock_webhook, mock_sleep):
        args = self._make_args()
        simulate.run_simulation(args)
        endpoints = [c[0][1] for c in mock_webhook.call_args_list]
        assert "job-completed" in endpoints

    @patch("simulate.time.sleep")
    @patch("simulate.post_webhook")
    def test_successful_run_sends_phase_transitions(self, mock_webhook, mock_sleep):
        args = self._make_args(method="sft")
        simulate.run_simulation(args)
        endpoints = [c[0][1] for c in mock_webhook.call_args_list]
        assert endpoints.count("job-phase-transition") == 2  # 3 phases → 2 transitions

    @patch("simulate.time.sleep")
    @patch("simulate.post_webhook")
    def test_rag_has_one_transition(self, mock_webhook, mock_sleep):
        args = self._make_args(method="rag")
        simulate.run_simulation(args)
        endpoints = [c[0][1] for c in mock_webhook.call_args_list]
        assert endpoints.count("job-phase-transition") == 1  # 2 phases → 1 transition

    @patch("simulate.time.sleep")
    @patch("simulate.post_webhook")
    def test_unknown_method_returns_one(self, mock_webhook, mock_sleep):
        args = self._make_args(method="unknown_method")
        rc = simulate.run_simulation(args)
        assert rc == 1

    @patch("simulate.random.random", return_value=0.0)  # always < fail_probability
    @patch("simulate.random.choice", return_value="training")
    @patch("simulate.random.randint", return_value=50)
    @patch("simulate.time.sleep")
    @patch("simulate.post_webhook")
    def test_simulated_failure_returns_one(
        self, mock_webhook, mock_sleep, mock_randint, mock_choice, mock_random
    ):
        args = self._make_args(fail_probability=1.0)
        rc = simulate.run_simulation(args)
        assert rc == 1

    @patch("simulate.random.random", return_value=0.0)
    @patch("simulate.random.choice", return_value="training")
    @patch("simulate.random.randint", return_value=50)
    @patch("simulate.time.sleep")
    @patch("simulate.post_webhook")
    def test_simulated_failure_sends_job_failed(
        self, mock_webhook, mock_sleep, mock_randint, mock_choice, mock_random
    ):
        args = self._make_args(fail_probability=1.0)
        simulate.run_simulation(args)
        endpoints = [c[0][1] for c in mock_webhook.call_args_list]
        assert "job-failed" in endpoints
        assert "job-completed" not in endpoints

    @patch("simulate.time.sleep")
    @patch("simulate.post_webhook")
    def test_completed_payload_contains_model_ref(self, mock_webhook, mock_sleep):
        args = self._make_args(method="lora")
        simulate.run_simulation(args)
        completed_calls = [
            c for c in mock_webhook.call_args_list if c[0][1] == "job-completed"
        ]
        assert len(completed_calls) == 1
        payload = completed_calls[0][0][2]
        assert "result" in payload
        assert payload["result"]["model_ref"].startswith("registry/soofi-lora:")


# ---------------------------------------------------------------------------
# main (CLI argument parsing)
# ---------------------------------------------------------------------------

class TestMain:

    @patch("simulate.run_simulation", return_value=0)
    def test_valid_args(self, mock_run):
        with patch("sys.argv", [
            "simulate.py",
            "--method", "sft",
            "--dataset", "ds1",
            "--base-model", "llama-3.1-8B",
            "--webhook-url", "http://gw:8000",
            "--job-id", "job-123",
        ]):
            rc = simulate.main()
        assert rc == 0
        mock_run.assert_called_once()

    @patch("simulate.run_simulation", return_value=0)
    def test_custom_duration(self, mock_run):
        with patch("sys.argv", [
            "simulate.py",
            "--method", "lora",
            "--dataset", "ds1",
            "--base-model", "llama-3.1-8B",
            "--webhook-url", "http://gw:8000",
            "--job-id", "job-456",
            "--duration", "60",
        ]):
            simulate.main()
        args = mock_run.call_args[0][0]
        assert args.duration == 60

    def test_unknown_method_exits(self):
        with patch("sys.argv", [
            "simulate.py",
            "--method", "bogus",
            "--dataset", "ds1",
            "--base-model", "m",
            "--webhook-url", "http://gw:8000",
            "--job-id", "j1",
        ]):
            with pytest.raises(SystemExit):
                simulate.main()

    def test_invalid_fail_probability_exits(self):
        with patch("sys.argv", [
            "simulate.py",
            "--method", "sft",
            "--dataset", "ds1",
            "--base-model", "m",
            "--webhook-url", "http://gw:8000",
            "--job-id", "j1",
            "--fail-probability", "2.0",
        ]):
            with pytest.raises(SystemExit):
                simulate.main()

    def test_missing_required_arg_exits(self):
        with patch("sys.argv", ["simulate.py", "--method", "sft"]):
            with pytest.raises(SystemExit):
                simulate.main()
