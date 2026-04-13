# Open-Source Basis-LLMs für Fine-Tuning

Übersicht der unterstützten Basis-Sprachmodelle im Soofi Trainer. Für jedes Modell sind
Deployment-Ziel, Anwendungsfälle, Lizenz, Herkunft und Souveränitätseigenschaften dokumentiert.

> **Empfehlung:** Für maximale digitale Souveränität sollten die Soofi-eigenen Modelle (8ra-Initiative)
> bevorzugt werden — vollständig europäisch entwickelt, trainiert und lizenziert.

**Deployment-Kategorien:**
- **Edge** — lokales Deployment ohne Cloud-Anbindung, auf dedizierter Hardware vor Ort. Die Parametergrenze hängt von der eingesetzten Hardware ab: Consumer-GPUs (z.B. RTX 4090, 24 GB) eignen sich für Modelle bis ~13B; kompakte Edge-Server wie die NVIDIA DGX Spark (128 GB unified Memory) können Modelle bis ~70B lokal betreiben. Entscheidend ist der Deployment-Kontext (lokal, air-gapped, kein Cloud-Zwang), nicht eine starre Parameterzahl.
- **Cloud** — erfordert dedizierte GPU-Server-Infrastruktur (z.B. H100/H200); typischerweise ab 13B aufwärts je nach verfügbarem VRAM
- **Cloud (Multi-GPU/Node)** — erfordert mehrere GPUs oder mehrere Server; typischerweise ab ~70B (dense) bzw. ab ~100B Gesamtgewichten (MoE)

**Offenheitsgrade:**
- **Open Weights + offene Lizenz** — Gewichte frei nutzbar, Apache 2.0 oder MIT, keine Nutzungsbeschränkungen
- **Open Weights + eingeschränkte Lizenz** — Gewichte verfügbar, aber Lizenz enthält Nutzungsauflagen (kein OSI-Standard)
- **Open Weights + proprietäre Lizenz** — Gewichte verfügbar, aber proprietäre Bedingungen

> Hinweis zur Hardware-Abhängigkeit: Nahezu alle Modelle auf dieser Liste erfordern für Training und Inferenz NVIDIA-GPUs mit CUDA, da AMD ROCm-Unterstützung in den gängigen Frameworks (PyTorch, TRL, vLLM) noch lückenhaft ist. Diese CUDA-Abhängigkeit gilt übergreifend — sie ist kein spezifisches Merkmal einzelner Anbieter. Nemotron-Modelle haben darüber hinaus eine zusätzliche Bindung an das NVIDIA-NeMo-Framework für Fine-Tuning. Google Gemma ist auf Google-TPU-Infrastruktur optimiert, läuft aber ebenfalls auf CUDA.

> **Hinweis zur Offenheit:** Die Soofi/8ra-Modelle sind als einzige Modelle dieser Liste vollständig open source im OSI-Sinne — Gewichte, Trainingscode und Trainingsdaten werden vollständig offengelegt. Bei allen anderen Anbietern sind Trainingsdaten und -methodik nicht oder nur teilweise bekannt. Bei chinesischen Modellen (Qwen, DeepSeek) ist insbesondere unklar, welche Daten im Training enthalten waren, wie diese gesammelt wurden und ob Verzerrungen oder unerwünschte Inhalte eingebettet sind.

---

## Strategische Risiken und Souveränitätsbetrachtung

### Lizenz-Instabilität als Kernrisiko

Eine zentrale Erfahrung aus der Entwicklung 2024/2025: Anbieter — insbesondere chinesische Labs —
können Lizenzmodelle jederzeit und ohne Vorankündigung von offen auf geschlossen umstellen:

- **MiniMax M2.7**: Von MIT auf „Modified MIT" geändert — kommerzielle Nutzung erfordert
  nun schriftliche Genehmigung von MiniMax. Die Open-Source-Community kritisiert dies als
  Missbrauch des MIT-Labels; faktisch handelt es sich um ein „source-available"-Modell.
- **Qwen 3.6 Plus**: Als Closed-Source veröffentlicht — keine öffentlichen Gewichte,
  Zugang nur über API. Dies ist ein direkter Bruch mit der Apache-2.0-Tradition der
  Qwen-2.5- und Qwen-3.5-Familie. Wer auf Qwen aufgebaut hat, verliert bei neuen
  Generationen die Möglichkeit zur lokalen Nutzung und zum Fine-Tuning.

