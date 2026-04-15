# Anwendungsfälle für souveräne LLM-Spezialisierung

Souveräne, domänenspezifisch angepasste Sprachmodelle sind besonders dort wertvoll, wo
sensible Daten, europäische Regulierung und fachspezifische Präzisionsanforderungen
zusammentreffen. Nicht generische Chatbots, sondern spezialisierte Assistenzsysteme auf
eigenen Daten, eigener Infrastruktur und mit nachvollziehbaren Ergebnissen — das ist der
Kern des Soofi-Ansatzes.

Der größte Mehrwert entsteht, wenn ein Modell nicht nur Wissen wiedergeben, sondern
strukturierte Entscheidungen vorbereiten, komplexe Dokumente auswerten und domänenspezifische
Ausgaben in definierten Formaten erzeugen muss.

---

## 1. Compliance-Copilot

**Domäne:** Regulierung, Recht, Governance, Cloud- und Dateninfrastruktur

**Beschreibung:** Ein Compliance-Copilot prüft systematisch, ob Architektur- und
Betriebsentscheidungen die Anforderungen aus DSGVO, EU AI Act, NIS2, Datenresidenz und
Portabilität erfüllen. Er analysiert Richtlinien, Verträge und Auditberichte, identifiziert
Lücken und formuliert nachvollziehbare Begründungen für Compliance-Entscheidungen. Besonders
relevant für Unternehmen, die öffentliche Aufträge vergeben oder vergaberechtlich gebunden sind.

**Warum souverän?** Compliance-Prüfungen enthalten oft vertrauliche Architekturdetails,
interne Sicherheitsrichtlinien und personenbezogene Auditdaten — Informationen, die nicht
an externe Cloud-APIs gesendet werden dürfen.

**Datenbasis:** Regulatorische Texte (DSGVO, AI Act, NIS2), interne Richtlinien,
Architekturentscheidungen, Auditberichte, Sicherheitsstandards, annotierte Fallbeispiele

**Methode:** RAG als Grundlage (Retrieval über Normen und Policies) + Supervised Fine-Tuning
für domänenspezifische Instruktionen und Ausgabeformate + Preference Tuning für risikoaverse,
regelorientierte Antworten

**Soofi-Fit:** Hoch — Kombination aus RAG und LoRA/DPO; lokaler Betrieb als Voraussetzung

---

## 2. Wissensmanagement und Produktionsdokumentation

**Domäne:** Fertigung, Instandhaltung, Qualitätssicherung, Maschinenbau

**Beschreibung:** Fertigungsunternehmen verfügen über umfangreiche technische Dokumentation:
Wartungshandbücher, Fehlerkataloge, SOPs, Maschinenbeschreibungen und Qualitätsnormen. Ein
spezialisierter Assistent beantwortet Fragen der Techniker direkt aus diesen Dokumenten —
ohne langes Suchen in dicken Handbüchern oder Warten auf den Experten. Typische Fragen:
Wartungsintervalle, Fehlercodes, Reparaturschritte, zulässige Materialien.

**Warum souverän?** Produktionsdaten und Maschinendokumentation enthalten
Geschäftsgeheimnisse und proprietäres Know-how. Externe APIs sind ausgeschlossen.

**Datenbasis:** Technische Handbücher (PDF), Fehlerkataloge, SOPs, Wartungsprotokolle,
Qualitätsnormen (ISO, DIN), interne Wissensdatenbanken

**Methode:** Primär RAG — Dokumente werden in die Wissensdatenbank geladen, das Modell
greift bei jeder Frage auf relevante Abschnitte zu. Fine-Tuning sinnvoll, wenn
unternehmensspezifisches Vokabular (Maschinenbezeichnungen, Fehlercodes) im Basismodell
unbekannt ist.

**Soofi-Fit:** Sehr hoch — klassischer Einstiegs-Use-Case; sofort einsetzbar mit RAG,
klarer Erweiterungspfad zu Fine-Tuning

