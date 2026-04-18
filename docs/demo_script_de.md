# Soofi Trainer — Demo-/Bedienungsskript

Dieses Skript führt einmal durchgängig durch die Bedienung des Soofi Trainers —
von der Auswahl des Anwendungsfalls bis zum Start des Modelltrainings. Zusätzlich
enthält es **Zwischenfragen-Blöcke**, die sich jederzeit im Gespräch einschieben
lassen (Agentenkarten, Trainingsübersicht, Wissensinhalte).

Alle User-Sätze sind so formuliert, dass sie per Sprach- oder Texteingabe direkt
in die Soofi-UI gegeben werden können. Agent-Reaktionen sind als Erwartungen in *kursiv* skizziert.

Der Soofi Trainer ist ein Demonstrator — die vorgeschlagenen Methoden und
Modelle sind nicht immer fachlich optimal. Darauf kommt es in dieser Demo aber
nicht an: Im Vordergrund steht, wie leichtgängig Unternehmen künftig zu
anwendungsspezifischen, souveränen Modellen auf Basis eigener Daten gelangen.

Spielt ruhig mit dem System, experimentiert mit eigenen Dialogen und lasst
euch darauf ein — auch wenn etwas nicht auf Anhieb funktioniert, ist das
überhaupt nicht schlimm. Im Hintergrund werden **Session-Logs** erstellt, die
wir im Anschluss gerne gemeinsam auswerten. Dabei handelt es sich
ausschließlich um **textuelle Protokolle** des Dialogverlaufs — es werden
**keine Sprachaufzeichnungen** gespeichert.

---

## 0. Voraussetzungen

### Backend & Zugang

- Das dockerisierte Backend läuft auf DFKI-Servern in Saarbrücken.
- Der Zugang erfordert ein aktives VPN. Dieses ist auf den iPads bereits
  eingerichtet — bei aktiver Verbindung erscheint rechts oben in der
  Statusleiste ein **VPN-Symbol**.
