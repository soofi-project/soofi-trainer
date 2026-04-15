# Task

- user story: [US-10](US-10-demo-preparation.md)

/label ~UserStory_US-10
/label ~Task
/label ~ToDo

# Description

**Onboarding Guide — Demonstrator-Leitfaden für Demo-Präsentierende**

Ein kompakter, druckbarer Guide für Kolleginnen und Kollegen, die den Soofi-Demonstrator
auf der Hannover Messe oder anderen Events vorstellen. Der Leitfaden vermittelt die zentralen
Key Messages, erklärt das System auf einem Niveau für technisch interessiertes Publikum ohne
KI-Vorwissen und enthält eine vollständig ausformulierte Beispielinteraktion zum Einüben.

## Inhalt des Guides

### 1. Key Messages (max. 5, je ein Satz)

Die zentralen Aussagen, die ein Messebesucher nach der Demo mitnehmen soll:

1. **Kein KI-Expertenwissen nötig** — Soofi analysiert den Use Case im Gespräch und
   empfiehlt automatisch die passende Methode (RAG oder Fine-Tuning).
2. **Vom Gespräch zum Trainingsauftrag in Minuten** — der gesamte Prozess von der
   Problemschilderung bis zum laufenden LoRA-Job läuft durch eine einzige
   Konversationsschnittstelle.
3. **Industriell relevante Domänen** — Fertigungsdokumentation, Qualitätssicherung,
   Predictive Maintenance: Soofi ist auf produzierendes Gewerbe ausgerichtet.
4. **Open-Source-Basis, lokal betreibbar** — keine Cloud-Abhängigkeit, volle Datenkontrolle
   für sensible Produktionsdaten.
5. **Standards-konform** — Trainingsartefakte werden als AAS-Teilmodelle exportiert und
   lassen sich in Digital-Twin-Infrastrukturen (Eclipse EDC) einbinden.

### 2. Hintergrundwissen für Präsentierende

#### Was ist die Verwaltungsschale (Asset Administration Shell, AAS)?

