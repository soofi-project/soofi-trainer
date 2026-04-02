"""Minimal i18n for the Soofi Interaction Agent — DE/EN runtime toggle."""

from typing import Literal

Language = Literal["de", "en"]

_STRINGS: dict[str, dict[Language, str]] = {
    # Tracker labels (SSE SEARCH_STATUS)
    "search_kb": {
        "de": "Suche in der Wissensdatenbank",
        "en": "Searching knowledge base",
    },
    "processing_training": {
        "de": "Verarbeite Trainingsauftrag\u2026",
        "en": "Processing training job\u2026",
    },
    "search_datasets": {
        "de": "Suche nach öffentlichen Datensätzen",
        "en": "Searching for public datasets",
    },
    "loading_agent_card": {
        "de": "Lade Agentenkarte\u2026",
        "en": "Loading agent card\u2026",
    },
    # Tool return labels
    "cards_closed": {"de": "Agentenkarten geschlossen.", "en": "Agent cards closed."},
    "agent_not_found": {
        "de": 'Agent "{agent}" nicht gefunden. Verfügbare Agenten: {available}',
        "en": 'Agent "{agent}" not found. Available agents: {available}',
    },
    "card_opened": {
        "de": "Agentenkarte geöffnet: {name}",
        "en": "Agent card opened: {name}",
    },
    "cards_opened": {
        "de": "{count} Agentenkarten geöffnet.",
        "en": "{count} agent cards opened.",
    },
    # Doc viewer labels
    "doc_closed": {"de": "Dokumentenansicht geschlossen.", "en": "Document viewer closed."},
    "doc_next": {"de": "Nächstes Dokument geöffnet.", "en": "Next document opened."},
    "doc_previous": {"de": "Vorheriges Dokument geöffnet.", "en": "Previous document opened."},
    "doc_opened": {"de": "Dokument {index} geöffnet.", "en": "Document {index} opened."},
    "doc_none": {
        "de": "Keine Quelldokumente im Gespräch vorhanden.",
        "en": "No source documents in the conversation.",
    },
    "doc_invalid_index": {
        "de": "Ungültiger Index {index}. Es gibt {total} Quelldokument(e) (1\u2013{total}).",
        "en": "Invalid index {index}. There are {total} source document(s) (1\u2013{total}).",
    },
    # Training view labels
    "training_view_opened": {
        "de": "Trainingsübersicht geöffnet.",
        "en": "Training overview opened.",
    },
    "training_view_closed": {
        "de": "Trainingsübersicht geschlossen.",
        "en": "Training overview closed.",
    },
    # SSE error
    "sse_error": {
        "de": "\n\n[Fehler bei der Verarbeitung]",
        "en": "\n\n[Error during processing]",
    },
    # Speech fallback
    "speech_fallback": {
        "de": "Ich habe folgendes gefunden.",
        "en": "Here is what I found.",
    },
}


def tr(key: str, lang: Language, **kwargs: object) -> str:
    """Translate a key to the given language. Supports {placeholder} formatting."""
    entry = _STRINGS.get(key)
    if entry is None:
        return key
    text = entry.get(lang, entry.get("de", key))
    if kwargs:
        text = text.format(**kwargs)
    return text
