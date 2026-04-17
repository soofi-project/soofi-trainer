# Soofi Trainer — Demo-/Bedienungsskript

Dieses Skript führt einmal durchgängig durch die Bedienung des Soofi Trainers —
von der Auswahl des Anwendungsfalls bis zum Start des Modelltrainings. Zusätzlich
enthält es **Zwischenfragen-Blöcke**, die sich jederzeit im Gespräch einschieben
lassen (Agentenkarten, Trainingsübersicht, Wissensinhalte).

Alle User-Sätze sind so formuliert, dass sie per Sprach- oder Texteingabe direkt
in die Soofi-UI (`https://localhost/` oder `http://localhost:3001`) gegeben
werden können. Agent-Reaktionen sind als Erwartungen in *kursiv* skizziert.

---

## 0. Voraussetzungen

- Stack läuft: `./up.sh` (Default-Backend `chatgpt`, Profil `local`).
- UI erreichbar unter `https://localhost/` (Caddy, self-signed) bzw. `:3001`.
- Mikrofon freigegeben, Lautsprecher aktiv (TTS).

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

- Browser-Tab schließen oder Seite neu laden → neue Session-ID.
- Sessionlogs landen unter `session-logs/YYYY-MM-DD_HH-MM-SS_<id>.md` (falls
  `SESSION_LOG_ENABLED=true`).

---

## 5. Ausfallszenarien (gut für Demo-Robustheit)

- **Kein Dataspace-Treffer** → „Such mal auf HuggingFace" als Fallback.
- **Kein HuggingFace-Treffer** → alternative Begriffe vorschlagen lassen.
- **Advisor antwortet zu knapp** → „Kannst du das noch ausführlicher
  erläutern?" — der Advisor hängt an bestehenden `advisor_context_id` an.
- **Agent-Karte fehlt** → `./down.sh && ./up.sh --build` prüft die
  A2A-Registrierung neu.
