"""Pure stdlib tests for vLLM-only LLM env parsing in agent graph modules."""

from __future__ import annotations

import importlib.util
import os
import sys
import types
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]

MODULE_SPECS = [
    {
        "file": REPO_ROOT / "advisor" / "src" / "graph.py",
        "package": "advisor_case",
        "prefix": "ADVISOR",
        "model_env": "ADVISOR_MODEL",
        "extra_modules": {
            "prompts": {"SYSTEM_PROMPT_DE": "prompt"},
        },
    },
    {
        "file": REPO_ROOT / "interaction-agent" / "src" / "graph.py",
        "package": "interaction_case",
        "prefix": "INTERACTION",
        "model_env": "INTERACTION_MODEL",
        "extra_modules": {
            "a2a_client": {
                "ask_advisor": lambda *args, **kwargs: None,
                "ask_dataset_agent": lambda *args, **kwargs: None,
                "ask_training_agent": lambda *args, **kwargs: None,
                "stream_advisor": lambda *args, **kwargs: None,
                "stream_dataset_agent": lambda *args, **kwargs: None,
                "stream_training_agent": lambda *args, **kwargs: None,
            },
            "constants": {
                "ADVISOR_EVENT": "advisor_event",
                "ADVISOR_KEY_CHUNK": "advisor_chunk",
                "ADVISOR_KEY_SEARCH_STATUS": "advisor_search_status",
                "AGENT_CARD_EVENT": "agent_card_event",
                "AGENT_CARD_KEY": "agent_card",
                "DATASET_AGENT_KEY_CHUNK": "dataset_chunk",
                "DATASET_AGENT_KEY_STATUS": "dataset_status",
                "DATASET_AGENT_KEY_TOOL": "dataset_tool",
                "DATASET_EVENT": "dataset_event",
                "DOC_VIEWER_KEY": "doc_viewer",
                "ADVISOR_KEY_RAG_SOURCES": "advisor_rag_sources",
                "SOOFI_EVENT_JOB_STARTED": "job_started",
                "SOOFI_EVENT_KEY": "soofi_event",
                "SOOFI_EVENT_RAG_SOURCES": "rag_sources",
                "SOOFI_EVENT_SEARCH_STATUS": "search_status",
                "TRAINING_AGENT_KEY_CHUNK": "training_chunk",
                "TRAINING_AGENT_KEY_JOB_STARTED": "training_job_started",
                "TRAINING_AGENT_KEY_STATUS": "training_status",
                "TRAINING_EVENT": "training_event",
                "TRAINING_VIEW_EVENT": "training_view_event",
                "TRAINING_VIEW_KEY": "training_view",
            },
            "i18n": {
                "Language": str,
                "tr": lambda *args, **kwargs: "translated",
            },
            "prompts": {
                "get_system_prompt": lambda *_args, **_kwargs: "prompt",
            },
        },
    },
    {
        "file": REPO_ROOT / "training-agent" / "src" / "training_agent" / "graph.py",
        "package": "training_case",
        "prefix": "TRAINING_AGENT",
        "model_env": "TRAINING_AGENT_MODEL",
        "extra_modules": {
            "prompts": {"SYSTEM_PROMPT_DE": "prompt"},
        },
    },
    {
        "file": REPO_ROOT / "dataset-agent" / "src" / "dataset_agent" / "graph.py",
        "package": "dataset_case",
        "prefix": "DATASET_AGENT",
        "model_env": "DATASET_AGENT_MODEL",
        "extra_modules": {
            "prompts": {"SYSTEM_PROMPT_DE": "prompt"},
        },
    },
]


