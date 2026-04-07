# Task

- user story: [US-10](US-10-demo-preparation.md)

/label ~UserStory_US-10
/label ~Task
/label ~ToDo

# Description

**Session-Logs als agentenlesbare Markdown-Dateien**

Nach jeder Benutzer-Session mit Soofi Trainer wird sofort eine Protokolldatei in `session-logs/`
angelegt und bei jedem Event kontinuierlich fortgeschrieben. Das Format ist dual-purpose:
human-readable für manuelle Analyse UND maschinenlesbar für einen Coding-Agent, der eine Menge
von Logs auswertet, gewichtete Verbesserungsvorschläge ableitet und automatisch neue Tasks anlegt.

## Motivation

Session-Logs sind die Grundlage für einen selbstverstärkenden Verbesserungskreislauf:

```
Sessions → Logs → Agent-Analyse → gewichtete Refinement-Liste → neue Tasks → Umsetzung → bessere Sessions
```

Der Analyse-Agent (Claude Code) soll ohne menschliche Vorarbeit aus einem `session-logs/`-Ordner
automatisch erkennen, wo Nutzer scheitern, wo Antworten zu lang oder unscharf sind, und daraus
priorisierte Tasks generieren, die nach und nach abgearbeitet werden können.

## Log-Format

### Design-Prinzipien

1. **YAML-Frontmatter für Metadaten** — maschinell parsebar ohne Regex-Hacks
2. **Strukturierte Signal-Annotationen** — jedes Event trägt ein `type:`-Tag, das der Agent
   direkt filtern kann (kein Free-Text-Parsing nötig)
3. **Friction-Signale explizit kodiert** — Korrekturen, Wiederholungen, Abbrüche sind als
   eigene Event-Typen modelliert, nicht nur implizit im Text enthalten
4. **Zeitstempel pro Eintrag** — ermöglicht Latenzmessung zwischen User-Input und Agent-Antwort

### Dateiformat

```markdown
---
session_id: a3f8c1d2
started_at: 2026-04-05T14:32:07
ended_at: 2026-04-05T14:36:19
duration_s: 252
language: de
end_reason: normal          # normal | timeout | error | abandoned
message_count: 6
advisor_calls: 2
training_calls: 0
rag_sources_total: 3
recommendation: lora_finetuning   # lora_finetuning | qlora | rag | none
training_started: false
friction_events: 2          # Summe aller friction-type Events in dieser Session
---

# Soofi Session — 2026-04-05 14:32:07

## Verlauf

<!-- type:user ts:14:32:07 -->
**[14:32:07] Benutzer:**
Ich möchte ein Modell für die Klassifikation von Fertigungsdaten fein-tunen.

<!-- type:tool_call tool:ask_advisor ts:14:32:08 query:"Fein-Tuning Klassifikation Fertigung" -->
**[14:32:08] → Advisor** *(Suche: "Fein-Tuning Klassifikation Fertigung")*

<!-- type:rag_sources ts:14:32:11 -->
**[14:32:11] RAG-Quellen:**
- `fine-tuning-guide.pdf` § Methodik — Score: 0.91
- `manufacturing-datasets.pdf` § Überblick — Score: 0.87

<!-- type:agent ts:14:32:11 latency_ms:3240 -->
**[14:32:11] Soofi:**
Für Ihren Anwendungsfall empfehle ich **LoRA Fine-Tuning** ...

<!-- type:user ts:14:33:05 -->
**[14:33:05] Benutzer:**
Welche Datenmenge brauche ich mindestens?

<!-- type:agent ts:14:33:08 latency_ms:2890 -->
**[14:33:08] Soofi:**
Für LoRA Fine-Tuning sind typischerweise 500–2000 annotierte Beispiele ausreichend ...

<!-- type:friction subtype:correction confidence:low ts:14:34:22 -->
<!-- friction: Benutzer korrigiert vorherige Eingabe — "nein, ich meine Textklassifikation,
     nicht Bildklassifikation" — Agent hatte Domäne falsch interpretiert -->
**[14:34:22] Benutzer:**
Nein, ich meine Textklassifikation, nicht Bildklassifikation.

<!-- type:agent ts:14:34:25 latency_ms:2100 -->
**[14:34:25] Soofi:**
Entschuldigung — für Textklassifikation gilt ...

## Empfehlung

<!-- type:recommendation -->
| Aspekt | Wert |
|--------|------|
| Methode | LoRA Fine-Tuning |
| Basis-Modell | — |
| Training gestartet | Nein |
```

