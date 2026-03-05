"""Dummy training simulator — simulates training phases and reports progress via webhooks."""

from __future__ import annotations

import argparse
import logging
import math
import random
import sys
import time

import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("simulate")

# Phase duration ratios per method (fraction of total duration)
METHOD_PHASES: dict[str, list[tuple[str, float]]] = {
    # Standard 3-phase methods
    "sft":          [("data_preparation", 0.20), ("training", 0.65), ("model_upload", 0.15)],
    "lora":         [("data_preparation", 0.20), ("training", 0.65), ("model_upload", 0.15)],
    "qlora":        [("data_preparation", 0.20), ("training", 0.65), ("model_upload", 0.15)],
    "distillation": [("data_preparation", 0.20), ("training", 0.65), ("model_upload", 0.15)],
    "cpt":          [("data_preparation", 0.20), ("training", 0.65), ("model_upload", 0.15)],
    "instruction":  [("data_preparation", 0.20), ("training", 0.65), ("model_upload", 0.15)],
    "dpo":          [("data_preparation", 0.20), ("training", 0.65), ("model_upload", 0.15)],
    "rlhf":         [("data_preparation", 0.20), ("training", 0.65), ("model_upload", 0.15)],
    # RAG: no training phase
    "rag":          [("data_preparation", 0.60), ("model_upload", 0.40)],
}

# Progress reporting intervals (percentage step) per phase
PROGRESS_STEPS: dict[str, int] = {
    "data_preparation": 10,
    "training": 5,
    "model_upload": 20,
}

# Method-specific simulated metrics
METHOD_METRICS: dict[str, dict] = {
    "sft": {"trainable_params": "7B", "gpu_memory_gb": 40.2},
    "lora": {"trainable_params": "18.7M", "rank": 16, "gpu_memory_gb": 12.4},
    "qlora": {"trainable_params": "18.7M", "rank": 16, "bits": 4, "gpu_memory_gb": 7.8},
    "rag": {"index_type": "HNSW", "chunk_size": 512, "overlap": 64},
    "distillation": {"teacher_model": "llama-3.1-70B", "student_model": "llama-3.1-8B"},
    "cpt": {"trainable_params": "7B", "gpu_memory_gb": 38.5},
    "instruction": {"trainable_params": "7B", "gpu_memory_gb": 40.2},
    "dpo": {"trainable_params": "7B", "gpu_memory_gb": 42.0, "beta": 0.1},
    "rlhf": {"trainable_params": "7B", "gpu_memory_gb": 48.0, "ppo_epochs": 4},
}


def post_webhook(webhook_url: str, endpoint: str, payload: dict) -> bool:
    """Send a webhook POST request. Returns True on success."""
    url = f"{webhook_url}/{endpoint}"
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        logger.info("  POST %s → %d", url, resp.status_code)
        return True
    except requests.RequestException as e:
        logger.error("  POST %s failed: %s", url, e)
        return False


def simulated_loss(progress: int, method: str) -> float:
    """Generate a realistic-looking training loss curve."""
    t = progress / 100.0
    base = 2.5 * math.exp(-3.0 * t) + 0.3
    noise = random.gauss(0, 0.02)
    if method in ("dpo", "rlhf"):
        base *= 0.8
    return round(max(0.01, base + noise), 4)


def simulate_phase(
    phase_name: str,
    duration: float,
    job_id: str,
    method: str,
    webhook_url: str,
    max_progress: int = 100,
) -> None:
    """Simulate a single training phase with progress updates."""
    step = PROGRESS_STEPS.get(phase_name, 10)
    intervals = list(range(step, max_progress + 1, step))
    if not intervals or intervals[-1] != max_progress:
        intervals.append(max_progress)

    time_per_interval = duration / len(intervals) if intervals else 0

    for progress in intervals:
        time.sleep(time_per_interval)

        metrics: dict | None = None
        if phase_name == "training":
            metrics = {
                "loss": simulated_loss(progress, method),
                "epoch": round(progress / 100 * 3, 1),
            }
            if method in ("lora", "qlora"):
                metrics["learning_rate"] = round(2e-4 * (1 - progress / 100 * 0.9), 6)
        elif phase_name == "data_preparation":
            if progress <= 30:
                metrics = {"step": "validation"}
            elif progress <= 60:
                metrics = {"step": "formatting"}
            else:
                metrics = {"step": "splitting"}
            if method == "qlora" and progress <= 20:
                metrics["step"] = "quantization"
        elif phase_name == "model_upload":
            metrics = {"uploaded_mb": round(progress / 100 * 4500, 1)}

        payload = {"job_id": job_id, "phase": phase_name, "progress": progress}
        if metrics:
            payload["metrics"] = metrics

        logger.info("[%s] %s: %d%%", job_id[:8], phase_name, progress)
        post_webhook(webhook_url, "job-progress", payload)