---

## 3. Engineering-Copilot und Qualitätssicherung

**Domäne:** Entwicklung, Systemtechnik, Telekommunikation, Embedded Systems, QA

**Beschreibung:** Technische Teams arbeiten täglich mit Standards, Spezifikationen,
Testergebnissen und Defektberichten. Ein Engineering-Copilot unterstützt bei Root-Cause-Analyse,
Qualitätsprüfung, Testfallgenerierung und Dokumentation — auf Basis interner Dokumente und
Normen, nicht aus dem Allgemeinwissen des Modells. Kritisches Fachwissen bleibt an europäischen
Plattformen gebunden statt in externe Dienste abzufließen.

**Warum souverän?** Produktspezifikationen, Testdaten und Fehlerberichte sind geistiges
Eigentum; Compliance mit Exportkontrollvorschriften (ITAR, EAR) schließt externe Dienste oft aus.

**Datenbasis:** Technische Standards (IEC, IEEE, 3GPP), interne Spezifikationen,
Defekt- und Testdatenbanken, QA-Handbücher, Postmortem-Analysen

**Methode:** RAG über Standards und Spezifikationen + SFT für kontrollierte Reasoning-Ketten
(Root-Cause-Analyse, strukturierte QA-Outputs)

**Soofi-Fit:** Hoch — RAG als Einstieg, gezieltes Fine-Tuning auf Fachsprache und
Ausgabeformat

---

## 4. Predictive-Maintenance-Assistent

**Domäne:** Fertigung, Anlagenbetrieb, Energieversorgung, Infrastruktur

**Beschreibung:** Anlagen senden kontinuierlich Betriebs- und Sensordaten. Ein spezialisierter
Assistent erkennt frühzeitig Muster, die auf drohende Ausfälle hinweisen, erklärt die
identifizierten Anomalien in verständlicher Sprache und empfiehlt konkrete Wartungsmaßnahmen.
Er verbindet strukturierte Maschinendaten mit technischem Dokumentationswissen — ein Hybrid
aus Datenanalyse und Wissensbasis.

**Warum souverän?** Produktionsdaten und Anlagentelemetrie sind geschäftskritisch und
dürfen die eigene Infrastruktur nicht verlassen.

**Datenbasis:** Sensordaten (Zeitreihen), Wartungsprotokolle, Ausfallhistorien, technische
Dokumentation, Lieferantenspezifikationen

**Methode:** RAG für Handbuch- und Protokollwissen + Fine-Tuning für domänenspezifische
Anomalieerkennung und Erklärungssprache; bei strukturierten Sensordaten ggf. Kombination
mit Zeitreihenanalyse als Vorverarbeitungsschritt

**Soofi-Fit:** Mittel bis hoch — Einstieg über RAG möglich; Full-Stack erfordert Anbindung
von Sensordatenquellen

---

## 5. Federation- und Incident-Reasoning-Assistent

**Domäne:** IT-Betrieb, Cloud-Infrastruktur, Security Operations, kritische Infrastruktur

**Beschreibung:** In föderierten Multi-Provider-Infrastrukturen ist die Ursachenanalyse
bei Störungen komplex: Ereignisse aus verschiedenen Systemen müssen korreliert, Hypothesen
strukturiert und Runbooks kontextbezogen angewendet werden. Ein Incident-Reasoning-Assistent
beschleunigt Root-Cause-Analyse, priorisiert Eskalationen und unterstützt das Team bei der
Wiederherstellung — besonders in Situationen, wo Zeitdruck und Komplexität zusammentreffen.

**Warum souverän?** Incident-Daten, Topologien und Sicherheitsprotokolle sind hochsensibel;
für kritische Infrastrukturen (Energie, Telco, Behörden) ist souveräner Betrieb oft
regulatorisch vorgeschrieben.

