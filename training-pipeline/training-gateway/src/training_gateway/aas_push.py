"""AAS submodel push for trained models (IDTA 02060 AI Model Nameplate)."""

from __future__ import annotations

import base64
import logging
import os
import uuid
from typing import Any

import httpx

from training_gateway.models import Job

logger = logging.getLogger(__name__)

_KIND_OF_LEARNING_LABELS: dict[str, str] = {
    "lora": "LoRA fine-tuning",
    "qlora": "QLoRA fine-tuning",
    "sft": "Supervised fine-tuning",
    "dpo": "DPO fine-tuning",
    "rlhf": "RLHF",
    "distillation": "Knowledge distillation",
    "cpt": "Continued pretraining",
    "instruction": "Instruction tuning",
    "rag": "RAG",
}


def _aas_env_url() -> str:
    hostname = os.environ["AAS_HOSTNAME"]
    port = os.environ["AAS_ENVIRONMENT_PORT"]
    return f"http://{hostname}:{port}"  # raises KeyError if not set


def _aas_id() -> str:
    return os.environ["AAS_ID"]  # raises KeyError if not set


def _base64url(value: str) -> str:
    """Base64URL-encode a string without padding (for BaSyx REST API)."""
    return base64.urlsafe_b64encode(value.encode()).decode().rstrip("=")


def _gen_submodel_id() -> str:
    """Generate a unique submodel ID in DFKI IDTA segment format."""
    raw = uuid.uuid4().hex.upper()
    segments = [raw[i : i + 4] for i in range(0, 16, 4)]
    return f"https://dfki.de/ids/asset/{'_'.join(segments)}"


def _looks_like_uri(value: str) -> bool:
    """True if *value* looks like an http(s) URL or a DFKI IDS asset URI.

    Keeps the AAS submodel's ``xs:anyURI`` property valid — we only fall back
    to ``dataset_ref`` when it's actually a URI, never when it's a plain name.
    """
    lowered = value.strip().lower()
    return lowered.startswith(("http://", "https://", "s3://"))


# --- AAS element builders ---


def _prop(id_short: str, value_type: str, value: Any) -> dict[str, Any]:
    return {
        "idShort": id_short,
        "modelType": "Property",
        "valueType": value_type,
        "value": str(value) if value is not None else "",
    }


def _mlp(id_short: str, text: str, lang: str = "en") -> dict[str, Any]:
    return {
        "idShort": id_short,
        "modelType": "MultiLanguageProperty",
        "value": [{"language": lang, "text": text}],
    }


def _smc(
    id_short: str,
    elements: list[dict[str, Any]],
    semantic_id: dict[str, Any] | None = None,
) -> dict[str, Any]:
    node: dict[str, Any] = {
        "idShort": id_short,
        "modelType": "SubmodelElementCollection",
        "value": elements,
    }
    if semantic_id:
        node["semanticId"] = semantic_id
    return node


_DATASET_SMC_SEMANTIC_ID: dict[str, Any] = {
    "type": "ExternalReference",
    "keys": [
        {
            "type": "GlobalReference",
            "value": "https://admin-shell.io/idta/AIModelNameplate/AIDataset/1/0",
        }
    ],
}

_TIMESTAMP_SEMANTIC_ID: dict[str, Any] = {
    "type": "ExternalReference",
    "keys": [
        {
            "type": "GlobalReference",
            "value": "https://admin-shell.io/idta/AIModelNameplate/AIDataset/TimeStamp/1/0",
        }
    ],
}

_DATASET_REF_SEMANTIC_ID: dict[str, Any] = {
    "type": "ExternalReference",
    "keys": [
        {
            "type": "GlobalReference",
            "value": "https://admin-shell.io/idta/AIModelNameplate/AIDataset/DatasetReference/1/0",
        }
    ],
}


def _timestamp_range(start_ts: str, end_ts: str) -> dict[str, Any]:
    return {
        "idShort": "TimeStamp",
        "modelType": "Range",
        "valueType": "xs:dateTime",
        "semanticId": _TIMESTAMP_SEMANTIC_ID,
        "min": start_ts,
        "max": end_ts,
    }


def _dataset_smc_aas(id_short: str, submodel_id: str, start_ts: str, end_ts: str) -> dict[str, Any]:
    """AIDataset SMC for a dataset that has an AAS submodel — uses ReferenceElement."""
    return _smc(
        id_short,
        [
            {
                "idShort": "AIDatasetReference",
                "modelType": "ReferenceElement",
                "category": "CONSTANT",
                "semanticId": _DATASET_REF_SEMANTIC_ID,
                "value": {
                    "type": "ExternalReference",
                    "keys": [{"type": "Submodel", "value": submodel_id}],
                },
            },
            _timestamp_range(start_ts, end_ts),
        ],
        semantic_id=_DATASET_SMC_SEMANTIC_ID,
    )


def _dataset_smc_external(id_short: str, uri: str, start_ts: str, end_ts: str) -> dict[str, Any]:
    """AIDataset SMC for an external dataset (HuggingFace, Kaggle, URL) — uses Property."""
    return _smc(
        id_short,
        [
            _prop("ExternalDatasetURI", "xs:anyURI", uri),
            _timestamp_range(start_ts, end_ts),
        ],
        semantic_id=_DATASET_SMC_SEMANTIC_ID,
    )


