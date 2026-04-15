"""Tests for web-search backend helper logic.

Pure helper tests only — these inline copies avoid importing graph.py, which
depends on langchain and other optional runtime packages.
"""


def get_searxng_web_search_config(env: dict[str, str]) -> dict[str, str]:
    """Inline copy of graph._get_searxng_web_search_config."""
    default_host = "http://searxng:8080"
    host = (env.get("INTERACTION_WEB_SEARCH_SEARXNG_HOST") or default_host).strip()
    if not host:
        host = default_host

    return {"host": host}


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