### Event-Typen (`type:`)

| Typ | Bedeutung | Analyse-Relevanz |
|-----|-----------|-----------------|
| `user` | Benutzer-Nachricht | Themenextraktion, Fragetypen |
| `agent` | Agenten-Antwort | Latenz, Antwortqualität |
| `tool_call` | Tool-Aufruf (Advisor, Training) | Tool-Nutzungsmuster |
| `rag_sources` | Zurückgegebene RAG-Quellen | Relevanz, fehlende Dokumente |
| `recommendation` | Abschließende Empfehlung | Methodenverteilung |
| `friction` | Reibungsereignis (s. u.) | **Hauptquelle für Refinements** |
| `error` | Fehler / Exception | Technische Bugs |
| `session_end` | Abschluss-Event | End-Reason-Verteilung |

### Friction-Subtypes

Friction-Events sind die wichtigsten Signale für den Analyse-Agent. Sie werden explizit
annotiert, damit der Agent nicht aus Prosa-Text schließen muss, was schiefgelaufen ist:

| Subtype | Bedeutung | Beispiel |
|---------|-----------|---------|
| `correction` | Nutzer korrigiert Missverständnis des Agents | "Nein, ich meine X, nicht Y" |
| `repetition` | Nutzer stellt dieselbe Frage erneut | Zweite Frage nach bereits beantworteten Infos |
| `clarification_request` | Agent konnte Anfrage nicht verstehen | "Können Sie das präzisieren?" |
| `incomplete_answer` | Nutzer signalisiert unvollständige Antwort | "Und was ist mit X?" als Follow-up |
| `abandoned` | Session endet ohne Ergebnis | Kein `recommendation`-Event, `end_reason: abandoned` |
| `tool_failure` | Tool-Aufruf schlug fehl | Advisor nicht erreichbar, Timeout |

## Analyse-Agent-Workflow

Ein separater Task (T-10-6) beschreibt den Analyse-Agent selbst. T-10-5 legt das Fundament:
das Log-Format muss so gestaltet sein, dass der Agent folgende Aufgaben ohne Ambiguität
ausführen kann:

1. **Batch-Lesen**: Alle `.md`-Dateien in `session-logs/` einlesen, YAML-Frontmatter parsen
2. **Friction-Aggregation**: Alle `type:friction`-Events über alle Sessions sammeln und
   nach `subtype` gruppieren
3. **Gewichtung**: `score = frequency × severity × recency_factor` (z. B. `abandoned` > `correction` > `repetition`; Sessions < 24 h mit Faktor 1.5, älter als 7 d mit 0.6)
4. **Refinement-Extraktion**: Pro Friction-Cluster einen Verbesserungsvorschlag formulieren
5. **Task-Anlage**: Automatisch Issues in `docs/issues/` als Markdown-Dateien erstellen

### Beispiel-Output des Analyse-Agents

```
Analyse von 23 Sessions (2026-04-05 – 2026-04-07):

Rang 1 (Score 18): correction × 9 — Agent verwechselt Text- und Bildklassifikation
  → Task: System-Prompt um explizite Domänen-Klärungsfrage erweitern

Rang 2 (Score 12): clarification_request × 6 — "Datenmenge" zu unspezifisch beantwortet
  → Task: RAG-Dokument "Faustregel Trainingsdaten" ergänzen

Rang 3 (Score 8): abandoned × 4 — Sessions enden ohne Training-Start
  → Task: Proaktiver CTA "Training jetzt starten?" nach Empfehlung einbauen
```

