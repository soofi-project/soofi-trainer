"""Routing integration tests for the Interaction Agent.

Verifies that given a user message, the interaction agent consistently routes
to the correct sub-agent tool. Answer *content* is not checked — only which
tool(s) were called (TOOL_CALL_START events in the SSE stream).

WICHTIG — Testfragen müssen vollständig und kontextunabhängig sein:
Alle Sub-Agenten sind stateless. Fragen mit unaufgelösten Pronomen ("das", "dazu",
"dafür") sind keine gültigen Testfälle — sie würden auch im echten Betrieb nicht
so an Sub-Agenten weitergegeben. Der Interaction Agent ist dafür zuständig, solche
Referenzen vor dem Weiterleiten aufzulösen.

Run with:
    pytest tests/routing/ -m integration -v

Requirements: full Soofi stack running (docker compose up).
"""

import json
from typing import Any

import httpx
import pytest

AGENT_URL = "https://localhost:3001/api/agent"
# Generous timeout: LLM + sub-agent call can take 30–60 s under load
REQUEST_TIMEOUT = 90.0


# ---------------------------------------------------------------------------
# SSE helpers
# ---------------------------------------------------------------------------

def _parse_sse(raw: str) -> list[dict[str, Any]]:
    """Parse SSE text/event-stream into a list of JSON event dicts."""
    events = []
    for line in raw.splitlines():
        if line.startswith("data: "):
            try:
                events.append(json.loads(line[6:]))
            except json.JSONDecodeError:
                pass
    return events


def _tool_calls(events: list[dict[str, Any]]) -> list[str]:
    """Return ordered list of tool names from TOOL_CALL_START events."""
    return [e["tool"] for e in events if e.get("type") == "TOOL_CALL_START"]


def _training_view_opened(events: list[dict[str, Any]]) -> bool:
    """Return True if the training view was opened via STATE_SNAPSHOT.

    control_training_view has no ToolStreamTracker so it emits no TOOL_CALL_START.
    Instead it dispatches a STATE_SNAPSHOT with custom_component=soofi-training-progress.
    """
    return any(
        e.get("type") == "STATE_SNAPSHOT"
        and e.get("snapshot", {}).get("custom_component") == "soofi-training-progress"
        and e.get("snapshot", {}).get("action") == "open"
        for e in events
    )


def _route(
    message: str, history: list[dict[str, str]] | None = None
) -> tuple[list[str], list[dict[str, Any]]]:
    """Send a message (with optional history).

    Returns (tool_calls, all_events) so callers can inspect any event type.
    """
    messages: list[dict[str, str]] = list(history or [])
    messages.append({"role": "user", "content": message})
    with httpx.Client(timeout=REQUEST_TIMEOUT, verify=False) as client:
        resp = client.post(
            AGENT_URL,
            json={"messages": messages, "language": "de"},
        )
        resp.raise_for_status()
    events = _parse_sse(resp.text)
    return _tool_calls(events), events


# ---------------------------------------------------------------------------
# ask_advisor_tool — Fachfragen LLM-Spezialisierung
# ---------------------------------------------------------------------------

@pytest.mark.integration
@pytest.mark.parametrize("message", [
    "Was ist RAG?",
    "Erkläre mir LoRA",
    "Wann sollte ich Fine-Tuning statt RAG verwenden?",
    "Was ist QLoRA und wofür wird es verwendet?",
    "Was sind die Unterschiede zwischen SFT und DPO?",
])
def test_advisor_fachfrage(message: str) -> None:
    tools, _ = _route(message)
    assert "ask_advisor_tool" in tools, (
        f"Erwartet ask_advisor_tool für '{message}', aufgerufen: {tools}"
    )


# ---------------------------------------------------------------------------
# ask_advisor_tool — Soofi-Projekt
# ---------------------------------------------------------------------------

@pytest.mark.integration
@pytest.mark.parametrize("message", [
    "Was ist das Soofi-Projekt?",
    "Welche Partner sind beim Soofi-Projekt dabei?",
    "Was macht das DFKI im Soofi-Projekt?",
    "Erzähl mir von der 8ra-Initiative",
])
def test_advisor_soofi_projekt(message: str) -> None:
    tools, _ = _route(message)
    assert "ask_advisor_tool" in tools, (
        f"Erwartet ask_advisor_tool für '{message}', aufgerufen: {tools}"
    )


# ---------------------------------------------------------------------------
# ask_advisor_tool — Souveräne Modelle & Anwendungsfälle
# ---------------------------------------------------------------------------

@pytest.mark.integration
@pytest.mark.parametrize("message", [
    "Warum sind souveräne KI-Modelle wichtig?",
    "Welche offenen Sprachmodelle gibt es?",
    "Was sind strategische Risiken proprietärer Modelle?",
    "Für welche industriellen Anwendungsfälle sind souveräne Modelle relevant?",
])
def test_advisor_modelle_anwendungsfaelle(message: str) -> None:
    tools, _ = _route(message)
    assert "ask_advisor_tool" in tools, (
        f"Erwartet ask_advisor_tool für '{message}', aufgerufen: {tools}"
    )