**Datenbasis:** Incident-Tickets, Monitoring- und Telemetriedaten, Netzwerktopologien,
Betriebsdokumentation, Postmortems, SLA-Regeln, Playbooks

**Methode:** Tool-Use-Tuning + ReAct-artige Ablaufdaten + domänenspezifisches SFT für
strukturierte Reasoning-Traces; Anbindung an SIEM, CMDB und Ticketing-Systeme

**Soofi-Fit:** Mittel — erfordert umfangreiche operative Datenbasis; gut für
Organisationen mit reifem IT-Betrieb

---

## 6. Mehrsprachiger KMU-Copilot

**Domäne:** Mittelstand, Handel, Service, Kundenkommunikation, HR

**Beschreibung:** Europäische KMU kommunizieren in vielen Sprachen — mit Kunden, Lieferanten
und Mitarbeitern. Ein mehrsprachiger Copilot unterstützt bei Support, Service, internen
Wissensabfragen und Prozessassistenz. Mehrsprachigkeit ist ein genuin europäischer Vorteil,
der von außereuropäischen Anbietern oft weniger gut bedient wird — insbesondere für
Sprachkombinationen jenseits von Englisch.

**Warum souverän?** Kundendaten, HR-Informationen und Unternehmenskommunikation unterliegen
der DSGVO; lokale Sprachkompetenz für Fachsprache und Dialekte entsteht nur durch
domänenspezifisches Training.

**Datenbasis:** Interne Wissensdatenbanken, FAQ, Produktkataloge, Kommunikationshistorien,
HR-Dokumente (mehrsprachig)

**Methode:** RAG für Wissenszugang + SFT für mehrsprachige Ausgabequalität und
unternehmensspezifischen Sprachstil + Preference Tuning für Service-Ton und Konservativität

**Soofi-Fit:** Hoch — gut geeignet als breiter Einstiegs-Use-Case für KMU ohne tiefe
KI-Expertise

---

## 7. Digital Product Passport Assistenz

**Domäne:** Produktion, Lieferkette, Nachhaltigkeit, Regulierung (EU Green Deal, ESPR)

**Beschreibung:** Der digitale Produktpass (DPP) wird durch EU-Regulierung schrittweise
Pflicht — zunächst für Batterien, Textilien und Elektronik, perspektivisch breiter.
Ein DPP-Assistent extrahiert, normalisiert und begründet Produkt-, Lieferketten- und
Nachhaltigkeitsinformationen aus heterogenen Quellen und erzeugt standardisierte Ausgaben
in definierten Formaten. Er verbindet Regulierungswissen mit produktspezifischen Daten.

**Warum souverän?** Lieferkettendaten und Materialkompositionen sind wettbewerbssensibel;
regulatorische Nachweisführung erfordert auditierbare, lokal betriebene Systeme.

**Datenbasis:** Produktdatenblätter, Zertifizierungsdokumente, technische Spezifikationen,
Materialinformationen, regulatorische Vorgaben (ESPR, EU Batterie-VO), Ontologien

**Methode:** Schemaorientiertes SFT + strukturierte Extraktionsdaten + RAG für Referenzwissen
und Normtexte; Constrained Generation für definierte Ausgabeformate

**Soofi-Fit:** Hoch — wachsender regulatorischer Druck macht diesen Use Case zunehmend
kritisch; gute Kombination aus RAG und Fine-Tuning

---

## 8. Vergabe- und Ausschreibungsassistent

**Domäne:** Öffentliche Verwaltung, öffentliche Beschaffung, Einkauf

**Beschreibung:** Öffentliche Ausschreibungen folgen strikten rechtlichen Vorgaben (GWB,
VgV, VOB, EU-Vergaberecht) und erfordern präzise, formal korrekte Dokumentation. Ein
Vergabe-Copilot unterstützt bei der Erstellung von Leistungsbeschreibungen, der Prüfung
von Angeboten gegen Ausschreibungskriterien und der Dokumentation von Vergabeentscheidungen.

