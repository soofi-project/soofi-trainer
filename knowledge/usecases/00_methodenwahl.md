# Methodenwahl nach Anwendungsfall

Übersicht, welche Spezialisierungsmethoden für welche Use Cases empfohlen werden.

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

## Faustregel

- **Nur RAG**: ausreichend wenn das Basismodell die Domänensprache kennt und strukturierte
  Ausgaben nicht zwingend erforderlich sind (klassische Q&A auf eigenen Dokumenten)
- **RAG + Fine-Tuning**: wenn domänenspezifisches Vokabular, definierte Ausgabeformate oder
  spezifische Aufgabenlogik vorliegen
- **+ Preference Tuning**: wenn das Modell in regulierten oder sicherheitskritischen Kontexten
  konservativ, regelorientiert und risikoavers antworten muss