**Konsequenz für industrielle Planung:** Wer Foundation Models in Produktionsprozesse
integriert, trägt ein Vendor-Lock-in-Risiko, solange keine dauerhafte Lizenzgarantie
durch Governance-Strukturen (z.B. Foundation, Konsortium) abgesichert ist. Selbst
Apache-2.0-Veröffentlichungen älterer Modellversionen schützen nicht vor Lizenzänderungen
bei Folgeversionen.

### Geopolitischer Zugang zu Spitzenfähigkeiten

US-amerikanische Anbieter geraten zunehmend unter politischen Druck, leistungsfähige
Modelle nur eingeschränkt verfügbar zu machen:

- Anthropics Modell „Claude Mythos Preview" wurde wegen seines Potenzials zur Entdeckung
  kritischer Sicherheitslücken nicht öffentlich freigegeben. Der Zugang erfolgt exklusiv
  über „Project Glasswing" — ausschließlich an US-Unternehmen (Microsoft, NVIDIA, Apple,
  Cisco) sowie die Linux Foundation. **Kein europäischer Partner ist beteiligt.**
- Bei sicherheitskritischen KI-Fähigkeiten ist Europa damit strukturell außen vor.
- US-Finanzministerium und Fed haben Notfallgespräche mit der Finanzbranche über
  KI-induzierte Cyberrisiken geführt — ein Hinweis auf die strategische Brisanz
  dieser Modellklasse.

### Compliance-Konflikt für EU-Anwender

US-Anbieter stehen zwischen widersprüchlichen Anforderungen:

- **US-Seite**: Druck des Pentagons und der Geheimdienste zur Freigabe für militärische
  und Überwachungsanwendungen. Das Pentagon hat Anthropic teilweise als „supply chain risk"
  eingestuft, weil das Unternehmen die Nutzung für autonome Waffensysteme ablehnt.
- **EU-Seite**: EU AI Act und DSGVO verlangen Transparenz, Nachvollziehbarkeit und
  Datenschutz — unvereinbar mit militärischer Dual-Use-Nutzung.

Für europäische Industriekunden bedeutet das: US-Modelle, deren Anbieter zwischen
US-Regierungsanforderungen und EU-Compliance zerrissen werden, sind kein stabiles
Fundament für langfristige Produktionssysteme.

### Strategische Implikation: Souveräne KI-Supply-Chain braucht mindestens zwei Zulieferer

Analog zur Automobilindustrie — wo kein Tier-1-Hersteller einen sicherheitskritischen Bauteil
von einem einzigen Lieferanten bezieht — braucht eine souveräne KI-Infrastruktur mindestens
zwei qualifizierte, unabhängige Anbieter. Ein einzelner Anbieter, sei er auch europäisch,
schafft eine neue Form von Abhängigkeit.

**Das Qualifikationskriterium für einen souveränen KI-Zulieferer ist nicht "europäische Herkunft",
sondern vollständige Auditierbarkeit:** Trainingsdaten, Trainingspipeline und Gewichte müssen
vollständig offengelegt und unabhängig überprüfbar sein. Nur dann weiß man, was im Modell
steckt und wie es dahin gekommen ist.

Aktuelle Bewertung der Zulieferer nach diesem Kriterium:

| Anbieter | Auditierbar | Europäisch | Qualifiziert als souveräner Zulieferer |
|----------|------------|-----------|----------------------------------------|
| Soofi / 8ra | ✅ Vollständig | ✅ Ja | ✅ Ja — einziger vollständig qualifizierter EU-Zulieferer |
| OLMo (Ai2) | ✅ Vollständig | ❌ USA | ⚠️ Teilweise — auditierbar, aber US-Jurisdiktion |
| Mistral AI | ❌ Nicht vollständig | ✅ Ja | ⚠️ Teilweise — europäisch, aber Trainingsdaten unbekannt |
| Alle anderen | ❌ Nein | ❌ Nein | ❌ Nein |

**Das strukturelle Problem:** Europa hat aktuell nur einen vollständig qualifizierten
Zulieferer (Soofi/8ra). Das ist das eigentliche Risiko — nicht die Lizenzstrategie
einzelner Anbieter. OLMo ist als zweiter Zulieferer für Auditierbarkeit wertvoll,
löst aber die Frage der Jurisdiktion nicht. Die Argumentation für weitere europäische
Initiativen wie 8ra und IPCEI-AI wird dadurch gestärkt, nicht geschwächt.

