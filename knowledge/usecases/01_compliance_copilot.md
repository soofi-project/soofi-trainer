# Use Case: Compliance-Copilot

**Domäne:** Regulierung, Recht, Governance, Cloud- und Dateninfrastruktur

## Beschreibung

Ein Compliance-Copilot prüft systematisch, ob Architektur- und Betriebsentscheidungen die
Anforderungen aus DSGVO, EU AI Act, NIS2, Datenresidenz und Portabilität erfüllen. Er
analysiert Richtlinien, Verträge und Auditberichte, identifiziert Lücken und formuliert
nachvollziehbare Begründungen für Compliance-Entscheidungen. Besonders relevant für
Unternehmen, die öffentliche Aufträge vergeben oder vergaberechtlich gebunden sind.

## Warum souverän?

Compliance-Prüfungen enthalten oft vertrauliche Architekturdetails, interne
Sicherheitsrichtlinien und personenbezogene Auditdaten — Informationen, die nicht an
externe Cloud-APIs gesendet werden dürfen.

## Datenbasis

Regulatorische Texte (DSGVO, AI Act, NIS2), interne Richtlinien, Architekturentscheidungen,
Auditberichte, Sicherheitsstandards, annotierte Fallbeispiele

## Empfohlene Methode

RAG als Grundlage (Retrieval über Normen und Policies) + Supervised Fine-Tuning für
domänenspezifische Instruktionen und Ausgabeformate + Preference Tuning für risikoaverse,
regelorientierte Antworten

## Soofi-Fit

**Hoch** — Kombination aus RAG und LoRA/DPO; lokaler Betrieb als Voraussetzung