## Technischer Ansatz

### Implementierungsort

`interaction-agent/src/session_logger.py` — neue `SessionLogger`-Klasse. Der Interaction
Agent kennt den vollständigen Gesprächsverlauf (LangGraph-State, SSE-Events) und ist damit
der einzig sinnvolle Ort für das Logging.

### Schreibstrategie

- Datei wird beim **ersten** Request einer neuen `conversation_id` sofort angelegt
- Jeder neue Eintrag wird per `file.flush()` direkt auf Disk geschrieben — kein Puffern
- YAML-Frontmatter wird am **Ende** einmalig vollständig geschrieben (Seek to start),
  da Zähler (message_count, friction_events etc.) erst beim Abschluss feststehen
- Gesprächsverlauf wächst durch reines Append — kein Rewrite des Hauptblocks nötig

### Friction-Erkennung

Friction-Events werden **nicht automatisch** vom Agent erkannt (zu fehleranfällig). Stattdessen:

- `correction`: Heuristik — Benutzer-Nachricht enthält "nein", "falsch", "ich meine" o. ä.
  → Logger annotiert als **Kandidat**, mit `confidence:low` oder `confidence:high`
- `tool_failure`, `error`: Direkt aus Exceptions / Error-Events
- `abandoned`: Aus `end_reason=timeout` + kein `recommendation`-Event

Die Heuristik erzeugt False Positives — der Analyse-Agent soll dies berücksichtigen
(`confidence: low` Events geringer gewichten).

### Neue Dateien / Änderungen

| Datei | Änderung |
|-------|---------|
| `interaction-agent/src/session_logger.py` | Neu — `SessionLogger`-Klasse |
| `interaction-agent/src/agent.py` | Logger initialisieren & finalisieren |
| `interaction-agent/src/graph.py` | Logger-Einträge bei Tool-Aufrufen schreiben |
| `compose/interaction.yml` | Volume-Mount für `session-logs/` |
| `.env` | `SESSION_LOG_ENABLED`, `SESSION_LOG_DIR`, `SESSION_LOG_TIMEOUT_S` |
| `.gitignore` | `session-logs/` ausschließen |

### Volume-Mount

```yaml
# compose/interaction.yml
interaction-agent:
  volumes:
    - ./session-logs:/app/session-logs
```

### Konfiguration (`.env`)

```env
SESSION_LOG_ENABLED=true
SESSION_LOG_DIR=/app/session-logs
SESSION_LOG_TIMEOUT_S=300
```

## Acceptance Criteria

- [ ] Datei wird beim **ersten** Request einer neuen Session sofort angelegt
- [ ] Jeder Eintrag wird sofort geflusht — Log ist bei Absturz vollständig bis zum letzten Event
- [ ] YAML-Frontmatter enthält alle Pflichtfelder (session_id, started_at, end_reason, friction_events, …)
- [ ] Alle Event-Typen (`user`, `agent`, `tool_call`, `rag_sources`, `friction`, `error`) werden korrekt annotiert
- [ ] Friction-Kandidaten werden mit `confidence`-Flag annotiert
- [ ] Latenz (`latency_ms`) wird pro `agent`-Event berechnet und eingetragen
- [ ] YAML-Frontmatter wird beim Session-Abschluss vollständig geschrieben
- [ ] `end_reason` ist immer gesetzt (`normal | timeout | error | abandoned`)
- [ ] Logging per `SESSION_LOG_ENABLED=false` deaktivierbar
- [ ] Volume-Mount konfiguriert — Logs überleben Container-Neustart
- [ ] `session-logs/` in `.gitignore`

# Branches

- feature/T-10-5-session-logs