def run_simulation(args: argparse.Namespace) -> int:
    """Run the full training simulation. Returns exit code."""
    logger.info("=" * 60)
    logger.info("Dummy Training Simulator")
    logger.info("  Job ID:      %s", args.job_id)
    logger.info("  Method:      %s", args.method)
    logger.info("  Dataset:     %s", args.dataset)
    logger.info("  Base Model:  %s", args.base_model)
    logger.info("  Duration:    %ds", args.duration)
    logger.info("  Fail Prob:   %.1f%%", args.fail_probability * 100)
    logger.info("  Webhook URL: %s", args.webhook_url)
    logger.info("=" * 60)

    phases = METHOD_PHASES.get(args.method)
    if phases is None:
        logger.error("Unknown method: %s", args.method)
        return 1

    # Determine if this run should simulate a failure
    should_fail = random.random() < args.fail_probability
    fail_at_phase = random.choice([p[0] for p in phases]) if should_fail else None
    fail_at_progress = random.randint(10, 80) if should_fail else None

    for i, (phase_name, ratio) in enumerate(phases):
        phase_duration = args.duration * ratio

        # Phase transition webhook (except for the first phase — it's already running)
        if i > 0:
            prev_phase = phases[i - 1][0]
            post_webhook(
                args.webhook_url,
                "job-phase-transition",
                {"job_id": args.job_id, "from_phase": prev_phase, "to_phase": phase_name},
            )

        logger.info("--- Phase: %s (%.0fs) ---", phase_name, phase_duration)

        # Check for simulated failure
        if should_fail and phase_name == fail_at_phase:
            # Run partial progress up to the failure point
            partial_duration = phase_duration * (fail_at_progress / 100)
            simulate_phase(
                phase_name=phase_name,
                duration=partial_duration,
                job_id=args.job_id,
                method=args.method,
                webhook_url=args.webhook_url,
                max_progress=fail_at_progress,
            )
            error_msg = (
                f"Simulated failure in {phase_name} at {fail_at_progress}%: "
                f"CUDA out of memory (simulated)"
            )
            logger.error(error_msg)
            post_webhook(
                args.webhook_url,
                "job-failed",
                {"job_id": args.job_id, "error": error_msg},
            )
            return 1

        simulate_phase(
            phase_name=phase_name,
            duration=phase_duration,
            job_id=args.job_id,
            method=args.method,
            webhook_url=args.webhook_url,
        )

    # Job completed
    method_info = METHOD_METRICS.get(args.method, {})
    result = {
        "model_ref": f"registry/soofi-{args.method}:{args.job_id[:8]}",
        "metrics": {
            "total_duration_s": args.duration,
            "method": args.method,
            **method_info,
        },
    }
    post_webhook(args.webhook_url, "job-completed", {"job_id": args.job_id, "result": result})

    logger.info("=" * 60)
    logger.info("Simulation complete!")
    logger.info("=" * 60)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Dummy training simulator")
    parser.add_argument("--method", required=True, help="Training method (sft, lora, qlora, rag, ...)")
    parser.add_argument("--dataset", required=True, help="Dataset reference")
    parser.add_argument("--base-model", required=True, help="Base model name")
    parser.add_argument("--webhook-url", required=True, help="Gateway webhook base URL")
    parser.add_argument("--job-id", required=True, help="Job ID (assigned by gateway)")
    parser.add_argument("--duration", type=int, default=120, help="Total simulation duration in seconds")
    parser.add_argument("--fail-probability", type=float, default=0.0, help="Chance of simulated failure (0.0-1.0)")

    args = parser.parse_args()

    if args.method not in METHOD_PHASES:
        parser.error(f"Unknown method: {args.method}. Valid: {list(METHOD_PHASES.keys())}")

    if not 0.0 <= args.fail_probability <= 1.0:
        parser.error("--fail-probability must be between 0.0 and 1.0")

    return run_simulation(args)


if __name__ == "__main__":
    sys.exit(main())
