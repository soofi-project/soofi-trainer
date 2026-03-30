"""LLM configuration helpers for the Soofi Advisor."""

import os
from typing import Any

_TRUE_VALUES = {"1", "true", "yes", "on"}
_FALSE_VALUES = {"0", "false", "no", "off"}


def _get_optional_env(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None
    value = value.strip()
    return value or None


def _get_required_env(name: str) -> str:
    value = _get_optional_env(name)
    if value is None:
        raise RuntimeError(f"{name} env var required.")
    return value


def _parse_float(name: str, default: str) -> float:
    raw = _get_optional_env(name) or default
    try:
        return float(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} env var must be a float, got {raw!r}.") from exc


def _parse_int(name: str, default: str) -> int:
    raw = _get_optional_env(name) or default
    try:
        return int(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} env var must be an integer, got {raw!r}.") from exc


def _parse_bool(name: str, default: bool) -> bool:
    raw = _get_optional_env(name)
    if raw is None:
        return default
    normalized = raw.lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False
    raise RuntimeError(
        f"{name} env var must be a boolean (true/false/1/0/yes/no/on/off), got {raw!r}."
    )


def build_llm_kwargs(model_env_var: str, prefix: str) -> dict[str, Any]:
    """Build ChatOpenAI kwargs from per-agent environment variables."""
    base_url = _get_optional_env("OPENAI_BASE_URL")
    llm_kwargs: dict[str, Any] = {
        "model": _get_required_env(model_env_var),
        "temperature": _parse_float(f"{prefix}_TEMPERATURE", "1.0"),
        "top_p": _parse_float(f"{prefix}_TOP_P", "0.95"),
        "presence_penalty": _parse_float(f"{prefix}_PRESENCE_PENALTY", "1.0"),
    }
    if not base_url:
        return llm_kwargs

    llm_kwargs["openai_api_base"] = base_url
    llm_kwargs["extra_body"] = {
        "top_k": _parse_int(f"{prefix}_TOP_K", "20"),
        "min_p": _parse_float(f"{prefix}_MIN_P", "0.0"),
        "repetition_penalty": _parse_float(f"{prefix}_REPEAT_PENALTY", "1.0"),
        "chat_template_kwargs": {
            "enable_thinking": _parse_bool(f"{prefix}_ENABLE_THINKING", False)
        },
    }
    return llm_kwargs