### Unbekannter Trainingsinhalt als technisches Risiko

Über die lizenz- und geopolitischen Aspekte hinaus besteht bei nicht-transparenten Modellen
ein inhärentes **technisches Risiko durch unbekannte Trainingsdaten**:

- **Unbekannte Datenquellen**: Bei Modellen wie Qwen oder DeepSeek ist nicht nachvollziehbar,
  welche Texte, Dokumente und Webseiten im Training verwendet wurden. Copyright-Verletzungen,
  urheberrechtlich geschützte Industriedaten oder problematische Inhalte können ohne Wissen
  der Nutzer eingeflossen sein.
- **Unbekannte Verzerrungen (Biases)**: Ohne Kenntnis der Trainingsdaten lassen sich
  systematische Verzerrungen — politischer, kultureller oder wirtschaftlicher Natur — nicht
  identifizieren oder ausschließen. Für regulierte Branchen (Medizin, Recht, Finanzen) ist
  das ein Compliance-Risiko.
- **Backdoors und Datenvergiftung**: Es kann nicht ausgeschlossen werden, dass Modelle
  unbekannter Herkunft gezielt auf bestimmte Eingaben trainiert wurden, die ein
  vorhersehbares, unerwünschtes Verhalten auslösen (sog. Training-Backdoors).
  Bei Modellen aus geopolitisch sensiblen Ländern ist dieses Risiko besonders relevant.
- **Keine Auditierbarkeit**: Da weder Trainingsdaten noch -code offenliegen, ist eine
  unabhängige Überprüfung nicht möglich — eine Grundvoraussetzung für den EU AI Act
  (Hochrisiko-KI-Systeme) und für vertrauenswürdige industrielle Anwendungen.

Die Soofi-Modelle sind als einzige Modelle dieser Liste vollständig auditierbar:
Gewichte, Trainingscode und Trainingsdaten sind öffentlich zugänglich und können
unabhängig überprüft werden.

### Europäische Souveränitäts-Empfehlung

Für Anwendungen mit Anforderungen an digitale Souveränität, DSGVO-Konformität oder
langfristige Planungssicherheit gilt folgende Priorisierung:

1. **Mistral AI** (🇫🇷 EU, Apache 2.0) — einzige europäische Familie, bislang keine
   Lizenzänderungen, DSGVO-nahe Unternehmenskultur
2. **Microsoft Phi / Meta Llama** (🇺🇸 USA, MIT/Llama CL) — US-rechtliche Abhängigkeit,
   aber etablierte Ökosysteme; akzeptabel für nicht-sicherheitskritische Anwendungen
3. **Alibaba Qwen / DeepSeek** (🇨🇳 China) — technisch leistungsfähig, aber hohes
   Lizenz-Instabilitätsrisiko und geopolitische Abhängigkeit; für sensitive Anwendungen
   nicht empfohlen

---

## Soofi / 8ra-Initiative ⭐ Empfohlen

| Eigenschaft | Wert |
|-------------|------|
| **Konsortium** | DFKI, Fraunhofer IAIS & IIS, L3S Research Center (Uni Hannover), Lamarr Institute, TU Darmstadt, Uni Würzburg, Berliner Hochschule für Technik, ellamind, Merantix Momentum |
| **Koordination** | KI-Bundesverband |
| **Land** | Deutschland 🇩🇪 / EU 🇪🇺 |
| **Förderung** | Bundesministerium für Wirtschaft und Energie (BMWE), IPCEI-CIS, 8ra-Initiative |
| **Lizenz** | Vollständig Open Source (Gewichte + Code) |
| **Offenheit** | Höchste Stufe — Open Weights + offene Lizenz + europäische Governance-Struktur verhindert einseitige Lizenzänderungen |
| **Souveränität** | Maximale digitale Souveränität: vollständig in Europa entwickelt, trainiert und betrieben. Als einzige Modelle dieser Liste werden Gewichte, Trainingscode **und** Trainingsdaten vollständig offengelegt — vollständig auditierbar und EU-AI-Act-konform. Keine geopolitische Abhängigkeit von US- oder chinesischen Anbietern. DSGVO-konform by design. Kein Vendor-Lock-in durch Konsortiumsstruktur. Empfohlene Basis für alle souveränitätskritischen Anwendungen in Industrie, Behörden und Forschung. |

