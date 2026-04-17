"""Unit tests for aas_push module — submodel generation and HTTP push."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from training_gateway.aas_push import (
    _base64url,
    _gen_submodel_id,
    _looks_like_uri,
    build_ai_model_nameplate,
    push_submodel_to_aas,
    _dataset_smc_aas,
    _dataset_smc_external,
)
from training_gateway.models import Job, JobResult, JobStatus, TrainingMethod


def _make_job(**kwargs) -> Job:  # type: ignore[return]
    defaults: dict = {
        "id": "test-job-1234-5678-abcd",
        "method": TrainingMethod.lora,
        "dataset_ref": "https://dfki.de/ids/asset/DS01_0001_0001_0001",
        "base_model": "mistralai/Mistral-7B-v0.1",
        "config": {"epochs": 3, "learning_rate": 0.0002, "batch_size": 4},
        "status": JobStatus.completed,
        "created_at": datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        "updated_at": datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
        "result": JobResult(
            model_ref="s3://soofi-models/test-job/model.bin",
            metrics={"final_loss": 0.42},
        ),
    }
    defaults.update(kwargs)
    return Job(**defaults)


@pytest.mark.unit
class TestBase64Url:
    def test_known_value(self) -> None:
        assert _base64url("hello") == "aGVsbG8"

    def test_no_padding(self) -> None:
        result = _base64url("https://dfki.de/ids/aas/9849_9446_1501_2526")
        assert "=" not in result


@pytest.mark.unit
class TestLooksLikeUri:
    def test_https_is_uri(self) -> None:
        assert _looks_like_uri("https://hf.co/datasets/foo/bar") is True

    def test_http_is_uri(self) -> None:
        assert _looks_like_uri("http://example.com/ds") is True

    def test_s3_is_uri(self) -> None:
        assert _looks_like_uri("s3://bucket/key") is True

    def test_plain_name_is_not_uri(self) -> None:
        assert _looks_like_uri("Refusal-Compliance Prompt Pairs") is False

    def test_empty_is_not_uri(self) -> None:
        assert _looks_like_uri("") is False


@pytest.mark.unit
class TestGenSubmodelId:
    def test_format(self) -> None:
        sid = _gen_submodel_id()
        assert sid.startswith("https://dfki.de/ids/asset/")
        suffix = sid.removeprefix("https://dfki.de/ids/asset/")
        parts = suffix.split("_")
        assert len(parts) == 4
        assert all(len(p) == 4 for p in parts)

    def test_unique(self) -> None:
        ids = {_gen_submodel_id() for _ in range(20)}
        assert len(ids) == 20


@pytest.mark.unit
class TestBuildAiModelNameplate:
    def test_basic_structure(self) -> None:
        job = _make_job()
        sid = "https://dfki.de/ids/asset/AAAA_BBBB_CCCC_DDDD"
        sm = build_ai_model_nameplate(job, sid)

        assert sm["modelType"] == "Submodel"
        assert sm["id"] == sid
        assert sm["idShort"] == "AIModel_test_job_1234_5678_abcd"
        assert sm["kind"] == "Instance"
        assert "semanticId" in sm
        assert sm["semanticId"]["keys"][0]["value"] == (
            "https://admin-shell.io/idta/SubmodelTemplate/AIModelNameplate/1/0"
        )

    def test_element_id_shorts(self) -> None:
        job = _make_job()
        sm = build_ai_model_nameplate(job, "https://dfki.de/ids/asset/X")
        id_shorts = [e["idShort"] for e in sm["submodelElements"]]
        assert "URIOfTheProduct" in id_shorts
        assert "Version" in id_shorts
        assert "Storage" in id_shorts
        assert "KindOfLearning" in id_shorts
        assert "TrainingResults" in id_shorts
        assert "Details" in id_shorts
        assert "AITypeSpecificInformation" in id_shorts
        assert "AIDataset" in id_shorts

    def test_lora_kind_of_learning(self) -> None:
        job = _make_job(method=TrainingMethod.lora)
        sm = build_ai_model_nameplate(job, "x")
        mlp = next(e for e in sm["submodelElements"] if e["idShort"] == "KindOfLearning")
        assert mlp["value"][0]["text"] == "LoRA fine-tuning"

    def test_qlora_kind_of_learning(self) -> None:
        job = _make_job(method=TrainingMethod.qlora)
        sm = build_ai_model_nameplate(job, "x")
        mlp = next(e for e in sm["submodelElements"] if e["idShort"] == "KindOfLearning")
        assert mlp["value"][0]["text"] == "QLoRA fine-tuning"

    def test_training_results_with_loss(self) -> None:
        job = _make_job()
        sm = build_ai_model_nameplate(job, "x")
        tr = next(e for e in sm["submodelElements"] if e["idShort"] == "TrainingResults")
        example = next(v for v in tr["value"] if v["idShort"] == "ExampleResult")
        assert example["value"] == "Final loss: 0.42"

    def test_training_results_no_loss(self) -> None:
        job = _make_job(result=JobResult(model_ref="s3://bucket/m"))
        sm = build_ai_model_nameplate(job, "x")
        tr = next(e for e in sm["submodelElements"] if e["idShort"] == "TrainingResults")
        example = next(v for v in tr["value"] if v["idShort"] == "ExampleResult")
        assert example["value"] == ""

    def test_hyperparameters(self) -> None:
        job = _make_job(config={"epochs": 5, "learning_rate": 1e-4, "batch_size": 8})
        sm = build_ai_model_nameplate(job, "x")
        ai_info = next(
            e for e in sm["submodelElements"] if e["idShort"] == "AITypeSpecificInformation"
        )
        hp = next(v for v in ai_info["value"] if v["idShort"] == "Hyperparameter")
        hp_map = {e["idShort"]: e["value"] for e in hp["value"]}
        assert hp_map["Epochs"] == "5"
        assert hp_map["LearningRate"] == "0.0001"
        assert hp_map["BatchSize"] == "8"

    def test_base_model_in_transfer_learning(self) -> None:
        job = _make_job(base_model="meta-llama/Llama-3.1-8B-Instruct")
        sm = build_ai_model_nameplate(job, "x")
        ai_info = next(
            e for e in sm["submodelElements"] if e["idShort"] == "AITypeSpecificInformation"
        )
        tl = next(v for v in ai_info["value"] if v["idShort"] == "TransferLearning")
        name = next(v for v in tl["value"] if v["idShort"] == "Name")
        assert name["value"] == "meta-llama/Llama-3.1-8B-Instruct"

    def test_aas_dataset_uses_reference_element(self) -> None:
        job = _make_job(
            config={
                "datasets": [{"source": "aas", "submodel_id": "https://dfki.de/ids/asset/DS_0001"}]
            }
        )
        sm = build_ai_model_nameplate(job, "x")
        ds = next(e for e in sm["submodelElements"] if e["idShort"] == "AIDataset")
        ref_elem = next(v for v in ds["value"] if v["idShort"] == "AIDatasetReference")
        assert ref_elem["modelType"] == "ReferenceElement"
        assert ref_elem["value"]["keys"][0]["value"] == "https://dfki.de/ids/asset/DS_0001"

    def test_huggingface_dataset_uses_property(self) -> None:
        job = _make_job(
            config={
                "datasets": [
                    {
                        "source": "huggingface",
                        "uri": "https://huggingface.co/datasets/tatsu-lab/alpaca",
                    }
                ]
            }
        )
        sm = build_ai_model_nameplate(job, "x")
        ds = next(e for e in sm["submodelElements"] if e["idShort"] == "AIDataset")
        uri_elem = next(v for v in ds["value"] if v["idShort"] == "ExternalDatasetURI")
        assert uri_elem["modelType"] == "Property"
        assert uri_elem["value"] == "https://huggingface.co/datasets/tatsu-lab/alpaca"

    def test_dataset_ref_fallback_is_external(self) -> None:
        job = _make_job(dataset_ref="https://huggingface.co/datasets/tatsu-lab/alpaca", config={})
        sm = build_ai_model_nameplate(job, "x")
        ds = next(e for e in sm["submodelElements"] if e["idShort"] == "AIDataset")
        uri_elem = next(v for v in ds["value"] if v["idShort"] == "ExternalDatasetURI")
        assert uri_elem["value"] == "https://huggingface.co/datasets/tatsu-lab/alpaca"

    def test_dataset_ref_fallback_skipped_for_non_uri(self) -> None:
        """A plain dataset name must NOT be forced into the xs:anyURI property."""
        job = _make_job(dataset_ref="Refusal-Compliance Prompt Pairs", config={})
        sm = build_ai_model_nameplate(job, "x")
        id_shorts = [e["idShort"] for e in sm["submodelElements"]]
        assert "AIDataset" not in id_shorts

    def test_mixed_datasets_numbered(self) -> None:
        job = _make_job(
            config={
                "datasets": [
                    {"source": "aas", "submodel_id": "https://dfki.de/ids/asset/DS_0001"},
                    {"source": "kaggle", "uri": "https://www.kaggle.com/datasets/foo/bar"},
                ]
            }
        )
        sm = build_ai_model_nameplate(job, "x")
        id_shorts = [e["idShort"] for e in sm["submodelElements"]]
        assert "AIDataset" in id_shorts
        assert "AIDataset1" in id_shorts
        # First is AAS → ReferenceElement
        ds0 = next(e for e in sm["submodelElements"] if e["idShort"] == "AIDataset")
        assert any(v["idShort"] == "AIDatasetReference" for v in ds0["value"])
        # Second is Kaggle → Property
        ds1 = next(e for e in sm["submodelElements"] if e["idShort"] == "AIDataset1")
        assert any(v["idShort"] == "ExternalDatasetURI" for v in ds1["value"])

    def test_uri_of_product_from_model_ref(self) -> None:
        job = _make_job()
        sm = build_ai_model_nameplate(job, "x")
        uri = next(e for e in sm["submodelElements"] if e["idShort"] == "URIOfTheProduct")
        assert uri["value"] == "s3://soofi-models/test-job/model.bin"

    def test_no_result_no_model_ref(self) -> None:
        job = _make_job(result=None)
        sm = build_ai_model_nameplate(job, "x")
        uri = next(e for e in sm["submodelElements"] if e["idShort"] == "URIOfTheProduct")
        assert uri["value"] == ""


@pytest.mark.unit
class TestPushSubmodelToAas:
    @pytest.mark.asyncio
    async def test_successful_push(self) -> None:
        job = _make_job()

        mock_response_201 = MagicMock()
        mock_response_201.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response_201)

        with (
            patch.dict(
                os.environ,
                {
                    "AAS_HOSTNAME": "aas.example.com",
                    "AAS_ENVIRONMENT_PORT": "8289",
                    "AAS_ID": "https://dfki.de/ids/aas/TEST",
                },
            ),
            patch("training_gateway.aas_push.httpx.AsyncClient", return_value=mock_client),
        ):
            result = await push_submodel_to_aas(job)

        assert result["status"] == "published"
        assert result["aas_url"] == "http://aas.example.com:8289"
        assert result["submodel_id"].startswith("https://dfki.de/ids/asset/")
        assert mock_client.post.call_count == 2

    @pytest.mark.asyncio
    async def test_submodel_post_url(self) -> None:
        job = _make_job()

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)

        with (
            patch.dict(
                os.environ,
                {
                    "AAS_HOSTNAME": "localhost",
                    "AAS_ENVIRONMENT_PORT": "8289",
                    "AAS_ID": "https://dfki.de/ids/aas/TEST",
                },
            ),
            patch("training_gateway.aas_push.httpx.AsyncClient", return_value=mock_client),
        ):
            await push_submodel_to_aas(job)

        first_call_url = mock_client.post.call_args_list[0][0][0]
        assert first_call_url == "http://localhost:8289/submodels"

    @pytest.mark.asyncio
    async def test_submodel_ref_post_url_contains_base64(self) -> None:
        job = _make_job()
        aas_id = "https://dfki.de/ids/aas/TEST_AAS"

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)

        with (
            patch.dict(
                os.environ,
                {"AAS_HOSTNAME": "localhost", "AAS_ENVIRONMENT_PORT": "8289", "AAS_ID": aas_id},
            ),
            patch("training_gateway.aas_push.httpx.AsyncClient", return_value=mock_client),
        ):
            await push_submodel_to_aas(job)

        second_call_url = mock_client.post.call_args_list[1][0][0]
        assert "/shells/" in second_call_url
        assert "/submodel-refs" in second_call_url
        # Verify no "=" padding in the URL
        assert "=" not in second_call_url
