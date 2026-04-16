# Use Case: Predictive-Maintenance-Assistent

**Domäne:** Fertigung, Anlagenbetrieb, Energieversorgung, Infrastruktur

## Beschreibung

Anlagen senden kontinuierlich Betriebs- und Sensordaten. Ein spezialisierter Assistent
erkennt frühzeitig Muster, die auf drohende Ausfälle hinweisen, erklärt die identifizierten
Anomalien in verständlicher Sprache und empfiehlt konkrete Wartungsmaßnahmen. Er verbindet
strukturierte Maschinendaten mit technischem Dokumentationswissen — ein Hybrid aus
Datenanalyse und Wissensbasis.

## Warum souverän?

Produktionsdaten und Anlagentelemetrie sind geschäftskritisch und dürfen die eigene
Infrastruktur nicht verlassen.

## Datenbasis

Sensordaten (Zeitreihen), Wartungsprotokolle, Ausfallhistorien, technische Dokumentation,
Lieferantenspezifikationen

## Empfohlene Methode

RAG für Handbuch- und Protokollwissen + Fine-Tuning für domänenspezifische
Anomalieerkennung und Erklärungssprache; bei strukturierten Sensordaten ggf. Kombination
mit Zeitreihenanalyse als Vorverarbeitungsschritt

## Soofi-Fit

**Mittel bis hoch** — Einstieg über RAG möglich; Full-Stack erfordert Anbindung von
Sensordatenquellen