### Geplante Modell-Releases (Stand April 2025)

| Modell | Größe | Architektur | Deployment | Geplanter Launch | Anwendungsfälle |
|--------|-------|------------|-----------|-----------------|-----------------|
| Soofi 8B | 8B | Dense | Edge / Cloud | Mitte Mai 2025 | Instruction Following, Klassifikation, NER, Domänenadaption, Q&A, Chatbot — optimiert für deutsche Sprache und industrielle Anwendungsfälle |
| Soofi 30B | 30B | MoE | Cloud | Ende Mai 2025 | Komplexes Reasoning, Dokumentenanalyse, mehrsprachiges Q&A, Zusammenfassung, Domänenadaption |
| Soofi 120B | 120B | MoE | Cloud (Multi-GPU) | Ende Juli 2025 | High-Quality-Generierung, wissenschaftliche Texte, komplexe mehrstufige Aufgaben, industrielle Expertensysteme |

> Modellnamen sind vorläufig. Alle Release-Termine unter Vorbehalt (???).

---

## Allen Institute for AI — OLMo

| Eigenschaft | Wert |
|-------------|------|
| **Unternehmen** | Allen Institute for AI (Ai2) |
| **Land** | USA 🇺🇸 |
| **Lizenz** | Apache 2.0 |
| **Offenheit** | Vollständig open source — Gewichte, Trainingscode **und** Trainingsdaten offengelegt |
| **Trainingsdaten** | Dolmino-Mix (Pretraining), Tulu-3-Mixture (SFT), RLVR-Datasets (alle öffentlich auf HuggingFace) |
| **Trainingscode** | Vollständig offen unter github.com/allenai/OLMo (Apache 2.0) |
| **Souveränität** | US-amerikanisches Unternehmen, unterliegt US-Recht und CLOUD Act. Als einziges nicht-europäisches Modell vollständig auditierbar — Trainingsdaten und -pipeline sind vollständig offengelegt und unabhängig überprüfbar. Für Anwendungen, bei denen Auditierbarkeit wichtiger ist als europäische Jurisdiktion, ein wertvoller zweiter Zulieferer neben Soofi/8ra. Für streng souveränitätskritische EU-Anwendungen (Behörden, Rüstung) wegen US-Rechtsrahmen nicht ausreichend. |

### Edge

| Modell | Größe | Deployment | Anwendungsfälle |
|--------|-------|-----------|-----------------|
| OLMo 2 1B Instruct | 1B | Edge | Klassifikation, einfache Extraktion, Forschung |
| OLMo 2 7B Instruct | 7B | Edge | Instruction Following, Q&A, Klassifikation, Domänenadaption |

### Cloud

| Modell | Größe | Deployment | Anwendungsfälle |
|--------|-------|-----------|-----------------|
| OLMo 2 13B Instruct | 13B | Cloud | Instruction Following, Zusammenfassung, Domänenadaption |
| OLMo 2 32B Instruct | 32B | Cloud | Komplexes Reasoning, Dokumentenanalyse, Q&A |
| OLMo 3 7B Instruct | 7B | Edge | Instruction Following, Q&A — neueste Generation |
| OLMo 3.1 32B Instruct | 32B | Cloud | Komplexe Aufgaben — neueste Generation |

---

## Mistral AI

| Eigenschaft | Wert |
|-------------|------|
| **Unternehmen** | Mistral AI |
| **Land** | Frankreich 🇫🇷 (EU) |
| **Lizenz** | Apache 2.0 (Mistral 7B, Nemo, Small, Mixtral) |
| **Offenheit** | Open Weights + offene Lizenz |
| **Souveränität** | Europäisches Unternehmen, DSGVO-konform, keine US-Exportkontroll-Abhängigkeit. Derzeit beste Wahl für souveräne EU-Deployments. Trainingsdaten nicht offengelegt. |

### Edge

| Modell | Größe | Deployment | Anwendungsfälle |
|--------|-------|-----------|-----------------|
| Mistral 7B Instruct v0.3 | 7B | Edge | Instruction Following, Klassifikation, Zusammenfassung, Chatbot |

### Cloud