# ---------------------------------------------------------------------------
# ask_advisor_tool — W-Fragen mit Pronomen (bekannte Problemfälle)
# ---------------------------------------------------------------------------

@pytest.mark.integration
@pytest.mark.parametrize("message", [
    # Pronomen aufgelöst — vollständige, kontextunabhängige Fragen
    "Für welche industriellen Anwendungsfälle sind souveräne KI-Modelle relevant?",
    "Welche offenen Sprachmodelle kommen für Fine-Tuning in Frage?",
    "Wie funktioniert LoRA genau?",
    "Warum sind souveräne Modelle strategisch wichtig?",
])
def test_advisor_w_frage_aufgeloest(message: str) -> None:
    """W-Fragen mit aufgelösten Referenzen müssen zum advisor geroutet werden."""
    tools, _ = _route(message)
    assert "ask_advisor_tool" in tools, (
        f"Erwartet ask_advisor_tool für '{message}', aufgerufen: {tools}"
    )


# ---------------------------------------------------------------------------
# ask_dataset_agent_tool
# ---------------------------------------------------------------------------

@pytest.mark.integration
@pytest.mark.parametrize("message", [
    "Suche Datensätze für Compliance",
    "Welche Trainingsdaten gibt es für Predictive Maintenance?",
    "Zeig mir Datensätze auf HuggingFace",
    "Welche Datenangebote gibt es im Datenraum?",
    # Vollständige Anfragen ohne unaufgelöste Pronomen:
    "Ich brauche Trainingsdaten für ein Compliance-Projekt",
    "Gibt es Datensätze für Compliance-Anwendungen?",
    "Suche Datensätze für LLM Fine-Tuning",
])
def test_dataset_agent_routing(message: str) -> None:
    tools, _ = _route(message)
    assert "ask_dataset_agent_tool" in tools, (
        f"Erwartet ask_dataset_agent_tool für '{message}', aufgerufen: {tools}"
    )
    assert "ask_advisor_tool" not in tools, (
        f"ask_advisor_tool fälschlicherweise aufgerufen für '{message}'"
    )


# ---------------------------------------------------------------------------
# ask_training_agent_tool — Status/Abbruch (kein Slot-Filling nötig)
# ---------------------------------------------------------------------------

@pytest.mark.integration
@pytest.mark.parametrize("message", [
    "Was ist der Status meines Trainings?",
    "Brich meinen Trainingsjob ab",
])
def test_training_agent_status_cancel_routing(message: str) -> None:
    """Status-Abfragen und Abbrüche gehen SOFORT an den Training Agent."""
    tools, _ = _route(message)
    assert "ask_training_agent_tool" in tools, (
        f"Erwartet ask_training_agent_tool für '{message}', aufgerufen: {tools}"
    )


# ---------------------------------------------------------------------------
# Slot-Filling: Training-Start ohne vollständige Parameter → kein Tool-Aufruf
# ---------------------------------------------------------------------------

@pytest.mark.integration
@pytest.mark.parametrize("message", [
    "Starte ein LoRA-Training",
    "Starte das Training mit QLoRA",
])
def test_training_start_incomplete_slots_no_tool(message: str) -> None:
    """Trainingsstart ohne vollständige Slots (kein Gesprächskontext) darf
    NICHT direkt an den Training Agent delegieren. Soofi soll stattdessen
    nach den fehlenden Parametern fragen (Anwendungsfall, Datensatz, Basismodell).
    """
    tools, _ = _route(message)
    assert "ask_training_agent_tool" not in tools, (
        f"ask_training_agent_tool fälschlicherweise aufgerufen für '{message}' "
        f"ohne vollständige Slots. Aufgerufen: {tools}"
    )


# ---------------------------------------------------------------------------
# show_agent_card
# ---------------------------------------------------------------------------

@pytest.mark.integration
@pytest.mark.parametrize("message", [
    "Welche Agenten gibt es?",
    "Zeig mir die Agentenkarte vom Advisor",
    "Was kann der Training Agent?",
])
def test_show_agent_card_routing(message: str) -> None:
    tools, _ = _route(message)
    assert "show_agent_card" in tools, (
        f"Erwartet show_agent_card für '{message}', aufgerufen: {tools}"
    )
    assert "ask_advisor_tool" not in tools, (
        f"ask_advisor_tool fälschlicherweise aufgerufen für '{message}'"
    )


# ---------------------------------------------------------------------------
# control_training_view
# ---------------------------------------------------------------------------

