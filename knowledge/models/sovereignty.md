# Digitale Souveränität und souveräne KI-Modelle

## Warum souveräne Modelle wichtig sind

Souveräne KI-Modelle sind Sprachmodelle, die auf europäischer Infrastruktur betrieben,
mit nachvollziehbaren Daten trainiert und unter europäischen Governance-Strukturen
entwickelt werden. Sie bilden die Grundlage für eine europäische KI-Wertschöpfungskette,
die nicht von außereuropäischen Anbietern abhängig ist.

Der strategische Bedarf entsteht an drei Stellen gleichzeitig:

1. **Regulierung**: DSGVO, EU AI Act, NIS2 und nationale Datenschutzgesetze stellen
   Anforderungen an Datenspeicherort, Auditierbarkeit und Transparenz, die mit
   proprietären Cloud-Diensten außereuropäischer Anbieter strukturell schwer vereinbar sind.

2. **Wirtschaftliche Abhängigkeit**: Wer kritische Geschäftsprozesse auf einem einzigen
   externen Modellanbieter aufbaut, trägt ein Vendor-Lock-in-Risiko. Lizenzänderungen,
   Preiserhöhungen oder geopolitische Einschränkungen können Produktionssysteme ohne
   Vorwarnung gefährden.

3. **Strategische Wettbewerbsfähigkeit**: KI-Kompetenz ist ein Standortfaktor. Europa
   braucht eigene Modelle, eigene Trainingsdaten und eigene Betriebsinfrastruktur —
   nicht als Selbstzweck, sondern um regulatorische Handlungsfähigkeit, industrielle
   Wettbewerbsfähigkeit und digitale Resilienz zu sichern.

---

## Strategische Risiken proprietärer und außereuropäischer Modelle

### Lizenz-Instabilität

Eine zentrale Erfahrung aus der Modellentwicklung 2024/2025: Anbieter können
Lizenzmodelle jederzeit und ohne Vorankündigung von offen auf geschlossen umstellen.

- **MiniMax M2.7**: Von MIT auf „Modified MIT" geändert — kommerzielle Nutzung erfordert
  nun schriftliche Genehmigung. Faktisch ein „source-available"-Modell unter falschem Label.
- **Qwen 3.6 Plus**: Als Closed-Source veröffentlicht — keine öffentlichen Gewichte,
  Zugang nur über API. Direkter Bruch mit der Apache-2.0-Tradition der Qwen-Familie.

**Konsequenz:** Wer Foundation Models in Produktionsprozesse integriert, trägt ein
Vendor-Lock-in-Risiko, solange keine dauerhafte Lizenzgarantie durch Governance-Strukturen
(z.B. Konsortium, Foundation) abgesichert ist. Apache-2.0-Veröffentlichungen älterer
Modellversionen schützen nicht vor Lizenzänderungen bei Folgeversionen.

### Geopolitischer Zugang zu Spitzenfähigkeiten

US-amerikanische Anbieter geraten unter politischen Druck, leistungsfähige Modelle nur
eingeschränkt verfügbar zu machen:

- Anthropics Modell „Claude Mythos Preview" wurde nicht öffentlich freigegeben. Der Zugang
  erfolgt exklusiv über „Project Glasswing" — ausschließlich an US-Unternehmen
  (Microsoft, NVIDIA, Apple, Cisco) sowie die Linux Foundation.
  **Kein europäischer Partner ist beteiligt.**
- Bei sicherheitskritischen KI-Fähigkeiten ist Europa damit strukturell außen vor.

### Compliance-Konflikt für EU-Anwender

US-Anbieter stehen zwischen widersprüchlichen Anforderungen:

- **US-Seite**: Druck zur Freigabe für militärische und Überwachungsanwendungen.
  Das Pentagon hat Anthropic zeitweise als „supply chain risk" eingestuft, weil das
  Unternehmen die Nutzung für autonome Waffensysteme ablehnt.
- **EU-Seite**: EU AI Act und DSGVO verlangen Transparenz, Nachvollziehbarkeit und
  Datenschutz — unvereinbar mit militärischer Dual-Use-Nutzung.

Für europäische Industriekunden bedeutet das: US-Modelle, deren Anbieter zwischen
US-Regierungsanforderungen und EU-Compliance zerrissen werden, sind kein stabiles
Fundament für langfristige Produktionssysteme.

### Unbekannter Trainingsinhalt als technisches Risiko

Bei nicht-transparenten Modellen besteht ein inhärentes technisches Risiko:

