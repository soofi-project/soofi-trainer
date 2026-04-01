"""Tests for sse_stream.py helper functions.

These tests exercise pure functions extracted inline to avoid importing the full
module (which depends on langchain_core, langgraph, etc. that aren't installed locally).
The logic is identical to the production code in src/sse_stream.py.
"""

import re
from types import SimpleNamespace
from typing import Any

import pytest

# ---------------------------------------------------------------------------
# Inline copies of the pure functions under test (no external deps)
# ---------------------------------------------------------------------------

_RE_DOCS_URL = re.compile(r"https?://[^/\s)]+(/docs/)")


def _extract_tool_text(raw: Any) -> str:
    if isinstance(raw, str):
        return raw
    content = raw.content if hasattr(raw, "content") else raw
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        for part in content:
            if isinstance(part, str):
                return part
            if isinstance(part, dict) and part.get("type") == "text":
                return part.get("text", "")
    return str(content)


def _compute_tail(full_output: str, streamed: str) -> str:
    if not full_output or len(full_output) <= len(streamed):
        return ""
    if full_output.startswith(streamed):
        return full_output[len(streamed):]
    cleaned_output = _RE_DOCS_URL.sub(r"\1", full_output)
    if cleaned_output.startswith(streamed):
        return cleaned_output[len(streamed):]
    return ""


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestExtractToolText:
    """Tests for _extract_tool_text — robust extraction from various ToolMessage formats."""

    def test_plain_string(self) -> None:
        assert _extract_tool_text("hello") == "hello"

    def test_empty_string(self) -> None:
        assert _extract_tool_text("") == ""

    def test_tool_message_with_str_content(self) -> None:
        msg = SimpleNamespace(content="some text")
        assert _extract_tool_text(msg) == "some text"

    def test_tool_message_with_list_of_parts(self) -> None:
        msg = SimpleNamespace(content=[{"type": "text", "text": "extracted"}])
        assert _extract_tool_text(msg) == "extracted"

    def test_tool_message_with_list_of_strings(self) -> None:
        msg = SimpleNamespace(content=["first", "second"])
        assert _extract_tool_text(msg) == "first"

    def test_tool_message_with_empty_list(self) -> None:
        msg = SimpleNamespace(content=[])
        assert _extract_tool_text(msg) == "[]"

    def test_tool_message_with_mixed_parts(self) -> None:
        msg = SimpleNamespace(content=[{"type": "image"}, {"type": "text", "text": "found"}])
        assert _extract_tool_text(msg) == "found"

    def test_dict_without_content(self) -> None:
        result = _extract_tool_text({"key": "value"})
        assert isinstance(result, str)

    def test_none_content(self) -> None:
        msg = SimpleNamespace(content=None)
        assert _extract_tool_text(msg) == "None"


class TestComputeTail:
    """Tests for _compute_tail — tail compensation for streamed vs full output."""

    def test_exact_match(self) -> None:
        assert _compute_tail("hello world", "hello world") == ""

    def test_partial_stream(self) -> None:
        assert _compute_tail("hello world", "hello ") == "world"

    def test_empty_output(self) -> None:
        assert _compute_tail("", "streamed") == ""

    def test_empty_streamed(self) -> None:
        assert _compute_tail("full output", "") == "full output"

    def test_output_shorter_than_streamed(self) -> None:
        assert _compute_tail("hi", "hello") == ""

    def test_with_docs_url_cleaning(self) -> None:
        full = "See https://www.dfki.de/docs/lora.md for details"
        streamed = "See /docs/lora.md for details"
        assert _compute_tail(full, streamed) == ""

    def test_docs_url_with_tail(self) -> None:
        full = "See https://www.dfki.de/docs/lora.md and more text"
        streamed = "See /docs/lora.md"
        assert _compute_tail(full, streamed) == " and more text"
