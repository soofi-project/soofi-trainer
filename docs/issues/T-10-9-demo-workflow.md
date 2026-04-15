# Task

- user story: [US-10](US-10-demo-preparation.md)

/label ~UserStory_US-10
/label ~Task
/label ~ToDo

# Description

**Demo-Workflow: Souveräne Modelle → Anwendungsfall → Datensatz → Training**

Der Advisor-Agent soll auch Fragen zu folgenden Themen beantworten können, die für
Demo-Gespräche auf der Hannover Messe typisch sind:

- **Souveräne KI / souveräne Modelle**: Warum ist Datensouveränität bei LLMs wichtig?
  Welche regulatorischen oder sicherheitsbezogenen Anforderungen sprechen für lokale Modelle?
- **Offene / Open-Weight-Modelle**: Welche offenen Modelle gibt es (Llama, Mistral, Falcon,
  Gemma u.a.)? Was sind ihre Stärken und Einsatzgrenzen im Vergleich zu proprietären APIs?
- **Relevante Anwendungsfälle**: Welche Unternehmens- und Behörden-Anwendungsfälle eignen
  sich für LLM-Spezialisierung? Wann ist welche Methode sinnvoll?

## Referenz-Demo-Szenario

Der folgende Gesprächsverlauf definiert den Ziel-Flow, gegen den alle Änderungen getestet
werden sollen. Jeder Schritt muss ohne manuelle Eingriffe oder Fehlermeldungen durchlaufen.

```
[User]  "Warum sind souveräne Modelle für die europäische Industrie wichtig?"
[Soofi] Erläutert Risiken proprietärer Cloud-LLMs (Datensouveränität, DSGVO, AI Act,
        Abhängigkeit), Chancen offener Modelle und positioniert Soofi als Lösung.
        → ask_advisor_tool

[User]  "Für welche industriellen Anwendungsfälle wäre das relevant?"
[Soofi] Nennt konkrete Anwendungsfälle (Compliance, Qualitätssicherung, Predictive
        Maintenance, Wissensmanagement …) und fragt, für welchen ein Modell trainiert
        werden soll.
        → ask_advisor_tool

[User]  "Ja, für Compliance" / "Gerne für den dritten"
[Soofi] Sucht passende Datensätze (HuggingFace / EDC) und listet Treffer auf; fragt,
        welchen Datensatz der User verwenden möchte.
        → ask_dataset_agent_tool

[User]  "Nehm den ersten" / "Nehme alle"
[Soofi] Schlägt geeignetes Basismodell und Methode (RAG / LoRA / QLoRA) vor und fragt,
        ob das Training gestartet werden soll.
        → ask_advisor_tool

[User]  "Ja" / "Starte Training"
[Soofi] Startet Trainingsauftrag und öffnet automatisch die Trainingsübersicht.
        → ask_training_agent_tool + control_training_view(open)

[Soofi] "Upload des trainierten Modells abgeschlossen. Das Modell kann nun verwendet werden."
        → Training Agent schließt Job ab, Fortschrittsanzeige zeigt 100 %
```

**Kritische Übergänge:**
- Schritt 2→3: Der User antwortet mit Ordinalreferenz ("Gerne für den dritten") oder Kurzname
  ("Ja, für Compliance"). Der Interaction Agent muss diese Referenz gegen die Liste aus Schritt 2
  auflösen und den korrekten Use Case an den Dataset Agent übergeben — ohne Rückfrage.
- Schritt 3→4: Dataset-Agent-Ergebnis muss kontextfest für Schritt 4 (Modell/Methoden-Empfehlung)
  erhalten bleiben — der Interaction Agent darf den Datensatz nicht aus dem Kontext verlieren.
  Auch hier kann der User wieder mit Ordinalreferenz antworten ("Nehm den ersten" / "Nehme alle").
- Schritt 4→5: Die im Gespräch genannten Parameter (Datensatz, Methode, Domäne) müssen beim
  `ask_training_agent_tool`-Aufruf vollständig übergeben werden — kein erneutes Nachfragen.

## Änderungen

### 1. Wissensdatenbank (`knowledge/`)

`knowledge/models/base_models.md` enthält bereits umfangreiche Inhalte zu offenen Modellen
(Llama, Mistral, OLMo, Gemma, Qwen …) **und** zur Souveränitätsanalyse (strategische Risiken,
DSGVO, EU AI Act, Soofi-Positionierung, Compliance-Konflikte, Auditierbarkeit). Das Problem:
beide Themen stecken in einer einzigen ~450-Zeilen-Datei, was die RAG-Präzision verschlechtert
(eine Souveränitätsfrage zieht den gesamten Modellkatalog rein).

**Neuverteilung** (keine neuen Themen — nur bessere Trennung):

- `knowledge/models/base_models.md` — **kürzen**: nur Modellkatalog behalten
  (Deployment-Kategorien, Offenheitsgrade, je Anbieter-Abschnitt mit Tabelle,
  Anwendungsfall-Übersicht am Ende). Derzeit ~Zeilen 1–24 + alle Anbieter-Tabellen.
- `knowledge/models/sovereignty.md` — **neu anlegen**: Inhalt aus `base_models.md`
  auslagern (derzeit ~Zeilen 25–138 + Souveränitäts-Übersichtstabelle):
  - Strategische Risiken (Lizenz-Instabilität, Geopolitik, Compliance-Konflikt EU/US)
  - Souveränitätskriterien und Auditierbarkeit
  - Soofi/8ra-Positionierung als einziger vollständig qualifizierter EU-Zulieferer
  - Europäische Souveränitäts-Empfehlung (Priorisierungsliste)