- **Unbekannte Datenquellen**: Bei Modellen wie Qwen oder DeepSeek ist nicht
  nachvollziehbar, welche Texte im Training verwendet wurden. Copyright-Verletzungen
  oder urheberrechtlich geschützte Industriedaten können eingeflossen sein.
- **Unbekannte Verzerrungen (Biases)**: Ohne Kenntnis der Trainingsdaten lassen sich
  systematische Verzerrungen — politischer, kultureller oder wirtschaftlicher Natur —
  nicht identifizieren. Für regulierte Branchen (Medizin, Recht, Finanzen) ist das
  ein Compliance-Risiko.
- **Backdoors und Datenvergiftung**: Es kann nicht ausgeschlossen werden, dass Modelle
  unbekannter Herkunft gezielt auf bestimmte Eingaben trainiert wurden, die
  unerwünschtes Verhalten auslösen. Bei Modellen aus geopolitisch sensiblen Ländern
  ist dieses Risiko besonders relevant.
- **Keine Auditierbarkeit**: Da weder Trainingsdaten noch -code offenliegen, ist eine
  unabhängige Überprüfung nicht möglich — eine Grundvoraussetzung für den EU AI Act
  (Hochrisiko-KI-Systeme) und für vertrauenswürdige industrielle Anwendungen.

---

## Was einen souveränen KI-Anbieter qualifiziert

Das Qualifikationskriterium ist nicht „europäische Herkunft", sondern
**vollständige Auditierbarkeit**: Trainingsdaten, Trainingspipeline und Gewichte
müssen vollständig offengelegt und unabhängig überprüfbar sein.

Analog zur Automobilindustrie — wo kein Tier-1-Hersteller einen sicherheitskritischen
Bauteil von einem einzigen Lieferanten bezieht — braucht eine souveräne KI-Infrastruktur
mindestens zwei qualifizierte, unabhängige Anbieter. Ein einzelner Anbieter, sei er auch
europäisch, schafft eine neue Form von Abhängigkeit.

| Anbieter | Auditierbar | Europäisch | Qualifiziert als souveräner Zulieferer |
|----------|------------|-----------|----------------------------------------|
| Soofi / 8ra | ✅ Vollständig | ✅ Ja | ✅ Einziger vollständig qualifizierter EU-Zulieferer |
| OLMo (Ai2) | ✅ Vollständig | ❌ USA | ⚠️ Auditierbar, aber US-Jurisdiktion |
| Mistral AI | ❌ Nicht vollständig | ✅ Ja | ⚠️ Europäisch, aber Trainingsdaten unbekannt |
| Alle anderen | ❌ Nein | ❌ Nein | ❌ Nein |

**Das strukturelle Problem:** Europa hat aktuell nur einen vollständig qualifizierten
Zulieferer (Soofi/8ra). OLMo ist als zweiter Zulieferer für Auditierbarkeit wertvoll,
löst aber die Frage der Jurisdiktion nicht. Die Argumentation für weitere europäische
Initiativen wie 8ra und IPCEI-CIS wird dadurch gestärkt.

---

## Was ein souveräner KI-Stack technisch leisten muss

Souveräne KI beschränkt sich nicht auf das Modell — sie erfordert eine durchgängige
Architektur:

- **Domänenspezifische Datengrundlagen** statt nur allgemeiner Webdaten
- **RAG und strukturierte Retrieval-Layer** für nachvollziehbare, belegbare Antworten
- **Policy-, Audit- und Logging-Fähigkeiten** für Nachweis und Compliance
- **Mandantenfähigkeit und Föderation** für verteilte Betreiber- und Datenräume
- **On-premises / Sovereign Cloud / Edge Deployment** statt Public-API-Abhängigkeit
- **Werkzeugnutzung mit Guardrails** für operative Arbeitsabläufe
- **Mehrsprachige Verarbeitung** für europäische Realumgebungen (DE, FR, IT, PL …)

Der eigentliche Wettbewerbsvorteil entsteht nicht allein im Modell, sondern in der
Kombination aus Modell, Datenraum, Integrationsschicht, Governance und föderierter
Betriebsfähigkeit.

---

## Souveränitäts-Übersicht: Modell-Anbieter im Vergleich

