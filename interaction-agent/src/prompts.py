"""System prompts for the Soofi Interaction Agent (DE + EN)."""

from pathlib import Path

from .i18n import Language

_PROMPTS_DIR = Path(__file__).parent / "prompts"


def _load(name: str) -> str:
    return (_PROMPTS_DIR / name).read_text(encoding="utf-8")


def get_system_prompt(lang: Language) -> str:
    """Return the system prompt for the given language."""
    if lang == "en":
        return _load("system_en.md")
    return _load("system_de.md")


def get_slot_extraction_prompt(lang: Language) -> str:
    """Return the slot-extraction prompt for the given language."""
    if lang == "en":
        return _load("slot_extraction_en.md")
    return _load("slot_extraction_de.md")