| Modell | Größe | Deployment | Anwendungsfälle |
|--------|-------|-----------|-----------------|
| Mistral Nemo 12B Instruct | 12B | Cloud | Mehrsprachige Anwendungen (inkl. Deutsch), Q&A, Zusammenfassung |
| Mistral Small 3 24B Instruct | 24B | Cloud | Komplexes Instruction Following, Domänenadaption, Dokumentenanalyse |
| Mixtral 8x22B Instruct (MoE) | 141B gesamt, 39B aktiv | Cloud (Multi-GPU) | Mehrsprachige komplexe Aufgaben, Code, Reasoning |

---

## Microsoft Phi

| Eigenschaft | Wert |
|-------------|------|
| **Unternehmen** | Microsoft Research |
| **Land** | USA 🇺🇸 |
| **Lizenz** | MIT |
| **Offenheit** | Open Weights + offene Lizenz |
| **Souveränität** | US-amerikanisches Unternehmen, unterliegt US-Recht (CLOUD Act). MIT-Lizenz ist maximal permissiv. Phi-Modelle werden auf Azure-Infrastruktur trainiert. Trainingsdaten (synthetisch generiert) nicht vollständig offengelegt. Für sensitive EU-Anwendungen sind US-Rechtsrahmen zu beachten. |

### Edge

| Modell | Größe | Deployment | Anwendungsfälle |
|--------|-------|-----------|-----------------|
| Phi-4-mini Instruct | 3.8B | Edge | Reasoning, Mathematik, Code, strukturierte Extraktion |

### Cloud

| Modell | Größe | Deployment | Anwendungsfälle |
|--------|-------|-----------|-----------------|
| Phi-4 14B Instruct | 14B | Cloud | Reasoning, Mathematik, Code, wissenschaftliche Texte |

---

## Meta Llama

| Eigenschaft | Wert |
|-------------|------|
| **Unternehmen** | Meta Platforms |
| **Land** | USA 🇺🇸 |
| **Lizenz** | Llama Community License (3.1 / 3.2 / 3.3 / 4) — kein OSI-Standard |
| **Offenheit** | Open Weights + eingeschränkte Lizenz |
| **Souveränität** | US-amerikanisches Unternehmen, unterliegt US-Recht und Exportkontrolle. Llama-Lizenz verbietet Nutzung für Anbieter mit > 700 Mio. monatlich aktiven Nutzern ohne Sondervereinbarung. Trainingsdaten nicht offengelegt. Llama 3.x ist de-facto Industriestandard mit breitem Ökosystem. |

### Edge

| Modell | Größe | Deployment | Anwendungsfälle |
|--------|-------|-----------|-----------------|
| Llama 3.2 1B Instruct | 1B | Edge | Klassifikation, einfache Extraktion, Chatbot auf schwacher Hardware |
| Llama 3.2 3B Instruct | 3B | Edge | Klassifikation, NER, einfaches Q&A, Zusammenfassung |
| Llama 3.1 8B Instruct | 8B | Edge | Instruction Following, Chatbot, Zusammenfassung, Domänenadaption |

### Cloud

| Modell | Größe | Deployment | Anwendungsfälle |
|--------|-------|-----------|-----------------|
| Llama 3.1 70B Instruct | 70B | Cloud (Multi-GPU) | High-Quality-Generierung, komplexes Reasoning, Dokumentenanalyse |
| Llama 3.3 70B Instruct | 70B | Cloud (Multi-GPU) | Verbesserte Version, stärker bei Instruction Following und Mehrsprachigkeit |

### Cloud (Multi-GPU/Node)

| Modell | Größe | Deployment | Anwendungsfälle |
|--------|-------|-----------|-----------------|
| Llama 3.1 405B Instruct | 405B | Cloud (Multi-Node) | Forschung, komplexe mehrstufige Aufgaben, High-Quality-Generierung |
| Llama 4 Scout (MoE) | ~109B gesamt, 17B aktiv | Cloud (Multi-GPU) | Multimodale Analyse, Reasoning, Instruction Following |
| Llama 4 Maverick (MoE) | ~880B gesamt, 17B aktiv | Cloud (Multi-Node) | Komplexe multimodale Aufgaben, Forschung |

---

## Google Gemma

