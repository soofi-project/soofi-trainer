# Task

- user story: [US-10](US-10-demo-preparation.md)

/label ~UserStory_US-10
/label ~Task
/label ~ToDo

# Description

**Demo Use Cases — Szenarien für die Hannover Messe**

Definition, Vorbereitung und End-to-End-Test von mindestens zwei konkreten Demo-Szenarien,
die den vollständigen Soofi-Pipeline-Durchlauf zeigen: Use-Case-Analyse →
Methodenempfehlung (RAG vs. Fine-Tuning) → Trainingsauftrag.

## Anforderungen an ein Demo-Szenario

Ein gutes Demo-Szenario ist:
- **Domänen-nah**: verständlich für ein Industrie-/Messe-Publikum ohne KI-Vorwissen
- **Schnell**: vollständiger Durchlauf in unter 5 Minuten
- **Visuell**: zeigt möglichst viele UI-Features (Voice, Doc Viewer, Training View)
- **Stabil**: funktioniert auch ohne Internetverbindung (lokales Modell / gecachte Antworten)

## Vorgeschlagene Szenarien

### Szenario A — Produktionsdaten-Assistent (Fertigungsindustrie)

Ein Anlagenbetreiber möchte einen LLM-Assistenten für technische Dokumentation und
Fehlerdiagnose spezialisieren. Soofi analysiert den Use Case, empfiehlt RAG für die
Wissensbasis und leitet ggf. einen Fine-Tuning-Job für domänenspezifische Terminologie ein.

**Gesprächsleitfaden:**
1. Nutzer beschreibt Use Case per Sprache: „Ich möchte einen Assistenten, der Fragen zu
   unseren Maschinenhandbüchern beantwortet."
2. Advisor empfiehlt RAG, erklärt Unterschied zu Fine-Tuning
3. Demo-Dokumente (z.B. Maschinenhandbuch-Auszüge) werden in Wissenbasis referenziert
4. Training View zeigt simulierten oder echten Trainingsfortschritt

### Szenario B — Qualitätssicherungs-Klassifikator (Produktion)

Ein QS-Team möchte ein Modell trainieren, das Fehlerkategorien aus Produktionsberichten
klassifiziert. Soofi empfiehlt Fine-Tuning, zeigt das Dataset und startet einen LoRA-Job.

**Gesprächsleitfaden:**
1. Nutzer: „Wir haben 2000 gelabelte Fehlermeldungen und wollen automatisch klassifizieren."
2. Advisor empfiehlt Fine-Tuning (strukturierter Task mit gelabelten Daten)
3. Training Agent bereitet Job vor, Training Gateway startet Container
4. Trainingsfortschritt in der UI sichtbar

## Vorzubereitende Artefakte

| Artefakt | Beschreibung |
|----------|-------------|
| Wissensdokumente | 3–5 PDF/Markdown-Dokumente für Szenario A in MinIO laden |
| Demo-Dataset | Kleine CSV/JSONL-Datei für Szenario B (Fine-Tuning) |
| Gesprächsskripte | Ausformulierte Fragen für den Moderator (DE) |
| Fallback-Notizen | Was tun wenn Netz/Modell nicht verfügbar? |

## Acceptance Criteria

- [ ] Mindestens zwei Szenarien vollständig definiert und dokumentiert
- [ ] Demo-Dokumente für Szenario A in MinIO geladen und durch Knowledge Ingestion indexiert
- [ ] Demo-Dataset für Szenario B vorbereitet und durch Training Gateway nutzbar
- [ ] Gesprächsskripte (DE) für beide Szenarien geschrieben
- [ ] Beide Szenarien End-to-End getestet (inkl. Voice-Eingabe auf iPad)
- [ ] Gesamtlaufzeit beider Szenarien unter 5 Minuten
- [ ] Offline-Fallback definiert und dokumentiert

# Branches

- feature/T-10-2-demo-use-cases