- `knowledge/usecases/usecases.md` — **befüllen** (aktuell leer, nur Überschrift —
  kritischste Lücke für Schritt 2 des Demo-Flows):
  Anwendungsfälle nach Branche/Domäne (Fertigung, Qualitätssicherung, **Compliance**,
  Predictive Maintenance, Wissensmanagement, Behörden, Gesundheit), je mit kurzem
  Steckbrief und Methodenempfehlung (RAG / Fine-Tuning / Kombination).
  Compliance muss explizit als benannter Use Case enthalten sein.

### 2. Advisor-Prompt (`advisor/src/prompts.py`)

Scope-Beschreibung erweitern:
- Souveräne KI / lokale Modelle als explizites Thema ergänzen
- Offene Modelle als Thema ergänzen
- Anwendungsfälle als Thema ergänzen

### 3. Interaction-Agent-Prompt (`interaction-agent/src/prompts.py`)

#### 3a. Keyword-Liste (Schritt 3) erweitern

Derzeit fehlen in der Keyword-Liste von Schritt 3 die für den Demo-Flow relevanten Begriffe.
Ergänzen:
- `souveräne Modelle`, `Datensouveränität`, `offene Modelle`, `Open-Weight`, `Open-Source-Modelle`
- `Anwendungsfall`, `Use Case`, `Llama`, `Mistral`, `Falcon`, `Gemma`

#### 3b. Kontextabhängige Kurzantworten regeln

Das aktuelle Routing versagt bei den für den Demo-Flow typischen Kurzantworten, weil der
Fallback (Schritt 8: "Im Zweifel → ask_advisor_tool") greift, obwohl ein anderes Tool
gemeint ist:

| Demo-Schritt | User-Eingabe | Aktuelles Verhalten | Soll-Verhalten |
|---|---|---|---|
| 2→3 | "Ja, für Compliance" / "Gerne für den dritten" | → ask_advisor_tool (Fallback) | → ask_dataset_agent_tool |
| 3→4 | "Nehm den ersten" / "Nehme alle" | → ask_advisor_tool (Fallback) | → ask_advisor_tool (zufällig richtig, aber Datensatz-Kontext wird nicht explizit übergeben) |
| 4→5 | "Ja" | → ask_advisor_tool (Fallback) | → ask_training_agent_tool |

Neue Regel ergänzen: Wenn die letzte Soofi-Antwort eine nummerierte Liste war und der User
mit einer Ordinalreferenz ("den dritten", "den ersten", "alle") oder einem Kurznamen aus
der Liste antwortet, muss der Agent:
1. Die Referenz gegen die letzte Antwort auflösen
2. Den aufgelösten Wert als Parameter an das kontextuell richtige Tool übergeben
3. Nicht erneut beim User nachfragen

Außerdem: Ein bloßes "Ja" als Bestätigung nach einer Empfehlung (Modell/Methode) muss
als Trainingsauftrag interpretiert werden → ask_training_agent_tool, nicht ask_advisor_tool.

## Acceptance Criteria

### Wissensdatenbank
- [ ] `knowledge/models/sovereignty.md` angelegt mit ausgelagertem Inhalt aus `base_models.md`
- [ ] `knowledge/models/base_models.md` auf reinen Modellkatalog reduziert
- [ ] `knowledge/usecases/usecases.md` befüllt (mind. 5 Anwendungsfälle inkl. Compliance)
- [ ] Knowledge-Ingestion erfolgreich — alle geänderten Dokumente in Weaviate vorhanden

### Prompt-Anpassungen
- [ ] Advisor-Prompt erweitert (DE + EN): Scope umfasst souveräne Modelle, offene Modelle, Anwendungsfälle
- [ ] Interaction-Agent-Prompt erweitert (DE + EN): Keyword-Liste deckt neue Begriffe ab

### Demo-Flow (Referenz-Szenario vollständig durchlaufbar)
- [ ] Schritt 1: Frage zu souveränen Modellen → Advisor antwortet mit Kontext und Soofi-Positionierung
- [ ] Schritt 2: Frage nach Anwendungsfällen → Advisor listet mind. 3 Fälle auf, fragt nach Auswahl
- [ ] Übergang 2→3: Kurzantwort ("Ja, für Compliance" / "den dritten") wird korrekt aufgelöst und an Dataset Agent übergeben
- [ ] Schritt 3: Domänenangabe → Dataset-Agent liefert passende Datensätze, fragt nach Auswahl
- [ ] Übergang 3→4: Kurzantwort ("den ersten" / "alle") wird aufgelöst, Kontext bleibt erhalten
- [ ] Schritt 4: Datensatzauswahl → Advisor empfiehlt Basismodell und Methode, fragt nach Bestätigung
- [ ] Übergang 4→5: Alle Parameter (Use Case, Datensatz, Methode, Modell) werden ohne Rückfrage übergeben
- [ ] Schritt 5: Trainingsbestätigung → Training startet, Übersicht öffnet automatisch
- [ ] Schritt 6: Job-Abschluss → Erfolgsmeldung erscheint in der UI

### Regression
- [ ] Bestehende RAG/Fine-Tuning/Soofi-Fragen funktionieren weiterhin korrekt

# Branches

- feature/T-10-9-demo-workflow