def build_ai_model_nameplate(job: Job, submodel_id: str) -> dict[str, Any]:
    """
    Build an IDTA-02060-1-0-1 AI Model Nameplate submodel from job metadata.

    Args:
        job: Completed training job with result and config.
        submodel_id: Unique AAS submodel ID (DFKI segment URI).

    Returns:
        Submodel dict ready for JSON serialization and POST to BaSyx.
    """
    cfg = job.config
    kind_of_learning = _KIND_OF_LEARNING_LABELS.get(job.method.value, job.method.value)

    # Model reference & storage path
    model_ref = (job.result.model_ref or "") if job.result else ""

    # Final loss from training metrics
    final_loss: Any = None
    if job.result and job.result.metrics:
        final_loss = job.result.metrics.get("final_loss") or job.result.metrics.get("loss")
    example_result = f"Final loss: {final_loss}" if final_loss is not None else ""

    # Hyperparameters — support both camelCase and snake_case keys
    epochs = cfg.get("epochs", cfg.get("num_train_epochs", 0))
    learning_rate = cfg.get("learning_rate", cfg.get("lr", 0.0))
    batch_size = cfg.get("batch_size", cfg.get("per_device_train_batch_size", 0))

    # Dataset elements
    # config["datasets"] is a list of typed entries:
    #   {"source": "aas",         "submodel_id": "https://dfki.de/ids/asset/..."}
    #   {"source": "huggingface", "uri": "https://huggingface.co/datasets/..."}
    #   {"source": "kaggle",      "uri": "https://www.kaggle.com/datasets/..."}
    #   {"source": "url",         "uri": "https://..."}
    # Fallback: only treat dataset_ref as an external URI when it actually
    # looks like one. Otherwise a free-form dataset name (e.g. "Refusal-
    # Compliance Prompt Pairs") would end up as the value of an xs:anyURI
    # property in the submodel — which is neither valid nor traceable.
    datasets: list[dict[str, Any]] = cfg.get("datasets", [])
    if not datasets and job.dataset_ref and _looks_like_uri(job.dataset_ref):
        datasets = [{"source": "url", "uri": job.dataset_ref}]

    start_ts = job.created_at.isoformat()
    end_ts = job.updated_at.isoformat()

    dataset_smcs: list[dict[str, Any]] = []
    for i, ds in enumerate(datasets):
        id_short = "AIDataset" if i == 0 else f"AIDataset{i}"
        if ds.get("source") == "aas":
            dataset_smcs.append(_dataset_smc_aas(id_short, ds["submodel_id"], start_ts, end_ts))
        else:
            dataset_smcs.append(_dataset_smc_external(id_short, ds["uri"], start_ts, end_ts))

    elements: list[dict[str, Any]] = [
        _prop("URIOfTheProduct", "xs:string", model_ref),
        _prop("Version", "xs:string", "1.0.0"),
        _prop("Storage", "xs:string", model_ref),
        _mlp("KindOfLearning", kind_of_learning),
        _smc("TrainingResults", [_prop("ExampleResult", "xs:string", example_result)]),
        _smc("Details", [_prop("AIFramework", "xs:string", "Hugging Face / PEFT")]),
        _smc(
            "AITypeSpecificInformation",
            [
                _smc("TransferLearning", [_prop("Name", "xs:string", job.base_model)]),
                _smc(
                    "Hyperparameter",
                    [
                        _prop("Epochs", "xs:int", epochs),
                        _prop("LearningRate", "xs:float", learning_rate),
                        _prop("BatchSize", "xs:int", batch_size),
                    ],
                ),
            ],
        ),
        *dataset_smcs,
    ]

    return {
        "modelType": "Submodel",
        "id": submodel_id,
        "idShort": f"AIModel_{job.id.replace('-', '_')}",
        "kind": "Instance",
        "semanticId": {
            "type": "ExternalReference",
            "keys": [
                {
                    "type": "GlobalReference",
                    "value": "https://admin-shell.io/idta/SubmodelTemplate/AIModelNameplate/1/0",
                }
            ],
        },
        "submodelElements": elements,
    }


async def push_submodel_to_aas(job: Job) -> dict[str, Any]:
    """
    Push an IDTA-02060 AI Model Nameplate to the Eclipse BaSyx AAS Environment.

    Executes two HTTP calls:
    1. POST /submodels — create the submodel
    2. POST /shells/{base64url(AAS_ID)}/submodel-refs — link to AIModelCatalogue AAS

    Args:
        job: Completed training job.

    Returns:
        Dict with ``submodel_id``, ``aas_url``, and ``status``.

    Raises:
        httpx.HTTPStatusError: If either AAS call returns a non-2xx response.
        httpx.RequestError: On network / timeout errors.
    """
    aas_url = _aas_env_url()
    aas_id = _aas_id()
    submodel_id = _gen_submodel_id()
    submodel = build_ai_model_nameplate(job, submodel_id)

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Create submodel
        resp = await client.post(
            f"{aas_url}/submodels",
            json=submodel,
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()
        logger.info("Job %s: submodel created at %s (id=%s)", job.id, aas_url, submodel_id)

        # 2. Link submodel to target AAS shell
        encoded_aas_id = _base64url(aas_id)
        submodel_ref = {
            "type": "ExternalReference",
            "keys": [{"type": "Submodel", "value": submodel_id}],
        }
        ref_resp = await client.post(
            f"{aas_url}/shells/{encoded_aas_id}/submodel-refs",
            json=submodel_ref,
            headers={"Content-Type": "application/json"},
        )
        ref_resp.raise_for_status()
        logger.info("Job %s: submodel linked to AAS %s", job.id, aas_id)

    return {
        "submodel_id": submodel_id,
        "aas_url": aas_url,
        "status": "published",
    }
