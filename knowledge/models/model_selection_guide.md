# Modellauswahl nach Anwendungsfall

Übersicht empfohlener Basismodelle für häufige Aufgabentypen. Für Details zu Lizenz,
Souveränität und verfügbaren Varianten siehe die jeweilige Modellfamilien-Dokumentation.

## Deployment-Kategorien

- **Edge** — lokales Deployment ohne Cloud-Anbindung. Consumer-GPUs (z.B. RTX 4090, 24 GB)
  eignen sich für Modelle bis ~13B; kompakte Edge-Server wie NVIDIA DGX Spark (128 GB) können
  Modelle bis ~70B lokal betreiben.
- **Cloud** — dedizierte GPU-Server-Infrastruktur (z.B. H100/H200); typischerweise ab 13B.
- **Cloud (Multi-GPU/Node)** — mehrere GPUs oder Server; typischerweise ab ~70B (dense).

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

## Souveränitäts-Empfehlung

Für Anwendungen mit DSGVO, EU AI Act oder langfristiger Planungssicherheit:

1. **Soofi / 8ra** — maximale Souveränität, vollständig auditierbar, europäische Governance
2. **Mistral AI** — europäisch, stabile Apache-2.0-Lizenz, DSGVO-nah
3. **Microsoft Phi / Meta Llama** — US-rechtliche Abhängigkeit, aber etablierte Ökosysteme
4. **Alibaba Qwen / DeepSeek** — technisch stark, aber geopolitische Abhängigkeit und
   Lizenz-Instabilitätsrisiko; für sensitive Anwendungen nicht empfohlen