Die Verwaltungsschale ist ein vom Bundesministerium und Industriekonsortien (ZVEI, Plattform
Industrie 4.0) standardisiertes digitales Informationsmodell für physische und digitale
Assets. Man kann sie sich als standardisierten „digitalen Ausweis" einer Maschine, eines
Bauteils oder — im Fall von Soofi — eines trainierten KI-Modells vorstellen. Jede
Verwaltungsschale besteht aus Teilmodellen (z.B. „Namensplatte", „Technische Daten",
„KI-Datensatz"), die maschinenlesbar und plattformunabhängig ausgetauscht werden können.
Soofi exportiert Trainingsartefakte als AAS-Teilmodelle, damit sie in bestehende
Digital-Twin-Infrastrukturen integriert werden können — ohne proprietäre Schnittstellen.

#### Was ist ein Datenraum (Eclipse Dataspace Connector, EDC)?

Ein Datenraum ist eine Infrastruktur, die es Unternehmen ermöglicht, Daten souverän
untereinander auszutauschen — also: der Dateneigentümer behält die Kontrolle darüber,
wer seine Daten unter welchen Bedingungen nutzen darf. Der Eclipse Dataspace Connector
(EDC) ist die Open-Source-Referenzimplementierung dafür (u.a. von Microsoft, SAP und DFKI
mitentwickelt), die im Rahmen von Catena-X und Gaia-X eingesetzt wird. Im Kontext von Soofi
bedeutet das: Trainingsartefakte (Modelle, Datensätze) können über einen EDC-Datenraum mit
anderen Unternehmen oder Systemen geteilt werden — kontrolliert, nachvollziehbar und ohne
zentrale Daten-Plattform als Mittelsmann. Für die Demo genügt es, den Satz zu sagen:
*„Über einen Datenraum kann das trainierte Modell sicher mit Partnern geteilt werden,
ohne dass wir die Kontrolle über unsere Daten aufgeben."*

### 3. System-Überblick für Präsentierende (2 Minuten Pitch)

Kurze Erklärung der Architektur in laienverständlicher Sprache:

- **Soofi UI** — die Sprach- und Chat-Oberfläche, mit der der Anwender interagiert
- **Interaction Agent** — das KI-Gehirn, das die Konversation steuert und Aufgaben
  an Spezialagenten delegiert
- **Advisor** — beantwortet Fachfragen aus der Wissensdatenbank (RAG)
- **Training Agent + Gateway** — plant und startet Trainingsaufträge im Hintergrund
- **AAS-Export** — Trainingsergebnisse als digitale Zwillinge exportierbar

### 4. Durchgängige Beispielinteraktion

**Szenario: Wartungsassistent für CNC-Maschinen (Dauer: ca. 4 Minuten)**

Dieses Szenario eignet sich für ein Fertigungspublikum und zeigt den vollständigen
Pipeline-Durchlauf.

---

#### Schritt 1 — Use-Case-Schilderung (0:00–0:45)

**Moderator sagt:**
> „Ich zeige jetzt, wie Soofi einen typischen Industrie-Use-Case verarbeitet. Ich spiele
> die Rolle eines Produktionsleiters."

**Eingabe (Sprache oder Text):**
> *„Hallo Soofi, wir betreiben 40 CNC-Fräsmaschinen in unserer Fertigung. Unsere Techniker
> suchen ständig in dicken Handbüchern nach Wartungsintervallen und Fehlercodes. Ich möchte
> einen KI-Assistenten, der diese Fragen direkt beantworten kann."*

**Erwartete Reaktion von Soofi:**
Soofi bestätigt das Anliegen, stellt eine Rückfrage zur Datenlage
(„Haben Sie die Handbücher als PDF vorliegen?") und kündigt an, eine Methodenempfehlung
zu erarbeiten.

---

#### Schritt 2 — Methodenempfehlung durch den Advisor (0:45–1:45)

**Folge-Eingabe:**
> *„Ja, wir haben die Handbücher als PDF. Etwa 500 Seiten pro Maschinentyp, insgesamt
> vier Typen."*

**Erwartete Reaktion:**
Der Advisor-Agent wird sichtbar aktiviert (Suche-Spinner in der UI). Soofi empfiehlt **RAG**:
- Dokumente in eine Wissensdatenbank laden
- LLM greift bei jeder Frage auf die relevanten Abschnitte zu
- Kein Training nötig, sofort einsatzbereit

**Moderator-Hinweis für Publikum:**
> „Sie sehen hier im Doc Viewer rechts, welche Quellen der Advisor für diese Empfehlung
> genutzt hat — vollständige Transparenz."

---

#### Schritt 3 — Ergänzung: Fine-Tuning-Bedarf (1:45–2:45)

**Folge-Eingabe:**
> *„Interessant. Wir haben aber auch ein internes Vokabular — Maschinennamen und Fehlercodes,
> die das Standard-Modell nicht kennt. Brauchen wir dafür Fine-Tuning?"*

**Erwartete Reaktion:**
Soofi erklärt den Unterschied zwischen RAG und Fine-Tuning in einem Satz,
empfiehlt eine **Kombination**: RAG für die Handbücher, Fine-Tuning für das
Domänenvokabular. Der Training Agent kündigt einen LoRA-Job an.

---

#### Schritt 4 — Trainingsauftrag (2:45–3:30)

Soofi leitet den Trainingsauftrag ein. In der UI erscheint die **Training View**
mit Fortschrittsbalken und Epochen-Metriken.

**Moderator-Hinweis für Publikum:**
> „Der Trainingsauftrag läuft im Hintergrund auf unserem GPU-Server. Im Produktivbetrieb
> würde das einige Stunden dauern — hier im Demo-Modus sehen Sie den simulierten
> Fortschritt."

---

#### Schritt 5 — Abschluss & AAS-Export (3:30–4:00)

**Folge-Eingabe:**
> *„Können wir das trainierte Modell in unsere Digital-Twin-Plattform einbinden?"*

**Erwartete Reaktion:**
Soofi erklärt den AAS-Export: Das Trainingsergebnis wird als standardisiertes
AAS-Teilmodell exportiert und kann über Eclipse EDC mit anderen Systemen geteilt werden.

---

### 5. Häufige Fragen aus dem Publikum (FAQ)

| Frage | Kurze Antwort |
|-------|--------------|
| „Welches LLM steckt dahinter?" | Konfigurierbar — lokal (Llama/Mistral via Ollama/vLLM) oder OpenAI-kompatible API |
| „Läuft das ohne Internet?" | Ja, der gesamte Stack ist lokal betreibbar |
| „Was kostet das?" | Open-Source-Basis; Betriebskosten abhängig von GPU-Hardware |
| „Wie lange dauert Fine-Tuning?" | Abhängig von Datenmenge und Hardware; typisch 2–8 Stunden auf H100 |
| „Kann Soofi mehrere Sprachen?" | Aktuell DE/EN; Erweiterbar |
| „Wo werden die Daten gespeichert?" | Lokal im Docker-Stack (MinIO für Dokumente, Weaviate für Vektoren) |

### 6. Setup-Checkliste vor der Demo

- [ ] `./up.sh` ausgeführt, alle Container grün (`docker ps`)
- [ ] Knowledge Ingestion abgeschlossen (Logs prüfen: `docker logs -f knowledge-ingestion`)
- [ ] Soofi UI im Browser geöffnet (iPad: Vollbild-PWA)
- [ ] Mikrofon-Berechtigung im Browser erteilt
- [ ] Demo-Dokumente in MinIO geladen (Szenario A)
- [ ] Internetverbindung nicht zwingend nötig — lokales Modell als Fallback konfiguriert
- [ ] Fallback-Plan bekannt: Bei Verbindungsproblemen → Text-Eingabe statt Sprache

### 7. Tipps für eine gute Präsentation

- **Langsam sprechen** bei Spracheingabe — Whisper braucht klare Aussprache
- **Pausen einbauen** nach jeder Soofi-Antwort, damit das Publikum lesen kann
- **Doc Viewer kommentieren** — die Quell-Transparenz ist ein Verkaufsargument
- **Nicht zu technisch werden** — Schlagworte wie „LangGraph" oder „Weaviate"
  weglassen, stattdessen „KI-Wissensdatenbank" und „intelligenter Weiterleiter"
- **Fragen ans Ende** — lieber den Durchlauf vollständig zeigen, dann diskutieren

## Vorzubereitende Artefakte

| Artefakt | Format | Zweck |
|----------|--------|-------|
| Onboarding Guide | PDF (A4, 2–3 Seiten) | Ausdruckbar für Präsentierende |
| Kurzfassung Key Messages | 1 Seite / Slide | Briefing vor der Demo |
| FAQ-Karte | Laminierte A5-Karte | Schnellreferenz am Stand |

## Acceptance Criteria

- [ ] Onboarding Guide als Markdown unter `docs/demo/onboarding-guide.md` abgelegt
- [ ] Mindestens 5 Key Messages definiert und vom Team abgenommen
- [ ] Vollständige Beispielinteraktion für Szenario A (CNC-Wartung) ausformuliert
- [ ] FAQ mit mindestens 6 typischen Publikumsfragen
- [ ] Setup-Checkliste vollständig und gegen realen Stack verifiziert
- [ ] Guide von mindestens einer Person ohne Vorwissen Probe-gelesen und für verständlich befunden
- [ ] PDF-Version erzeugt und an Demo-Team verteilt

# Branches

- feature/T-10-8-onboarding-guide
