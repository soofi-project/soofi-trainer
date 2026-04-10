"""Tests for interaction-agent system prompts."""

from src.prompts import get_system_prompt


class TestSystemPrompts:
    def test_german_prompt_mentions_web_search_tool(self) -> None:
        prompt = get_system_prompt("de")
        assert "**web_search_tool**" in prompt
        assert "Websuche" in prompt
        assert "aktuellen, neuesten oder kürzlichen öffentlichen Informationen" in prompt

    def test_english_prompt_mentions_web_search_tool(self) -> None:
        prompt = get_system_prompt("en")
        assert "**web_search_tool**" in prompt
        assert "current, latest, or recent public information" in prompt

    def test_dataset_priority_over_web_search_in_german_prompt(self) -> None:
        prompt = get_system_prompt("de")
        assert "ask_dataset_agent_tool aufrufen" in prompt
        assert "ask_dataset_agent_tool Vorrang" in prompt
        assert "web_search_tool" in prompt

    def test_training_priority_over_web_search_in_english_prompt(self) -> None:
        prompt = get_system_prompt("en")
        assert "ask_dataset_agent_tool has priority" in prompt
        assert "training tools take priority over web_search_tool" in prompt
