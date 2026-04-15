# Task

- user story: [US-03](US-03-agent-architecture.md)

/label ~UserStory_US-03
/label ~Task
/label ~Done
/milestone %Sprint3

# Description

**Stateless Sub-Agents & Flow-Orchestrierung im Interaction Agent**

Überarbeitung der Agenten-Architektur: alle Sub-Agenten (Advisor, Dataset Agent, Training Agent)
werden stateless, die gesamte Gesprächssteuerung (Übergangsfragen, Workflow-Progression)
liegt ausschließlich beim Interaction Agent.

## Motivation

Bisher erhielten Sub-Agenten eine `context_id` und hatten damit Zugriff auf den A2A-Gesprächsverlauf.
Das führte dazu, dass der Advisor Folgefragen aus dem Kontext beantwortete, anstatt die Wissensdatenbank
zu befragen. Außerdem steuerten Sub-Agenten selbst den Workflow-Dialog (Übergangsfragen nach
Anwendungsfall-Listen, Datensatz-Auswahl usw.), obwohl nur der Interaction Agent den vollständigen
Gesprächsüberblick hat.

## Änderungen

### Stateless Sub-Agenten (`interaction-agent/src/graph.py`, `agent.py`)

- Alle drei Sub-Agenten werden mit `context_id=None` aufgerufen — kein A2A-Session-Kontext
- `_training_context_id` und `_dataset_context_id` ContextVars entfernt
- `set_training_context_id()` und `set_dataset_context_id()` Setter entfernt
- `_advisor_context_id` bleibt erhalten, wird aber nur noch für den RAG-URL-Store (Source-Panel) genutzt

### Prompts der Sub-Agenten

**`advisor/src/prompts.py`**
- Referenz auf Gesprächsverlauf entfernt: "Jede Anfrage ist eigenständig"
- Alle Flow-Guidance-Regeln entfernt (Übergangsfragen nach Anwendungsfall-Listen, Datensatz-Auswahl,
  Basismodell-Empfehlung, Methoden-Empfehlung) — Verantwortung liegt beim Interaction Agent
- Vollständige Topic-Filter-Dokumentation für `search_documents` ergänzt
- Pflicht zur Wissensdatenbank-Suche auch bei Folgefragen explizit gemacht

**`training-agent/src/training_agent/prompts.py`**
- Referenz auf Gesprächsverlauf entfernt: "Jede Anfrage ist eigenständig"

**`dataset-agent/src/dataset_agent/prompts.py`**
- Referenz auf Gesprächsverlauf entfernt: "Jede Anfrage ist eigenständig"
- Sektion "Modellspezialisierungs-Workflow" (Auswahlfrage nach Datensatz-Auflistung) entfernt

### Interaction Agent Prompt (`interaction-agent/src/prompts.py`)

- Alle drei Sub-Agenten als stateless dokumentiert — vollständige, kontextunabhängige Anfragen
- Pronomen/Referenzen-Auflösung vor jedem Sub-Agenten-Aufruf explizit gefordert
- Schritt 8 (Kurzantwort-Erkennung): W-Fragen ("welche", "für welche", "wie" ...) werden
  nicht mehr als Kurzantworten klassifiziert → fallen durch auf Schritt 3 → `ask_advisor_tool`
- Schritt 10 (neu): Übergangsfragen-Logik im Interaction Agent:
  - Advisor hat Anwendungsfälle aufgelistet → "Möchten Sie für einen dieser Anwendungsfälle ein Modell spezialisieren?"
  - Advisor hat Anwendungsfall bestätigt → "Soll ich dazu passende Datensätze suchen?"
  - Dataset Agent hat Datensätze aufgelistet → "Welchen Datensatz möchten Sie verwenden?"
  - Advisor hat Basismodell empfohlen → "Soll ich dieses Modell verwenden?"
  - Advisor hat Methode empfohlen → "Soll ich das Training damit starten?"
  - Sachliche Antwort ohne Workflow-Bezug → keine Übergangsfrage

### SSE Streaming (`interaction-agent/src/sse_stream.py`)

- `ToolStreamTracker` erhält `finished`-Flag, das bei `on_tool_end` gesetzt wird
- `_handle_chat_stream` unterdrückt LLM-Output nur noch während eines laufenden Tool-Streams
  (`streamed and not finished`), nicht mehr pauschal nach jedem Tool-Aufruf
- Damit erreicht der zweite LLM-Call (Übergangsfrage) den Client
- `_STREAMING_TOOLS` in `graph.py` auf leeres Set gesetzt — kein Short-Circuit mehr für
  irgendein Sub-Agenten-Tool

### Soofi UI (`soofi-ui/src/main.ts`)

- `TOOL_CALL_END`-Handler setzt `streaming = false` nicht mehr für Advisor, Dataset Agent
  oder Training Agent
- `streaming = false` erfolgt einheitlich erst bei `RUN_FINISHED` (bereits in `finally`-Clause)
- Dadurch kann der Nutzer erst tippen, nachdem die Übergangsfrage vollständig erschienen ist

## Akzeptanzkriterien

- [x] Advisor ruft bei jeder Fachfrage `search_documents` auf, auch bei Folgefragen
- [x] Folgefrage "Für welche Anwendungsfälle?" triggert Wissensdatenbank-Suche
- [x] Interaction Agent stellt Übergangsfragen nach Advisor- und Dataset-Antworten
- [x] Sub-Agenten-Streaming-Visualisierung (Search-Status, Chunks, RAG-Sources) unverändert
- [x] Nutzer kann erst nach Abschluss der Übergangsfrage neu eingeben

# Branches

- feature/T-10-9-demo-workflow
