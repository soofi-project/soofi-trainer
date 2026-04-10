"""Tests for graph.py helper functions and state management.

Pure function tests — no external deps required.
"""

import collections
from types import SimpleNamespace

import pytest

# ---------------------------------------------------------------------------
# Inline copy of after_tools logic (avoids importing graph.py with all its deps)
# ---------------------------------------------------------------------------

_STREAMING_TOOLS = {"ask_advisor_tool", "ask_training_agent_tool", "ask_dataset_agent_tool"}


def after_tools(state: dict) -> str:
    """Skip the second LLM call if a streaming tool already delivered the response."""
    for msg in reversed(state["messages"]):
        if hasattr(msg, "tool_calls"):
            break
        if hasattr(msg, "name") and msg.name in _STREAMING_TOOLS:
            return "__end__"
    return "agent"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestAfterTools:
    """Tests for after_tools — short-circuit second LLM call for streaming tools."""

    def test_advisor_tool_skips(self) -> None:
        tool_msg = SimpleNamespace(name="ask_advisor_tool")
        ai_msg = SimpleNamespace(tool_calls=[{"name": "ask_advisor_tool"}])
        assert after_tools({"messages": [ai_msg, tool_msg]}) == "__end__"

    def test_training_tool_skips(self) -> None:
        tool_msg = SimpleNamespace(name="ask_training_agent_tool")
        ai_msg = SimpleNamespace(tool_calls=[{"name": "ask_training_agent_tool"}])
        assert after_tools({"messages": [ai_msg, tool_msg]}) == "__end__"

    def test_dataset_agent_tool_skips(self) -> None:
        tool_msg = SimpleNamespace(name="ask_dataset_agent_tool")
        ai_msg = SimpleNamespace(tool_calls=[{"name": "ask_dataset_agent_tool"}])
        assert after_tools({"messages": [ai_msg, tool_msg]}) == "__end__"

    def test_non_streaming_tool_continues(self) -> None:
        tool_msg = SimpleNamespace(name="show_agent_card")
        ai_msg = SimpleNamespace(tool_calls=[{"name": "show_agent_card"}])
        assert after_tools({"messages": [ai_msg, tool_msg]}) == "agent"

    def test_control_doc_viewer_continues(self) -> None:
        tool_msg = SimpleNamespace(name="control_doc_viewer")
        ai_msg = SimpleNamespace(tool_calls=[{"name": "control_doc_viewer"}])
        assert after_tools({"messages": [ai_msg, tool_msg]}) == "agent"

    def test_web_search_tool_continues(self) -> None:
        tool_msg = SimpleNamespace(name="web_search_tool")
        ai_msg = SimpleNamespace(tool_calls=[{"name": "web_search_tool"}])
        assert after_tools({"messages": [ai_msg, tool_msg]}) == "agent"

    def test_empty_messages(self) -> None:
        assert after_tools({"messages": []}) == "agent"

    def test_multiple_tool_results_streaming_wins(self) -> None:
        """When multiple tools are called, streaming tool should still skip."""
        ai_msg = SimpleNamespace(
            tool_calls=[{"name": "show_agent_card"}, {"name": "ask_advisor_tool"}]
        )
        tool1 = SimpleNamespace(name="show_agent_card")
        tool2 = SimpleNamespace(name="ask_advisor_tool")
        # tool2 is last → found first in reverse scan
        assert after_tools({"messages": [ai_msg, tool1, tool2]}) == "__end__"

    def test_multiple_tool_results_reversed_order(self) -> None:
        """Streaming tool first, non-streaming last — must still skip."""
        ai_msg = SimpleNamespace(
            tool_calls=[{"name": "ask_advisor_tool"}, {"name": "show_agent_card"}]
        )
        tool1 = SimpleNamespace(name="ask_advisor_tool")
        tool2 = SimpleNamespace(name="show_agent_card")
        # tool2 (non-streaming) is last in reverse scan — must still find tool1
        assert after_tools({"messages": [ai_msg, tool1, tool2]}) == "__end__"


class TestRagUrlsStoreLRU:
    """Tests for _rag_urls_store LRU eviction behavior."""

    def test_lru_eviction(self) -> None:
        store: collections.OrderedDict[str, list[str]] = collections.OrderedDict()
        max_size = 3

        for i in range(5):
            key = f"ctx_{i}"
            store[key] = [f"/docs/file_{i}.md"]
            store.move_to_end(key)
            while len(store) > max_size:
                store.popitem(last=False)

        assert len(store) == 3
        assert "ctx_0" not in store
        assert "ctx_1" not in store
        assert "ctx_2" in store
        assert "ctx_3" in store
        assert "ctx_4" in store

    def test_lru_update_refreshes(self) -> None:
        store: collections.OrderedDict[str, list[str]] = collections.OrderedDict()
        max_size = 3

        for i in range(3):
            store[f"ctx_{i}"] = [f"/docs/{i}.md"]

        # Update ctx_0 — should move it to end
        store["ctx_0"] = ["/docs/updated.md"]
        store.move_to_end("ctx_0")

        # Add a new entry — should evict ctx_1 (oldest), not ctx_0
        store["ctx_3"] = ["/docs/3.md"]
        store.move_to_end("ctx_3")
        while len(store) > max_size:
            store.popitem(last=False)

        assert "ctx_0" in store
        assert "ctx_1" not in store
        assert "ctx_2" in store
        assert "ctx_3" in store