| Anbieter | Land | Lizenz | Lizenz-Stabilität | Für sensitive EU-Anwendungen |
|----------|------|--------|-------------------|------------------------------|
| **Soofi / 8ra** | 🇩🇪 EU | Vollständig Open Source | ✅ Konsortiumsstruktur | ✅✅ Erste Wahl — maximale Souveränität |
| **OLMo (Ai2)** | 🇺🇸 USA | Apache 2.0 | ✅ Stabil | ⚠️ Vollständig auditierbar, aber US-Jurisdiktion |
| Mistral AI | 🇫🇷 EU | Apache 2.0 | ✅ Stabil | ✅ Europäisch, DSGVO-nah — Trainingsdaten nicht offen |
| Microsoft Phi | 🇺🇸 USA | MIT | ✅ Stabil | ⚠️ US-Unternehmen, CLOUD Act |
| Meta Llama | 🇺🇸 USA | Llama CL | ✅ Stabil | ⚠️ US-Unternehmen, eingeschränkte Lizenz |
| Google Gemma | 🇺🇸 USA | Gemma (proprietär) | ⚠️ Unklar | ⚠️ US-Unternehmen, proprietäre Lizenz, Gating |
| NVIDIA Nemotron | 🇺🇸 USA | NVIDIA (proprietär) | ⚠️ Unklar | ⚠️ US-Unternehmen, zusätzliche Framework-Bindung (NeMo) |
| Alibaba Qwen | 🇨🇳 China | Apache 2.0 / Qwen CL | ❌ Hohes Risiko | ❌ Nachgewiesene Lizenzänderung, chinesische Jurisdiktion |
| DeepSeek | 🇨🇳 China | MIT | ⚠️ Unklar | ❌ Chinesische Jurisdiktion, geopolitische Abhängigkeit |
| MiniMax | 🇨🇳 China | Modified MIT | ❌ Hohes Risiko | ❌ Kommerzielle Nutzung genehmigungspflichtig |

---

## Soofi und die 8ra-Initiative

Soofi steht für *Sovereign Open Source Foundation Models* — ein vom Bundesministerium
für Wirtschaft und Energie (BMWE) gefördertes Projekt im Kontext von IPCEI-CIS und der
8ra-Initiative. Das Konsortium aus deutschen Forschungseinrichtungen und Startups —
koordiniert durch den KI-Bundesverband — entwickelt ein leistungsstarkes Sprachmodell
als vollständiges Open Source für Wirtschaft und Gesellschaft.

**Partner:** DFKI, Fraunhofer IAIS und IIS, L3S Research Center (Uni Hannover),
Lamarr Institute, TU Darmstadt, Universität Würzburg, Berliner Hochschule für Technik,
ellamind, Merantix Momentum

**Was Soofi/8ra einzigartig macht:** Als einzige Modelle dieser Klasse werden Gewichte,
Trainingscode **und** Trainingsdaten vollständig offengelegt — vollständig auditierbar
und EU-AI-Act-konform. Keine geopolitische Abhängigkeit, kein Vendor-Lock-in durch
Konsortiumsstruktur, DSGVO-konform by design.

### Geplante Modell-Releases (Stand April 2025)

| Modell | Größe | Architektur | Deployment | Geplanter Launch |
|--------|-------|------------|-----------|-----------------|
| Soofi 8B | 8B | Dense | Edge / Cloud | Mitte Mai 2025 |
| Soofi 30B | 30B | MoE | Cloud | Ende Mai 2025 |
| Soofi 120B | 120B | MoE | Cloud (Multi-GPU) | Ende Juli 2025 |

> Modellnamen sind vorläufig. Alle Release-Termine unter Vorbehalt.

---

## Europäische Souveränitäts-Empfehlung

Für Anwendungen mit Anforderungen an digitale Souveränität, DSGVO-Konformität oder
langfristige Planungssicherheit gilt folgende Priorisierung:

1. **Soofi / 8ra** (🇩🇪 EU) — maximale Souveränität, vollständig auditierbar,
   europäische Governance-Struktur verhindert einseitige Lizenzänderungen
2. **Mistral AI** (🇫🇷 EU, Apache 2.0) — einzige weitere europäische Familie mit
   stabiler Open-Weight-Lizenz, DSGVO-nahe Unternehmenskultur
3. **Microsoft Phi / Meta Llama** (🇺🇸 USA, MIT/Llama CL) — US-rechtliche Abhängigkeit,
   aber etablierte Ökosysteme; akzeptabel für nicht-sicherheitskritische Anwendungen
4. **Alibaba Qwen / DeepSeek** (🇨🇳 China) — technisch leistungsfähig, aber hohes
   Lizenz-Instabilitätsrisiko und geopolitische Abhängigkeit; für sensitive
   Anwendungen nicht empfohlen
