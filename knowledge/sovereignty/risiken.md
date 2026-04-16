# Strategische Risiken proprietärer und außereuropäischer KI-Modelle

## Lizenz-Instabilität

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

## Geopolitischer Zugang zu Spitzenfähigkeiten

US-amerikanische Anbieter geraten unter politischen Druck, leistungsfähige Modelle nur
eingeschränkt verfügbar zu machen:

- Anthropics Modell „Claude Mythos Preview" wurde nicht öffentlich freigegeben. Der Zugang
  erfolgt exklusiv über „Project Glasswing" — ausschließlich an US-Unternehmen
  (Microsoft, NVIDIA, Apple, Cisco) sowie die Linux Foundation.
  **Kein europäischer Partner ist beteiligt.**
- Bei sicherheitskritischen KI-Fähigkeiten ist Europa damit strukturell außen vor.

## Compliance-Konflikt für EU-Anwender

US-Anbieter stehen zwischen widersprüchlichen Anforderungen:

- **US-Seite**: Druck zur Freigabe für militärische und Überwachungsanwendungen.
  Das Pentagon hat Anthropic zeitweise als „supply chain risk" eingestuft, weil das
  Unternehmen die Nutzung für autonome Waffensysteme ablehnt.
- **EU-Seite**: EU AI Act und DSGVO verlangen Transparenz, Nachvollziehbarkeit und
  Datenschutz — unvereinbar mit militärischer Dual-Use-Nutzung.

Für europäische Industriekunden bedeutet das: US-Modelle, deren Anbieter zwischen
US-Regierungsanforderungen und EU-Compliance zerrissen werden, sind kein stabiles
Fundament für langfristige Produktionssysteme.

## Unbekannter Trainingsinhalt als technisches Risiko

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
