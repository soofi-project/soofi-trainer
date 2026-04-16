# Use Case: Wissensmanagement und Produktionsdokumentation

**Domäne:** Fertigung, Instandhaltung, Qualitätssicherung, Maschinenbau

## Beschreibung

Fertigungsunternehmen verfügen über umfangreiche technische Dokumentation: Wartungshandbücher,
Fehlerkataloge, SOPs, Maschinenbeschreibungen und Qualitätsnormen. Ein spezialisierter
Assistent beantwortet Fragen der Techniker direkt aus diesen Dokumenten — ohne langes Suchen
in dicken Handbüchern oder Warten auf den Experten. Typische Fragen: Wartungsintervalle,
Fehlercodes, Reparaturschritte, zulässige Materialien.

## Warum souverän?

Produktionsdaten und Maschinendokumentation enthalten Geschäftsgeheimnisse und proprietäres
Know-how. Externe APIs sind ausgeschlossen.

## Datenbasis

Technische Handbücher (PDF), Fehlerkataloge, SOPs, Wartungsprotokolle, Qualitätsnormen
(ISO, DIN), interne Wissensdatenbanken

## Empfohlene Methode

Primär RAG — Dokumente werden in die Wissensdatenbank geladen, das Modell greift bei jeder
Frage auf relevante Abschnitte zu. Fine-Tuning sinnvoll, wenn unternehmensspezifisches
Vokabular (Maschinenbezeichnungen, Fehlercodes) im Basismodell unbekannt ist.

## Soofi-Fit

**Sehr hoch** — klassischer Einstiegs-Use-Case; sofort einsetzbar mit RAG,
klarer Erweiterungspfad zu Fine-Tuning