| Eigenschaft | Wert |
|-------------|------|
| **Unternehmen** | Google DeepMind |
| **Land** | USA 🇺🇸 |
| **Lizenz** | Gemma License (proprietär, kein OSI-Standard) |
| **Offenheit** | Open Weights + proprietäre Lizenz |
| **Souveränität** | US-amerikanisches Unternehmen, unterliegt US-Recht. Gemma-Lizenz erfordert Zustimmung zu Google-Nutzungsbedingungen und HuggingFace-Gating (Zugangsberechtigung nötig). Acceptable Use Policy schränkt bestimmte Anwendungen ein. Trainingsdaten nicht offengelegt. |

### Edge

| Modell | Größe | Deployment | Anwendungsfälle |
|--------|-------|-----------|-----------------|
| Gemma 3 1B | 1B | Edge | Klassifikation, Sentiment, einfaches Q&A |
| Gemma 3 4B | 4B | Edge | Instruction Following, Klassifikation, Zusammenfassung |

### Cloud

| Modell | Größe | Deployment | Anwendungsfälle |
|--------|-------|-----------|-----------------|
| Gemma 2 9B Instruct | 9B | Cloud | Instruction Following, Q&A, Domänenadaption |
| Gemma 3 12B Instruct | 12B | Cloud | Mehrsprachige Anwendungen, Instruction Following, Zusammenfassung |
| Gemma 3 27B Instruct | 27B | Cloud | Komplexe Analyse, Dokumentenverarbeitung, High-Quality-Generierung |

---

## Qwen (Alibaba)

| Eigenschaft | Wert |
|-------------|------|
| **Unternehmen** | Alibaba Group (DAMO Academy) |
| **Land** | China 🇨🇳 |
| **Lizenz** | Apache 2.0 (meiste Modelle); Qwen Community License (3B- und 72B-Varianten) |
| **Offenheit** | Open Weights + offene Lizenz (Apache 2.0-Varianten) |
| **Souveränität** | Chinesisches Unternehmen, unterliegt chinesischem Recht und potenziellen Exportbeschränkungen. Für sensitive EU-Anwendungen und Rüstungs-/Behördenumgebungen kritisch zu bewerten. Technisch sehr leistungsfähig und lizenzrechtlich offen (Apache 2.0), aber geopolitische Abhängigkeit beachten. Trainingsdaten nicht offengelegt. |

### Edge

| Modell | Größe | Deployment | Anwendungsfälle |
|--------|-------|-----------|-----------------|
| Qwen2.5 0.5B Instruct | 0.5B | Edge | Klassifikation, einfache Extraktion, Keyword-Erkennung |
| Qwen2.5 1.5B Instruct | 1.5B | Edge | Klassifikation, Sentiment-Analyse, kurze Textzusammenfassung |
| Qwen2.5 3B Instruct | 3B | Edge | Klassifikation, NER, einfaches Q&A, Chatbot |
| Qwen2.5 7B Instruct | 7B | Edge | Instruction Following, Q&A, Zusammenfassung, Chatbot, NER |
| Qwen3 0.6B | 0.6B | Edge | Klassifikation, einfache Extraktion, Reasoning (Thinking-Mode) |
| Qwen3 1.7B | 1.7B | Edge | Klassifikation, Sentiment, einfaches Reasoning |
| Qwen3 4B | 4B | Edge | Instruction Following, Reasoning, Klassifikation, Q&A |
| Qwen3 8B | 8B | Edge | Instruction Following, Reasoning, Zusammenfassung, Chatbot, Code |

### Cloud

| Modell | Größe | Deployment | Anwendungsfälle |
|--------|-------|-----------|-----------------|
| Qwen2.5 14B Instruct | 14B | Cloud | Instruction Following, Domänenadaption, Zusammenfassung, Q&A |
| Qwen2.5 32B Instruct | 32B | Cloud | Komplexes Reasoning, Dokumentenanalyse, mehrsprachiges Q&A |
| Qwen2.5 72B Instruct | 72B | Cloud | High-Quality-Generierung, komplexe Analyse, mehrsprachige Anwendungen |
| Qwen3 14B | 14B | Cloud | Reasoning, Instruction Following, Domänenadaption, Code |
| Qwen3 32B | 32B | Cloud | Komplexes Reasoning, mehrstufige Aufgaben, Dokumentenanalyse |
| Qwen3 30B-A3B (MoE) | 30B gesamt, 3B aktiv | Cloud | Schnelles Reasoning bei niedrigem VRAM-Verbrauch |
| Qwen3.5 27B | 27B | Cloud | Instruction Following, Reasoning, mehrsprachige Anwendungen |
| Qwen3.5 35B-A3B (MoE) | 35B gesamt, 3B aktiv | Cloud | Effizientes Reasoning, Klassifikation, Domänenadaption |