**Warum souverän?** Vergabedaten sind vertraulich; für öffentliche Stellen ist
souveräner Betrieb auf europäischer oder nationaler Infrastruktur vielfach Pflicht.

**Datenbasis:** Vergaberecht (GWB, VgV, VOB, EU-Richtlinien), Leistungsbeschreibungen,
Angebotsdokumente, interne Vergaberichtlinien, frühere Vergabeentscheidungen

**Methode:** RAG für Rechtsbasis + SFT für Vergabefachsprache und Ausgabeformate +
Preference Tuning für regelorientierte, risikoaverse Ausgaben

**Soofi-Fit:** Mittel — hohes Präzisionserfordernis; gut geeignet für Organisationen
mit umfangreicher Vergabetätigkeit

---

## 9. Verwaltungsassistent für Behörden

**Domäne:** Öffentliche Verwaltung, E-Government, Bürgerservice

**Beschreibung:** Behörden bearbeiten komplexe Verwaltungsvorgänge auf Basis von Gesetzen,
Verordnungen und internen Richtlinien. Ein Verwaltungsassistent unterstützt Sachbearbeitende
bei der Prüfung von Anträgen, der Erläuterung von Rechtsgrundlagen und der Formulierung
von Bescheiden — nachvollziehbar, konsistent und DSGVO-konform.

**Warum souverän?** Behördliche Daten sind besonders schützenswert; für staatliche Stellen
ist souveräner Betrieb auf auditierter Infrastruktur regulatorisch geboten (BSI IT-Grundschutz,
NIS2, EU AI Act Hochrisiko-Einstufung).

**Datenbasis:** Gesetzestexte, Verwaltungsvorschriften, interne Richtlinien,
Präzedenzfälle, Formularvorlagen

**Methode:** RAG als Basis + SFT für Verwaltungssprache und Bescheidformate +
Preference Tuning für Konservativität und Rechtssicherheit

**Soofi-Fit:** Hoch für Behörden — erfordert starke regulatorische Compliance der
Infrastruktur

---

## Methodenwahl nach Anwendungsfall

| Anwendungsfall | RAG | SFT / LoRA | DPO / Preference Tuning |
|---|---|---|---|
| Compliance-Copilot | ✅ Kern | ✅ Formate, Fachsprache | ✅ Risikoaversion |
| Wissensmanagement / Produktionsdoku | ✅ Kern | ⚠️ Bei Spezialvokabular | — |
| Engineering-Copilot / QA | ✅ Kern | ✅ Reasoning-Ketten | — |
| Predictive Maintenance | ✅ Handbücher | ✅ Anomalieerklärung | — |
| Federation Incident Reasoning | ⚠️ Ergänzend | ✅ Kern (Tool-Use, ReAct) | — |
| KMU-Copilot mehrsprachig | ✅ Kern | ✅ Sprachqualität | ✅ Service-Ton |
| Digital Product Passport | ✅ Normtexte | ✅ Extraktion, Formate | — |
| Vergabe-Assistent | ✅ Rechtsbasis | ✅ Fachsprache | ✅ Regelorientierung |
| Verwaltungsassistent | ✅ Gesetze | ✅ Bescheidsprache | ✅ Rechtssicherheit |

**Faustregel:**
- **Nur RAG**: ausreichend wenn das Basismodell die Domänensprache kennt und strukturierte
  Ausgaben nicht zwingend erforderlich sind (klassische Q&A auf eigenen Dokumenten)
- **RAG + Fine-Tuning**: wenn domänenspezifisches Vokabular, definierte Ausgabeformate oder
  spezifische Aufgabenlogik vorliegen
- **+ Preference Tuning**: wenn das Modell in regulierten oder sicherheitskritischen Kontexten
  konservativ, regelorientiert und risikoavers antworten muss
