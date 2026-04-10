"""Tests for web-search backend helper logic.

Pure helper tests only — these inline copies avoid importing graph.py, which
depends on langchain and other optional runtime packages.
"""

from types import SimpleNamespace


def get_openai_web_search_config(env: dict[str, str]) -> dict[str, str | None]:
    """Inline copy of graph._get_openai_web_search_config."""
    model = (env.get("INTERACTION_WEB_SEARCH_OPENAI_MODEL") or "gpt-4.1-mini").strip()
    if not model:
        model = "gpt-4.1-mini"

    return {
        "model": model,
        "base_url": env.get("INTERACTION_WEB_SEARCH_OPENAI_BASE_URL") or None,
        "api_key": (
            env.get("INTERACTION_WEB_SEARCH_OPENAI_API_KEY")
            or env.get("OPENAI_API_KEY")
            or None
        ),
    }


def extract_openai_web_search_text(response: object) -> str:
    """Inline copy of graph._extract_openai_web_search_text."""
    text = getattr(response, "text", None)
    if isinstance(text, str) and text.strip():
        return text.strip()

    content = getattr(response, "content", None)
    if isinstance(content, str) and content.strip():
        return content.strip()
    if isinstance(content, list):
        parts = [
            part.get("text", "")
            for part in content
            if isinstance(part, dict) and part.get("type") == "text" and part.get("text")
        ]
        if parts:
            return "\n".join(parts).strip()

    content_blocks = getattr(response, "content_blocks", None)
    if isinstance(content_blocks, list):
        parts = [
            block.get("text", "")
            for block in content_blocks
            if isinstance(block, dict) and block.get("type") == "text" and block.get("text")
        ]
        if parts:
            return "\n".join(parts).strip()

    raise ValueError("OpenAI web search returned no text content.")


class TestOpenAIWebSearchConfig:
    def test_uses_dedicated_values_when_present(self) -> None:
        env = {
            "INTERACTION_WEB_SEARCH_OPENAI_MODEL": "gpt-5-mini",
            "INTERACTION_WEB_SEARCH_OPENAI_BASE_URL": "https://api.openai.example/v1",
            "INTERACTION_WEB_SEARCH_OPENAI_API_KEY": "dedicated-key",
            "OPENAI_API_KEY": "fallback-key",
            "OPENAI_BASE_URL": "http://local-llm.invalid/v1",
        }

        config = get_openai_web_search_config(env)

        assert config == {
            "model": "gpt-5-mini",
            "base_url": "https://api.openai.example/v1",
            "api_key": "dedicated-key",
        }

    def test_ignores_global_openai_base_url(self) -> None:
        env = {
            "OPENAI_BASE_URL": "http://local-llm.invalid/v1",
            "OPENAI_API_KEY": "fallback-key",
        }

        config = get_openai_web_search_config(env)

        assert config["model"] == "gpt-4.1-mini"
        assert config["base_url"] is None
        assert config["api_key"] == "fallback-key"

    def test_empty_dedicated_model_falls_back_to_default(self) -> None:
        config = get_openai_web_search_config({"INTERACTION_WEB_SEARCH_OPENAI_MODEL": "   "})
        assert config["model"] == "gpt-4.1-mini"


class TestExtractOpenAIWebSearchText:
    def test_prefers_text_attribute(self) -> None:
        response = SimpleNamespace(
            text="Answer from response.text",
            content_blocks=[{"type": "text", "text": "ignored"}],
        )
        assert extract_openai_web_search_text(response) == "Answer from response.text"

    def test_falls_back_to_content_blocks(self) -> None:
        response = SimpleNamespace(
            text="",
            content_blocks=[
                {"type": "server_tool_call", "name": "web_search"},
                {
                    "type": "text",
                    "text": "Summarized search result",
                    "annotations": [{"type": "citation", "title": "Source"}],
                },
            ],
        )
        assert extract_openai_web_search_text(response) == "Summarized search result"

    def test_raises_when_no_text_is_present(self) -> None:
        response = SimpleNamespace(text="", content=[], content_blocks=[])
        try:
            extract_openai_web_search_text(response)
        except ValueError as exc:
            assert "no text content" in str(exc).lower()
        else:
            raise AssertionError("Expected ValueError when response has no text.")