### Cloud (Multi-GPU/Node)

| Modell | Größe | Deployment | Anwendungsfälle |
|--------|-------|-----------|-----------------|
| Qwen3 235B-A22B (MoE) | 235B gesamt, 22B aktiv | Cloud (Multi-GPU) | Komplexe mehrstufige Analyse, High-Quality-Generierung, Forschung |

---

## NVIDIA Nemotron

| Eigenschaft | Wert |
|-------------|------|
| **Unternehmen** | NVIDIA |
| **Land** | USA 🇺🇸 |
| **Lizenz** | NVIDIA Open Model License / NVIDIA Community Model License (proprietär) |
| **Offenheit** | Open Weights + proprietäre Lizenz |
| **Souveränität** | US-amerikanisches Unternehmen, unterliegt US-Recht und Exportkontrolle. Proprietäre Lizenz schränkt Redistribution ein. Nemotron-Modelle erfordern für Fine-Tuning zusätzlich das NeMo-Framework (NVIDIA-spezifisch) — das geht über die CUDA-Abhängigkeit hinaus, die faktisch für alle großen Modelle gilt. Besonders geeignet für Deployments auf NVIDIA-H-Serie-Infrastruktur. |

### Edge

| Modell | Größe | Deployment | Anwendungsfälle |
|--------|-------|-----------|-----------------|
| Nemotron Mini 4B Instruct | 4B | Edge | Chatbot, Instruction Following, Klassifikation |

### Cloud

| Modell | Größe | Deployment | Anwendungsfälle |
|--------|-------|-----------|-----------------|
| Llama 3.3 Nemotron Super 49B | 49B | Cloud (Multi-GPU) | Enterprise-NLP, Reasoning, komplexes Instruction Following |
| Llama 3.1 Nemotron 70B Instruct | 70B | Cloud (Multi-GPU) | High-Quality Enterprise-NLP, Reasoning, Dokumentenanalyse |

### Cloud (Multi-GPU/Node)

| Modell | Größe | Deployment | Anwendungsfälle |
|--------|-------|-----------|-----------------|
| Nemotron-4 340B Instruct | 340B | Cloud (Multi-Node) | Forschung, synthetische Datengenerierung, komplexe Analyse |

---

## DeepSeek

| Eigenschaft | Wert |
|-------------|------|
| **Unternehmen** | DeepSeek (Tochter von High-Flyer Capital Management) |
| **Land** | China 🇨🇳 |
| **Lizenz** | MIT |
| **Offenheit** | Open Weights + offene Lizenz (MIT) |
| **Souveränität** | Chinesisches Unternehmen, unterliegt chinesischem Recht. MIT-Lizenz ist maximal permissiv — lizenzrechtlich keinerlei Einschränkungen. Für sensitive EU/Behördenanwendungen ist die geopolitische Herkunft zu bewerten. Die R1-Distill-Modelle basieren auf Qwen- und Llama-Basismodellen (chinesische bzw. US-amerikanische Ursprungsmodelle). Trainingsdaten und -methodik nicht vollständig offengelegt. |

### Edge

| Modell | Größe | Deployment | Anwendungsfälle |
|--------|-------|-----------|-----------------|
| DeepSeek-R1-Distill-Qwen 1.5B | 1.5B | Edge | Reasoning, Mathematik, strukturierte Problemlösung |
| DeepSeek-R1-Distill-Qwen 7B | 7B | Edge | Reasoning, Mathematik, Code, mehrstufige Aufgaben |

### Cloud

| Modell | Größe | Deployment | Anwendungsfälle |
|--------|-------|-----------|-----------------|
| DeepSeek-R1-Distill-Qwen 14B | 14B | Cloud | Komplexes Reasoning, Mathematik, Code, wissenschaftliche Analyse |
| DeepSeek-R1-Distill-Qwen 32B | 32B | Cloud | High-Quality Reasoning, mehrstufige Problemlösung |

### Cloud (Multi-GPU/Node)

| Modell | Größe | Deployment | Anwendungsfälle |
|--------|-------|-----------|-----------------|
| DeepSeek-V3 (MoE) | 671B gesamt, 37B aktiv | Cloud (Multi-Node) | High-Quality-Generierung, komplexe Analyse, Forschung |
| DeepSeek-R1 (MoE) | 671B gesamt, 37B aktiv | Cloud (Multi-Node) | State-of-the-Art Reasoning, Mathematik, wissenschaftliche Aufgaben |

