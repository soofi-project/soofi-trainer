"""Minimal i18n for the Soofi Dataset Agent — DE/EN runtime toggle."""

from typing import Literal

Language = Literal["de", "en"]

_STRINGS: dict[str, dict[Language, str]] = {
    "searching_datasets": {
        "de": "Suche nach passenden Datensätzen",
        "en": "Searching for suitable datasets",
    },
    "processing_error": {
        "de": "Interner Fehler bei der Verarbeitung.",
        "en": "Internal error during processing.",
    },
    "no_response": {
        "de": "Keine Antwort generiert.",
        "en": "No response generated.",
    },
}


def tr(key: str, lang: Language, **kwargs: object) -> str:
    """Translate a key to the given language."""
    entry = _STRINGS.get(key)
    if entry is None:
        return key
    text = entry.get(lang, entry.get("de", key))
    if kwargs:
        text = text.format(**kwargs)
    return text
