"""Tests for web-search backend helper logic.

Pure helper tests only — these inline copies avoid importing graph.py, which
depends on langchain and other optional runtime packages.
"""

from types import SimpleNamespace


def get_searxng_web_search_config(env: dict[str, str]) -> dict[str, str]:
    """Inline copy of graph._get_searxng_web_search_config."""
    default_host = "http://searxng:8080"
    host = (env.get("INTERACTION_WEB_SEARCH_SEARXNG_HOST") or default_host).strip()
    if not host:
        host = default_host

    return {"host": host}


def get_openai_web_search_config(env: dict[str, str]) -> dict[str, str | None]:
    """Inline copy of graph._get_openai_web_search_config."""
    model = (env.get("INTERACTION_WEB_SEARCH_OPENAI_MODEL") or "gpt-5.4-mini-2026-03-17").strip()
    if not model:
        model = "gpt-5.4-mini-2026-03-17"

    return {
        "model": model,
        "base_url": "https://api.openai.com/v1",
        "api_key": (
            env.get("INTERACTION_WEB_SEARCH_OPENAI_API_KEY")
            or env.get("OPENAI_API_KEY")
            or None
        ),
    }


def get_openai_web_search_tool() -> dict[str, object]:
    """Inline copy of graph._get_openai_web_search_tool."""
    return {
        "type": "web_search",
        "user_location": {
            "type": "approximate",
            "country": "DE",
        },
    }


def get_openai_web_search_llm_kwargs(env: dict[str, str]) -> dict[str, str | bool]:
    """Inline copy of the kwargs assembled in graph._get_openai_web_search_llm."""
    config = get_openai_web_search_config(env)
    if not config["api_key"]:
        raise RuntimeError("OpenAI web search requires an API key.")

    return {
        "model": config["model"],
        "api_key": config["api_key"],
        "disable_streaming": True,
        "use_responses_api": True,
        "base_url": config["base_url"],
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


class TestSearxngWebSearchConfig:
    def test_uses_default_host_when_unset(self) -> None:
        config = get_searxng_web_search_config({})

        assert config == {"host": "http://searxng:8080"}

    def test_uses_dedicated_host_when_present(self) -> None:
        config = get_searxng_web_search_config(
            {"INTERACTION_WEB_SEARCH_SEARXNG_HOST": "http://search.internal:9090"}
        )

        assert config == {"host": "http://search.internal:9090"}

    def test_empty_host_falls_back_to_default(self) -> None:
        config = get_searxng_web_search_config({"INTERACTION_WEB_SEARCH_SEARXNG_HOST": "   "})

        assert config == {"host": "http://searxng:8080"}

    def test_ignores_openai_specific_env_vars(self) -> None:
        config = get_searxng_web_search_config(
            {
                "OPENAI_BASE_URL": "http://local-llm.invalid/v1",
                "INTERACTION_WEB_SEARCH_OPENAI_API_KEY": "dedicated-key",
            }
        )

        assert config == {"host": "http://searxng:8080"}


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
            "base_url": "https://api.openai.com/v1",
            "api_key": "dedicated-key",
        }

    def test_ignores_global_openai_base_url(self) -> None:
        env = {
            "OPENAI_BASE_URL": "http://local-llm.invalid/v1",
            "OPENAI_API_KEY": "fallback-key",
        }

        config = get_openai_web_search_config(env)

        assert config["model"] == "gpt-5.4-mini-2026-03-17"
        assert config["base_url"] == "https://api.openai.com/v1"
        assert config["api_key"] == "fallback-key"

    def test_empty_dedicated_model_falls_back_to_default(self) -> None:
        config = get_openai_web_search_config({"INTERACTION_WEB_SEARCH_OPENAI_MODEL": "   "})
        assert config["model"] == "gpt-5.4-mini-2026-03-17"

    def test_ignores_dedicated_search_base_url_override(self) -> None:
        env = {
            "OPENAI_BASE_URL": "http://local-llm.invalid/v1",
            "INTERACTION_WEB_SEARCH_OPENAI_BASE_URL": "https://proxy.example/v1",
            "OPENAI_API_KEY": "fallback-key",
        }

        config = get_openai_web_search_config(env)

        assert config["base_url"] == "https://api.openai.com/v1"


class TestOpenAIWebSearchClientKwargs:
    def test_disables_streaming_and_uses_responses_api(self) -> None:
        kwargs = get_openai_web_search_llm_kwargs({"OPENAI_API_KEY": "fallback-key"})

        assert kwargs == {
            "model": "gpt-5.4-mini-2026-03-17",
            "api_key": "fallback-key",
            "disable_streaming": True,
            "use_responses_api": True,
            "base_url": "https://api.openai.com/v1",
        }


class TestOpenAIWebSearchTool:
    def test_uses_ga_web_search_with_germany_location(self) -> None:
        tool = get_openai_web_search_tool()

        assert tool == {
            "type": "web_search",
            "user_location": {
                "type": "approximate",
                "country": "DE",
            },
        }


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
