"""System prompts for the Soofi Interaction Agent (DE + EN)."""

import os
from datetime import date
from pathlib import Path

from .i18n import Language

_PROMPTS_DIR = Path(__file__).parent / "prompts"

_DEFAULT_CITY = os.getenv("INTERACTION_DEFAULT_CITY")
if not _DEFAULT_CITY:
    raise RuntimeError("INTERACTION_DEFAULT_CITY env var required.")


def _load(name: str) -> str:
    return (_PROMPTS_DIR / name).read_text(encoding="utf-8")


def get_system_prompt(lang: Language) -> str:
    """Return the system prompt for the given language."""
    prompt = _load("system_en.md") if lang == "en" else _load("system_de.md")
    return prompt.replace("%DEFAULT_CITY%", _DEFAULT_CITY).replace(
        "%CURRENT_DATE%", date.today().isoformat()
    )


def get_slot_extraction_prompt(lang: Language) -> str:
    """Return the slot-extraction prompt for the given language."""
    if lang == "en":
        return _load("slot_extraction_en.md")
    return _load("slot_extraction_de.md")