def _stub_modules() -> dict[str, types.ModuleType]:
    class _FakeStateGraph:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

        def add_node(self, *_args, **_kwargs) -> None:
            pass

        def set_entry_point(self, *_args, **_kwargs) -> None:
            pass

        def add_conditional_edges(self, *_args, **_kwargs) -> None:
            pass

        def add_edge(self, *_args, **_kwargs) -> None:
            pass

        def compile(self, **_kwargs) -> str:
            return "compiled"

    class _FakeToolNode:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

        async def ainvoke(self, state):
            return state

    class _FakeChatOpenAI:
        def __init__(self, **kwargs) -> None:
            self.kwargs = kwargs

        def bind_tools(self, *_args, **_kwargs):
            return self

        async def ainvoke(self, *_args, **_kwargs):
            return types.SimpleNamespace(tool_calls=[])

    langchain_core = types.ModuleType("langchain_core")
    callbacks = types.ModuleType("langchain_core.callbacks")
    messages = types.ModuleType("langchain_core.messages")
    runnables = types.ModuleType("langchain_core.runnables")
    tools = types.ModuleType("langchain_core.tools")
    callbacks.adispatch_custom_event = lambda *args, **kwargs: None
    messages.AIMessage = type("AIMessage", (), {})
    messages.HumanMessage = type("HumanMessage", (), {})
    messages.ToolMessage = type("ToolMessage", (), {})
    runnables.RunnableConfig = dict
    tools.BaseTool = object
    tools.tool = lambda fn: fn

    langchain_openai = types.ModuleType("langchain_openai")
    langchain_openai.ChatOpenAI = _FakeChatOpenAI

    langgraph = types.ModuleType("langgraph")
    checkpoint = types.ModuleType("langgraph.checkpoint")
    checkpoint_memory = types.ModuleType("langgraph.checkpoint.memory")
    graph = types.ModuleType("langgraph.graph")
    graph_state = types.ModuleType("langgraph.graph.state")
    prebuilt = types.ModuleType("langgraph.prebuilt")
    checkpoint_memory.MemorySaver = object
    graph.MessagesState = dict
    graph.StateGraph = _FakeStateGraph
    graph_state.CompiledStateGraph = object
    prebuilt.ToolNode = _FakeToolNode

    httpx = types.ModuleType("httpx")
    httpx.AsyncClient = object

    return {
        "langchain_core": langchain_core,
        "langchain_core.callbacks": callbacks,
        "langchain_core.messages": messages,
        "langchain_core.runnables": runnables,
        "langchain_core.tools": tools,
        "langchain_openai": langchain_openai,
        "langgraph": langgraph,
        "langgraph.checkpoint": checkpoint,
        "langgraph.checkpoint.memory": checkpoint_memory,
        "langgraph.graph": graph,
        "langgraph.graph.state": graph_state,
        "langgraph.prebuilt": prebuilt,
        "httpx": httpx,
    }