---

## Souveränitäts-Übersicht

| Anbieter | Land | Lizenz | Lizenz-Stabilität | Für sensitive EU-Anwendungen |
|----------|------|--------|-------------------|------------------------------|
| **Soofi / 8ra** | 🇩🇪 Deutschland / EU | Vollständig Open Source | ✅ Stabil — Konsortiumsstruktur | ✅✅ Erste Wahl — vollständig europäisch, maximale Souveränität |
| **OLMo (Ai2)** | 🇺🇸 USA | Apache 2.0 | ✅ Stabil | ⚠️ Vollständig auditierbar, aber US-Jurisdiktion — zweiter Zulieferer für Auditierbarkeit |
| Mistral AI | 🇫🇷 EU | Apache 2.0 | ✅ Stabil | ✅ Europäisch, DSGVO-nah — aber Trainingsdaten nicht vollständig offen |
| Microsoft Phi | 🇺🇸 USA | MIT | ✅ Stabil | ⚠️ US-Unternehmen, CLOUD Act, offene Lizenz |
| Meta Llama | 🇺🇸 USA | Llama CL | ✅ Stabil | ⚠️ US-Unternehmen, eingeschränkte Lizenz, kein OSI-Standard |
| Google Gemma | 🇺🇸 USA | Gemma (prop.) | ⚠️ Unklar | ⚠️ US-Unternehmen, proprietäre Lizenz, Gating |
| NVIDIA Nemotron | 🇺🇸 USA | NVIDIA (prop.) | ⚠️ Unklar | ⚠️ US-Unternehmen, proprietäre Lizenz, zusätzliche Framework-Bindung (NeMo) |
| Alibaba Qwen | 🇨🇳 China | Apache 2.0 / Qwen CL | ❌ Hohes Risiko — Qwen 3.6 Plus bereits Closed-Source | ❌ Chinesisches Unternehmen, nachgewiesene Lizenzänderung |
| DeepSeek | 🇨🇳 China | MIT | ⚠️ Unklar | ❌ Chinesisches Unternehmen, geopolitische Abhängigkeit |
| MiniMax | 🇨🇳 China | Modified MIT | ❌ Hohes Risiko — kommerzielle Nutzung genehmigungspflichtig | ❌ Chinesisches Unternehmen, nachgewiesene Lizenzänderung |

---

## Anwendungsfall-Übersicht

| Anwendungsfall | Empfohlene Modelle (Edge) | Empfohlene Modelle (Cloud) |
|---------------|--------------------------|---------------------------|
| Textklassifikation | Qwen3 4B, Phi-4-mini, Llama 3.2 3B | Qwen3 14B, Mistral Small 24B |
| NER / Extraktion | Qwen2.5 7B, Llama 3.2 3B | Qwen3 14B, Llama 3.3 70B |
| Zusammenfassung | Qwen3 8B, Mistral 7B | Mistral Nemo 12B, Qwen3 32B |
| Q&A / Chatbot | Qwen3 8B, Llama 3.1 8B, Phi-4-mini | Llama 3.3 70B, Qwen3 32B |
| Reasoning / Mathematik | Phi-4-mini, DeepSeek-R1-Distill 7B, Qwen3 4B | DeepSeek-R1-Distill 32B, Qwen3 32B |
| Code-Generierung | Qwen3 8B | Qwen3 32B, Llama 3.3 70B |
| Domänenadaption | Qwen2.5 7B, Llama 3.1 8B | Mistral Small 24B, Qwen2.5 32B |
| Mehrsprachig (inkl. Deutsch) | Qwen3 8B, Mistral 7B | Mistral Nemo 12B, Qwen2.5 72B |
| Wissenschaftliche Texte | Phi-4-mini | Phi-4 14B, DeepSeek-R1-Distill 32B |
| Synthetische Datengenerierung | — | Nemotron-4 340B, DeepSeek-V3 |
| Souverän (EU-Präferenz) | Soofi 8B, Mistral 7B | Soofi 30B, Soofi 120B, Mistral Nemo 12B |
| Industrielle Anwendungen (DE) | Soofi 8B | Soofi 30B, Soofi 120B |