- Zur Ausfallsicherheit sind drei VMs parallel aufgesetzt, die sich im
  verwendeten Modell unterscheiden:

  | URL                                                       | Modell                    |
  |-----------------------------------------------------------|---------------------------|
  | [https://soofi-1.mrk40.de](https://soofi-1.mrk40.de)      | lokales Qwen3.5 122B      |
  | [https://soofi-2.mrk40.de](https://soofi-2.mrk40.de)      | lokales Qwen3.5 122B      |
  | [https://soofi-3.mrk40.de](https://soofi-3.mrk40.de)      | gpt-4o-mini (Cloud)       |

- Auf den iPads sind entsprechende **App-Icons auf dem Startbildschirm**
  hinterlegt — einfach antippen, kein manuelles Eingeben der URL nötig.

### iPads — Nutzung & Rückgabe

- **Wichtig:** Die iPads sind gemietet und dürfen zu keinem Zeitpunkt
  unbeaufsichtigt liegen bleiben.
- Rückgabe: Der Vermieter sammelt die Geräte am **letzten Messetag (Freitag)
  gegen 15:30 Uhr** wieder ein. Nach Messeende um 15:00 Uhr bleibt also nur
  eine halbe Stunde, um die iPads in den **Auslieferungszustand**
  zurückzusetzen.
- Im Reset-Prozess wird ein **Bestätigungscode** an die hinterlegte
  Kontakt-E-Mail geschickt. Den iPad-Verantwortlichen bitte vorab
  telefonisch verständigen, damit der Code ohne Verzögerung
  weitergeleitet wird.

---

## 0.1 Begriffe zum Einstieg — Dataspace & Verwaltungsschale

**Dataspace (Datenraum).** Ein Dataspace ist ein föderierter, regelbasierter
Raum, in dem Organisationen Daten oder Modelle untereinander anbieten und
beziehen, ohne die Kontrolle darüber aufzugeben. Die Daten bleiben beim
Anbieter; nur Metadaten (Kataloge) werden veröffentlicht, und der Zugriff
wird über Nutzungsverträge (Policies) geregelt. Technische Basis ist in der
Regel der **Eclipse Dataspace Connector (EDC)** — ein Open-Source-Connector
nach IDSA-Standards, der Katalog, Vertragsverhandlung und Datenübertragung
standardisiert. Typische Initiativen: Gaia-X, Catena-X, Manufacturing-X,
Mobility Data Space, 8ra.

**Verwaltungsschale (Asset Administration Shell, AAS).** Die Verwaltungsschale
ist der digitale Zwilling eines Assets (Maschine, Bauteil, Produkt, Software)
im Sinne der **Industrie 4.0 / Plattform Industrie 4.0**. Sie bündelt alle
relevanten Informationen eines Assets — Eigenschaften, Zustand, Dokumente,
Fähigkeiten — in standardisierten **Submodels** (z.B. Digital Nameplate,
Technical Data, Documentation) und stellt sie über eine einheitliche API
(REST, OPC UA, MQTT) bereit. Umgesetzt wird das hier mit **Eclipse BaSyx**.
Damit werden Assets maschinenlesbar, herstellerübergreifend austauschbar und
über Dataspace-Grenzen hinweg verknüpfbar.

## 0.2 Nutzung im Soofi Trainer

Im Soofi Trainer dient der **Dataspace** als souveräne Bezugsquelle für
Trainingsdatensätze. Der Dataset-Agent fragt zuerst den **EDC-Consumer**
(über MCP) an und durchsucht den Katalog des angebundenen **EDC-Providers**
nach passenden Datensätzen — z.B. für
Materialforschung oder Engineering. Erst wenn der Dataspace nichts liefert,
wird auf HuggingFace ausgewichen. So lässt sich demonstrieren, wie ein
Unternehmen interne oder vertraglich geregelte Daten ins LLM-Training
einbringt, ohne sie öffentlich verfügbar zu machen.

Die **Verwaltungsschale** liefert Soofi den fachlichen Kontext der Assets,
um die es im Anwendungsfall geht. Der AAS-Stack (Eclipse BaSyx) hält Submodels
zu typischen KMU-/Engineering-Szenarien bereit
(Maschinen, Bauteile, Datenblätter). Diese Informationen können von Agenten
als strukturiertes Domänenwissen gelesen werden — etwa um Datensätze
passgenau auf ein Asset zuzuschneiden, Trainingsdaten um Metadaten
anzureichern oder später im Engineering-Copilot fundierte Antworten zur
realen Anlage zu geben. Dataspace + Verwaltungsschale zusammen bilden damit
die Brücke zwischen souveränem Datenaustausch und maschinenlesbarem
Asset-Wissen, auf der das Soofi-Training aufsetzt.

---

## 1. Happy Path — vom Anwendungsfall bis zum Trainingsstart

### 1.1 Einstieg

> **User:** Kannst du mir helfen, ein Modell für meinen Anwendungsfall zu spezialisieren?

*→ Soofi fragt nach dem Anwendungsfall.*

### 1.2 Anwendungsfall nennen

> **User:** Ich brauche einen Assistenten zum Thema Compliance.

*→ Soofi bestätigt „Compliance" und fragt, ob nach Datensätzen gesucht werden soll.*

### 1.3 Datensatzsuche — Dataspace zuerst

> **User:** Ja, such mal nach Datensätzen.

*→ Dataset-Agent wird aufgerufen (zuerst Eclipse Dataspace). Wenn nichts
gefunden: Soofi schlägt HuggingFace als Fallback vor.*

### 1.4 Datensatzsuche — HuggingFace

> **User:** Ja, guck mal auf HuggingFace.

*→ Soofi listet 5 Datensätze (z.B. `refusal-compliance-pairs`,
`Akshata/autotrain-data-compliance`, ...).*

### 1.5 Datensatz auswählen

> **User:** Nimm den ersten Datensatz.

*→ Soofi empfiehlt passende Basismodelle (Soofi 8B / 30B MoE / 120B MoE), jeweils
mit kurzer Eignungs-Begründung (digitale Souveränität, Skalierung).*

### 1.6 Basismodell auswählen

> **User:** Nimm das Soofi 120B MoE.

*→ Soofi schlägt Trainingsmethoden vor (z.B. RAG, SFT, DPO, LoRA, QLoRA) und
fragt, welche verwendet werden soll.*

### 1.7 Methode auswählen

> **User:** Dann nehmen wir QLoRA.

*→ Soofi fasst alle 4 Slots zusammen (Anwendungsfall, Datensatz, Basismodell,
Methode) und fragt, ob das Training gestartet werden soll.*

### 1.8 Training starten

> **User:** Ja, starte das Training!

*→ Training-Agent wird aufgerufen, das Seitenpanel öffnet die
**Trainingsübersicht** (`training_view`). Soofi bestätigt: „Der
Trainingsauftrag wurde gestartet."*

---

## 2. Zwischenfragen — jederzeit einschiebbar

Die folgenden Blöcke funktionieren an jedem Punkt im Gespräch. Nach der
Beantwortung nimmt Soofi den Hauptfaden wieder auf (ggf. mit
„Wo waren wir stehen geblieben?").

### 2.A Agentenkarten anzeigen

> **User:** Zeig mir die Agenten-Karten.

*→ Seitenpanel öffnet `agent_cards` — 4 Karten: Interaction-, Advisor-,
Training-, Dataset-Agent.*

> **User:** Schließ die Ansicht wieder.

*→ Seitenpanel wird geschlossen.*

### 2.B Trainingsübersicht öffnen/schließen

> **User:** Öffne die Trainingsübersicht.

*→ Seitenpanel `training_view` zeigt Phasen (Datenvorbereitung, Training,
Evaluation) und Fortschritt.*

> **User:** Schließ die Trainingsübersicht wieder.

### 2.C Standortbestimmung im Dialog

> **User:** Wo waren wir stehen geblieben? Was fehlt denn noch?

*→ Soofi listet die gefüllten Slots (Anwendungsfall / Datensatz / Basismodell /
Methode) und nennt den nächsten fehlenden.*

### 2.D Wissensinhalte — Methodenvergleich

> **User:** Kannst du die Methoden vergleichen? Was ist der Unterschied zwischen RAG, LoRA, QLoRA, SFT und DPO?

*→ Advisor-Agent antwortet per RAG auf Basis von `rag_vs_fine_tuning.md`,
`lora.md`, `qlora.md`, `dpo.md`. Quellen werden am Chatbeitrag angezeigt.*

### 2.E Wissensinhalte — Basismodelle

> **User:** Welche offenen Modelle kennst du? Kannst du sie miteinander vergleichen?

*→ Advisor erklärt Soofi/8ra, OLMo, Mistral, Qwen, DeepSeek anhand
`base_models.md` und `rag_vs_fine_tuning.md` (Souveränität, Transparenz,
Lizenz).*

### 2.F Wissensinhalte — 8ra-Initiative

> **User:** Was kannst du mir über die 8ra-Initiative sagen?

*→ Advisor antwortet aus `8ra_initiative.md` und `soofi-project.md`
(EU-Mitgliedstaaten, IPCEI-CIS, BMWE-Koordination).*

### 2.G Wissensinhalte — RAG vs. Fine-Tuning

> **User:** Wann nutzt man RAG, wann Fine-Tuning?

*→ Advisor erklärt anhand `rag_vs_fine_tuning.md` — RAG für dynamisches Wissen,
Fine-Tuning für Sprachstil/Format.*

### 2.H Wissensinhalte — Use-Case-Beispiele

> **User:** Welche Anwendungsfälle sind für Soofi typisch?

*→ Advisor listet Beispiele aus `01_compliance_copilot.md`,
`02_wissensmanagement.md`, `03_engineering_copilot.md`,
`07_digital_product_passport.md`, `08_vergabe_assistent.md`,
`09_verwaltungsassistent.md`.*

---

## 3. Variationen für weitere Demo-Durchläufe

| Anwendungsfall       | Datensatzquelle   | Basismodell       | Methode |
|----------------------|-------------------|-------------------|---------|
| Compliance           | HuggingFace       | Soofi 120B MoE    | QLoRA   |
| Materialforschung    | Eclipse Dataspace | Soofi 30B MoE     | LoRA    |
| Wissensmanagement    | HuggingFace       | Soofi 8B Dense    | RAG     |
| Engineering-Copilot  | Eclipse Dataspace | Soofi 30B MoE     | SFT     |

**Tipp für Eclipse Dataspace:** zuerst „such mal nach Datensätzen" sagen, bei
Fehlanzeige gezielt nach `Materialforschung` im Dataspace fragen — der
Dataset-Agent liefert dann den Katalog-Eintrag mit `counterPartyAddress`.

---

## 4. Zurücksetzen / neue Session

- **Zurücksetzen-Button** in der Soofi-UI drücken → startet eine frische
  Session.
- Alternativ: Browser-Tab schließen oder Seite neu laden → neue Session-ID.

---

## 5. Ausfallszenarien (gut für Demo-Robustheit)

- **Kein Dataspace-Treffer** → „Such mal auf HuggingFace" als Fallback.
- **Kein HuggingFace-Treffer** → alternative Begriffe vorschlagen lassen.
- **Advisor antwortet zu knapp** → „Kannst du das noch ausführlicher
  erläutern?"
