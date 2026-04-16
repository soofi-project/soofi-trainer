"""System prompts for the Soofi Dataset Agent (DE + EN)."""

from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent / "prompts"


def _load(name: str) -> str:
    return (_PROMPTS_DIR / name).read_text(encoding="utf-8")


SYSTEM_PROMPT_DE = _load("system_de.md")
SYSTEM_PROMPT_EN = _load("system_en.md")
