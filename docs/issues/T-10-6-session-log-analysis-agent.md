# Task

- user story: [US-10](US-10-demo-preparation.md)
- depends on: [T-10-5](T-10-5-session-logs.md)

/label ~UserStory_US-10
/label ~Task
/label ~ToDo

# Description

**Analyse-Agent: Session-Logs → gewichtete Refinement-Tasks**

Ein Coding-Agent (Claude Code) liest alle Dateien in `session-logs/`, aggregiert
Friction-Events und Nutzungsmuster, bewertet diese nach Häufigkeit und Schwere und legt
automatisch priorisierte Verbesserungs-Tasks als Markdown-Dateien in `docs/issues/` an.

Der Agent läuft auf Abruf (`/analyse-sessions`) oder geplant nach einer Demo-Session. Er
braucht keine externe Infrastruktur — nur Zugriff auf `session-logs/` und `docs/issues/`.

## Workflow

```
session-logs/*.md
       │
       ▼
  [1] Parse          YAML-Frontmatter + type:-Annotationen aller Dateien einlesen
       │
       ▼
  [2] Aggregate      Friction-Events nach subtype gruppieren, Häufigkeiten zählen,
                     confidence:low Events mit Faktor 0.5 gewichten
       │
       ▼
  [3] Score          Gewichtungsformel pro Friction-Cluster (s. u.)
       │
       ▼
  [4] Cluster        Ähnliche Friction-Events zu einem Refinement-Thema zusammenfassen
                     (z. B. alle "correction"-Events mit "Klassifikation" → ein Cluster)
       │
       ▼
  [5] Synthesize     Pro Cluster einen konkreten Verbesserungsvorschlag formulieren
       │
       ▼
  [6] Create Tasks   Für jeden Vorschlag ab Score-Schwellwert eine Task-Datei anlegen
```

## Gewichtungsformel

```
score = frequency × severity × recency_factor

severity:
  abandoned            → 4
  tool_failure         → 3
  correction           → 2
  clarification_request → 2
  incomplete_answer    → 1
  repetition           → 1

recency_factor:
  Session in den letzten 24 h  → 1.5
  Session in den letzten 7 d   → 1.0
  älter                        → 0.6

confidence:low Events zählen mit Faktor 0.5
```

Nur Cluster mit `score ≥ 3.0` erhalten einen Task (konfigurierbar via `MIN_SCORE`).

## Analyse-Prompt (Agent-Instruktion)

Der Agent wird mit folgendem Prompt gestartet (in `tools/analyse_sessions.md` versioniert):

```
Du bist ein Analyse-Agent für Soofi Trainer Session-Logs.

Aufgabe:
1. Lies alle .md-Dateien in session-logs/ ein.
2. Parse den YAML-Frontmatter jeder Datei.
3. Extrahiere alle <!-- type:friction ... -->-Annotationen aus dem Gesprächsverlauf.
4. Aggregiere Friction-Events nach subtype. Gewichte confidence:low mit Faktor 0.5.
5. Berechne pro Cluster den Score: frequency × severity × recency_factor (Formeln s. u.).
6. Fasse ähnliche Ereignisse zu thematischen Clustern zusammen.
7. Formuliere pro Cluster einen konkreten Verbesserungsvorschlag (max. 3 Sätze).
8. Lege für jeden Cluster mit score ≥ MIN_SCORE eine neue Task-Datei in docs/issues/ an.
   Verwende das Task-Template aus docs/issues/_template_task.md.
   Nummeriere nach dem höchsten vorhandenen T-XX-Y im Verzeichnis.
9. Gib eine Zusammenfassung aller erzeugten Tasks aus.

Severity-Tabelle: abandoned=4, tool_failure=3, correction=2,
clarification_request=2, incomplete_answer=1, repetition=1.
MIN_SCORE=3.0 (Standard).
```

## Output-Format (erzeugter Task)

Jeder vom Analyse-Agent angelegte Task folgt dem Standard-Template und enthält
einen zusätzlichen `## Analyse-Grundlage`-Block:

```markdown
# Task

- user story: [US-XX](...)
- generated_by: session-log-analysis
- analysis_date: 2026-04-07
- source_sessions: 23
- friction_cluster: correction / Domänen-Disambiguierung
- cluster_score: 18.0

/label ~GeneratedByAnalysis
/label ~Task
/label ~ToDo

# Description

**[Agent-formulierter Titel]**

[Agent-formulierte Beschreibung, max. 3 Sätze]

## Analyse-Grundlage

| Metrik | Wert |
|--------|------|
| Friction-Subtype | correction |
| Häufigkeit | 9 × in 23 Sessions |
| Score | 18.0 |
| Betroffene Sessions | `a3f8c1d2`, `b7e2a091`, … |
| Repräsentatives Beispiel | "Nein, ich meine Textklassifikation, nicht Bildklassifikation" |

## Acceptance Criteria

- [ ] [Agent-generierte Kriterien]
```

## Implementierung

### Aufruf-Mechanismus

Der Analyse-Agent wird als **Claude Code Skill** (`/analyse-sessions`) implementiert.
Die Instruktions-Datei liegt unter `tools/analyse_sessions.md` und wird vom Skill geladen.

```bash
# Manueller Aufruf nach Demo-Session:
/analyse-sessions

# Optionale Parameter (als natürlichsprachliche Ergänzung):
/analyse-sessions letzte 24h
/analyse-sessions MIN_SCORE=5
```

### Skill-Datei (`tools/analyse_sessions.md`)

Enthält den vollständigen Analyse-Prompt (s. o.) plus Kontext-Links zu:
- Log-Format-Spezifikation: `docs/issues/T-10-5-session-logs.md`
- Task-Template: `docs/issues/_template_task.md`
- Severity-Tabelle und Gewichtungsformel

### Task-Template (`docs/issues/_template_task.md`)

Neues Standard-Template, das sowohl manuell als auch vom Analyse-Agent verwendet wird.
Stellt sicher, dass alle erzeugten Tasks dasselbe Schema haben.

### Neue Dateien / Änderungen

| Datei | Änderung |
|-------|---------|
| `tools/analyse_sessions.md` | Neu — Analyse-Prompt / Skill-Instruktion |
| `docs/issues/_template_task.md` | Neu — Standard-Task-Template |
| `.claude/commands/analyse-sessions.md` | Neu — Slash-Command-Definition |

## Acceptance Criteria

- [ ] `/analyse-sessions` startet den Analyse-Workflow ohne manuelle Vorbereitung
- [ ] Agent liest alle `session-logs/*.md` und parst YAML-Frontmatter korrekt
- [ ] Friction-Events werden nach subtype aggregiert, `confidence:low` mit 0.5 gewichtet
- [ ] Score wird nach Formel (frequency × severity × recency_factor) berechnet
- [ ] Cluster mit `score ≥ 3.0` erhalten automatisch eine Task-Datei in `docs/issues/`
- [ ] Erzeugte Tasks enthalten den `## Analyse-Grundlage`-Block mit Metriken und Beispielen
- [ ] Task-Nummerierung kollidiert nicht mit bestehenden Tasks (höchste vorhandene Nummer + 1)
- [ ] Zusammenfassung der erzeugten Tasks wird am Ende ausgegeben
- [ ] Skill-Datei ist unter `tools/analyse_sessions.md` versioniert

# Branches

- feature/T-10-6-session-log-analysis-agent