def _load_graph_module(module_spec: dict[str, object], env: dict[str, str]) -> types.ModuleType:
    package = f"{module_spec['package']}_{uuid.uuid4().hex}"
    graph_module_name = f"{package}.graph"

    patched_modules = _stub_modules()
    package_module = types.ModuleType(package)
    package_module.__path__ = []  # type: ignore[attr-defined]
    patched_modules[package] = package_module

    for suffix, attrs in module_spec["extra_modules"].items():
        module = types.ModuleType(f"{package}.{suffix}")
        for name, value in attrs.items():
            setattr(module, name, value)
        patched_modules[f"{package}.{suffix}"] = module

    with patch.dict(os.environ, env, clear=True), patch.dict(sys.modules, patched_modules):
        spec = importlib.util.spec_from_file_location(graph_module_name, module_spec["file"])
        if spec is None or spec.loader is None:
            raise AssertionError(f"Unable to load spec for {module_spec['file']}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[graph_module_name] = module
        spec.loader.exec_module(module)
        return module


class VllmLlmWiringTests(unittest.TestCase):
    def test_non_vllm_path_ignores_sampling_envs(self) -> None:
        for module_spec in MODULE_SPECS:
            with self.subTest(module=module_spec["file"].name):
                env = {module_spec["model_env"]: "test-model"}
                module = _load_graph_module(module_spec, env)
                with patch.dict(os.environ, env, clear=True):
                    self.assertEqual(module._build_vllm_kwargs(module_spec["prefix"]), {})

    def test_vllm_requires_base_url(self) -> None:
        for module_spec in MODULE_SPECS:
            with self.subTest(module=module_spec["file"].name):
                env = {
                    module_spec["model_env"]: "test-model",
                    "SOOFI_LLM_BACKEND": "vllm",
                }
                module = _load_graph_module(module_spec, env)
                with patch.dict(os.environ, env, clear=True):
                    with self.assertRaisesRegex(RuntimeError, "OPENAI_BASE_URL env var required"):
                        module._build_vllm_kwargs(module_spec["prefix"])

    def test_vllm_qwen_profile_uses_all_explicit_knobs(self) -> None:
        for module_spec in MODULE_SPECS:
            with self.subTest(module=module_spec["file"].name):
                prefix = module_spec["prefix"]
                env = {
                    module_spec["model_env"]: "test-model",
                    "SOOFI_LLM_BACKEND": "vllm",
                    "OPENAI_BASE_URL": "http://example.test/v1",
                    f"{prefix}_TEMPERATURE": "1.0",
                    f"{prefix}_TOP_P": "0.95",
                    f"{prefix}_TOP_K": "20",
                    f"{prefix}_MIN_P": "0.0",
                    f"{prefix}_PRESENCE_PENALTY": "1.5",
                    f"{prefix}_REPEAT_PENALTY": "1.0",
                    f"{prefix}_ENABLE_THINKING": "false",
                }
                module = _load_graph_module(module_spec, env)
                with patch.dict(os.environ, env, clear=True):
                    self.assertEqual(
                        module._build_vllm_kwargs(prefix),
                        {
                            "temperature": 1.0,
                            "top_p": 0.95,
                            "presence_penalty": 1.5,
                            "extra_body": {
                                "top_k": 20,
                                "min_p": 0.0,
                                "repetition_penalty": 1.0,
                                "chat_template_kwargs": {"enable_thinking": False},
                            },
                        },
                    )

    def test_vllm_nemotron_profile_omits_unset_optional_knobs(self) -> None:
        for module_spec in MODULE_SPECS:
            with self.subTest(module=module_spec["file"].name):
                prefix = module_spec["prefix"]
                env = {
                    module_spec["model_env"]: "test-model",
                    "SOOFI_LLM_BACKEND": "vllm",
                    "OPENAI_BASE_URL": "http://example.test/v1",
                    f"{prefix}_TEMPERATURE": "0.6",
                    f"{prefix}_TOP_P": "0.95",
                    f"{prefix}_MIN_P": "0.01",
                    f"{prefix}_ENABLE_THINKING": "true",
                }
                module = _load_graph_module(module_spec, env)
                with patch.dict(os.environ, env, clear=True):
                    self.assertEqual(
                        module._build_vllm_kwargs(prefix),
                        {
                            "temperature": 0.6,
                            "top_p": 0.95,
                            "extra_body": {
                                "min_p": 0.01,
                                "chat_template_kwargs": {"enable_thinking": True},
                            },
                        },
                    )

    def test_vllm_missing_required_value_fails_fast(self) -> None:
        for module_spec in MODULE_SPECS:
            with self.subTest(module=module_spec["file"].name):
                prefix = module_spec["prefix"]
                env = {
                    module_spec["model_env"]: "test-model",
                    "SOOFI_LLM_BACKEND": "vllm",
                    "OPENAI_BASE_URL": "http://example.test/v1",
                    f"{prefix}_TOP_P": "0.95",
                    f"{prefix}_MIN_P": "0.01",
                    f"{prefix}_ENABLE_THINKING": "true",
                }
                module = _load_graph_module(module_spec, env)
                with patch.dict(os.environ, env, clear=True):
                    with self.assertRaisesRegex(
                        RuntimeError, f"{prefix}_TEMPERATURE env var required"
                    ):
                        module._build_vllm_kwargs(prefix)

    def test_vllm_invalid_boolean_fails_fast(self) -> None:
        for module_spec in MODULE_SPECS:
            with self.subTest(module=module_spec["file"].name):
                prefix = module_spec["prefix"]
                env = {
                    module_spec["model_env"]: "test-model",
                    "SOOFI_LLM_BACKEND": "vllm",
                    "OPENAI_BASE_URL": "http://example.test/v1",
                    f"{prefix}_TEMPERATURE": "0.6",
                    f"{prefix}_TOP_P": "0.95",
                    f"{prefix}_MIN_P": "0.01",
                    f"{prefix}_ENABLE_THINKING": "sometimes",
                }
                module = _load_graph_module(module_spec, env)
                with patch.dict(os.environ, env, clear=True):
                    with self.assertRaisesRegex(
                        RuntimeError, f"{prefix}_ENABLE_THINKING env var must be a boolean"
                    ):
                        module._build_vllm_kwargs(prefix)


if __name__ == "__main__":
    unittest.main()
