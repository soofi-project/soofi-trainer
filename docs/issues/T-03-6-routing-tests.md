# Task

- user story: [US-03](US-03-agent-architecture.md)

/label ~UserStory_US-03
/label ~Task
/label ~ToDo
/milestone %Sprint3

# Description

**Routing-Integrationstests für den Interaction Agent**

Systematische Tests, die prüfen ob der Interaction Agent bei gegebenen Nutzereingaben
konsistent das richtige Sub-Agenten-Tool aufruft. Fehlschlagende Tests sind direkte
Hinweise auf Prompt-Lücken.

## Ansatz

**Ebene: Behavior-Tests auf dem laufenden Stack**
- HTTP POST an `/api/agent` (via nginx, Port 3001)
- SSE-Stream parsen, `TOOL_CALL_START`-Events extrahieren
- Assertion: erwartetes Tool taucht im Stream auf
- Antwortinhalt wird NICHT geprüft (nicht-deterministisch)
- Marker `@pytest.mark.integration` — nur bei laufendem Stack ausführen

## Testfälle

### ask_advisor_tool — Fachfragen LLM-Spezialisierung
- "Was ist RAG?"
- "Erkläre mir LoRA"
- "Wann sollte ich Fine-Tuning statt RAG verwenden?"
- "Was ist QLoRA und wofür wird es verwendet?"

### ask_advisor_tool — Soofi-Projekt
- "Was ist das Soofi-Projekt?"
- "Welche Partner sind beim Soofi-Projekt dabei?"
- "Was macht das DFKI im Soofi-Projekt?"

### ask_advisor_tool — Souveräne Modelle & Anwendungsfälle
- "Warum sind souveräne KI-Modelle wichtig?"
- "Welche offenen Sprachmodelle gibt es?"
- "Für welche industriellen Anwendungsfälle sind souveräne Modelle relevant?"
- ⚠️ "Für welche Anwendungsfälle wäre das relevant?" (W-Frage mit Pronomen)
- ⚠️ "Welche Modelle kommen dafür in Frage?" (W-Frage mit Pronomen)

### ask_dataset_agent_tool
- "Suche Datensätze für Compliance"
- "Welche Trainingsdaten gibt es für Predictive Maintenance?"
- "Zeig mir Datensätze auf HuggingFace"
- "Welche Datenangebote gibt es im Datenraum?"
- ⚠️ "Gibt es dazu passende Datensätze?" (Grenzfall Advisor/Dataset)

### ask_training_agent_tool
- "Starte ein LoRA-Training"
- "Was ist der Status meines Trainings?"

### show_agent_card
- "Welche Agenten gibt es?"
- "Zeig mir die Agentenkarte vom Advisor"

### control_training_view
- "Zeig mir die Job-Übersicht"
- "Öffne die Trainingsansicht"

### Kein Tool (Begrüßung)
- "Hallo" → kein TOOL_CALL_START erwartet

## Implementierung

- `tests/routing/conftest.py` — Stack-Verfügbarkeit prüfen, Tests überspringen wenn nicht erreichbar
- `tests/routing/test_interaction_routing.py` — Parametrisierte Testfälle
- Ausführung: `pytest tests/routing/ -m integration`

## Akzeptanzkriterien

- [ ] Alle nicht-markierten Testfälle bestehen
- [ ] ⚠️-Fälle (Pronomen, Grenzfälle) bestehen oder sind als `xfail` dokumentiert
- [ ] Tests laufen in < 5 min durch (parallele Ausführung)
- [ ] `conftest.py` überspringt Tests wenn Stack nicht läuft

# Branches

- feature/T-03-6-routing-tests