@pytest.mark.integration
@pytest.mark.parametrize("message", [
    "Zeig mir die Job-Übersicht",
    "Öffne die Trainingsansicht",
])
def test_training_view_routing(message: str) -> None:
    # control_training_view hat keinen ToolStreamTracker → kein TOOL_CALL_START.
    # Das Tool wird aufgerufen und erzeugt ein STATE_SNAPSHOT-Event.
    _, events = _route(message)
    assert _training_view_opened(events), (
        f"Erwartet STATE_SNAPSHOT(soofi-training-progress, open) für '{message}'. "
        f"Events: {[e.get('type') for e in events]}"
    )


# ---------------------------------------------------------------------------
# Begrüßung — kein Tool erwartet
# ---------------------------------------------------------------------------

@pytest.mark.integration
@pytest.mark.parametrize("message", [
    "Hallo",
    "Guten Morgen",
    "Hi",
])
def test_greeting_no_tool(message: str) -> None:
    tools, _ = _route(message)
    assert tools == [], (
        f"Begrüßung '{message}' sollte kein Tool aufrufen, aufgerufen: {tools}"
    )


# ---------------------------------------------------------------------------
# Mehrstufiger Workflow — Kontext-Auflösung
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_multiturn_usecase_to_dataset() -> None:
    """Nach Anwendungsfall-Bestätigung muss 'Ja' den dataset-agent triggern."""
    history = [
        {"role": "user", "content": "Für welche Anwendungsfälle sind souveräne Modelle relevant?"},
        {"role": "assistant", "content": (
            "Souveräne Modelle sind besonders relevant für: "
            "1. Compliance-Copilot, 2. Wissensmanagement, 3. Predictive Maintenance. "
            "Möchten Sie für einen dieser Anwendungsfälle ein Modell spezialisieren?"
        )},
        {"role": "user", "content": "Ja, für Compliance"},
        {"role": "assistant", "content": (
            "Compliance-Copilot: prüft Architekturentscheidungen gegen DSGVO, EU AI Act etc. "
            "Soll ich dazu passende Datensätze suchen?"
        )},
    ]
    tools, _ = _route("Ja, bitte", history=history)
    assert "ask_dataset_agent_tool" in tools, (
        f"Erwartet ask_dataset_agent_tool nach Datensatz-Frage, aufgerufen: {tools}"
    )


@pytest.mark.integration
def test_multiturn_dataset_to_model() -> None:
    """Nach Datensatz-Auswahl und expliziter Basismodell-Frage muss 'Ja' den advisor triggern.

    Der Interaction Agent stellt nach der Datensatz-Wahl die Übergangsfrage
    'Soll ich ein Basismodell empfehlen?' — darauf antwortet der Nutzer mit 'Ja'.
    """
    history = [
        {"role": "user", "content": "Suche Datensätze für Compliance"},
        {"role": "assistant", "content": (
            "Ich habe folgende Datensätze gefunden: "
            "1. EU-GDPR-QA, 2. LegalBench, 3. CUAD. "
            "Welchen Datensatz möchten Sie verwenden?"
        )},
        {"role": "user", "content": "den ersten"},
        {"role": "assistant", "content": (
            "Gut, EU-GDPR-QA ist ausgewählt. "
            "Soll ich ein passendes Basismodell für den Compliance-Anwendungsfall empfehlen?"
        )},
    ]
    tools, _ = _route("Ja, bitte", history=history)
    assert "ask_advisor_tool" in tools, (
        f"Erwartet ask_advisor_tool für Modellempfehlung nach Datensatz-Auswahl, aufgerufen: {tools}"
    )


@pytest.mark.integration
def test_multiturn_all_slots_triggers_training() -> None:
    """Wenn alle 4 Slots bekannt sind und der Nutzer bestätigt, muss ask_training_agent_tool ausgelöst werden."""
    history = [
        {"role": "user", "content": "Ich möchte ein Modell für Compliance spezialisieren."},
        {"role": "assistant", "content": "Soll ich dazu passende Datensätze suchen?"},
        {"role": "user", "content": "Ja"},
        {"role": "assistant", "content": (
            "Ich habe EU-GDPR-QA gefunden. Welchen Datensatz möchten Sie verwenden?"
        )},
        {"role": "user", "content": "EU-GDPR-QA"},
        {"role": "assistant", "content": (
            "Für Compliance empfehle ich Llama-3.1-8B als Basismodell. Soll ich dieses verwenden?"
        )},
        {"role": "user", "content": "Ja"},
        {"role": "assistant", "content": (
            "Für diesen Anwendungsfall empfehle ich LoRA als Methode. Soll ich das Training starten?"
        )},
    ]
    tools, _ = _route("Ja, bitte starte das Training", history=history)
    assert "ask_training_agent_tool" in tools, (
        f"Erwartet ask_training_agent_tool wenn alle 4 Slots bekannt sind, aufgerufen: {tools}"
    )
