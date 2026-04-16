# Modellauswahl nach Anwendungsfall

Übersicht empfohlener Basismodelle für häufige Aufgabentypen. Für Details zu Lizenz,
Souveränität und verfügbaren Varianten siehe die jeweilige Modellfamilien-Dokumentation
in [`base_models.md`](base_models.md).

> **Deployment-Kategorien** (Edge / Cloud / Cloud Multi-GPU) und die Hardware-Grenzen pro Kategorie
> sind in [`base_models.md`](base_models.md) dokumentiert.

## Empfehlungen nach Aufgabentyp

| Aufgabe | Edge-Modelle | Cloud-Modelle |
|---------|-------------|---------------|
| Textklassifikation | Qwen3 4B, Phi-4-mini, Llama 3.2 3B | Qwen3 14B, Mistral Small 24B |
| NER / Extraktion | Qwen2.5 7B, Llama 3.2 3B | Qwen3 14B, Llama 3.3 70B |
| Zusammenfassung | Qwen3 8B, Mistral 7B | Mistral Nemo 12B, Qwen3 32B |
| Q&A / Chatbot | Qwen3 8B, Llama 3.1 8B, Phi-4-mini | Llama 3.3 70B, Qwen3 32B |
| Reasoning / Mathematik | Phi-4-mini, DeepSeek-R1-Distill 7B, Qwen3 4B | DeepSeek-R1-Distill 32B, Qwen3 32B |
| Code-Generierung | Qwen3 8B | Qwen3 32B, Llama 3.3 70B |
| Domänenadaption / Fine-Tuning | Qwen2.5 7B, Llama 3.1 8B | Mistral Small 24B, Qwen2.5 32B |
| Mehrsprachig (inkl. Deutsch) | Qwen3 8B, Mistral 7B | Mistral Nemo 12B, Qwen2.5 72B |
| Wissenschaftliche Texte | Phi-4-mini | Phi-4 14B, DeepSeek-R1-Distill 32B |
| Synthetische Datengenerierung | — | Nemotron-4 340B, DeepSeek-V3 |
| Souverän (EU-Präferenz) | Soofi 8B, Mistral 7B | Soofi 30B, Soofi 120B, Mistral Nemo 12B |
| Industrielle Anwendungen (DE) | Soofi 8B | Soofi 30B, Soofi 120B |

## Souveränitäts-Hinweis

Für Anwendungen mit Anforderungen an digitale Souveränität, DSGVO-Konformität oder
langfristige Planungssicherheit siehe die Priorisierung in
[`../sovereignty/anbieter_vergleich.md`](../sovereignty/anbieter_vergleich.md).
