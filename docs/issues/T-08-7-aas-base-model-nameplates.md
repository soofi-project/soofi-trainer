# Task

- user story: [US-08](US-08-training-pipeline.md)
- depends on: [T-10-3](T-10-3-aas-submodels.md)
- required by: [T-08-6](T-08-6-aas-submodel-push.md)

/label ~UserStory_US-08
/label ~Task
/label ~ToDo

# Description

**AAS-Nameplates für Basismodelle (statischer Content)**

Damit trainierte Modelle in ihrem AI-Model-Nameplate-Teilmodell ([T-08-6](T-08-6-aas-submodel-push.md))
per `TransferLearning/AIModelNameplate` auf das Nameplate des Basismodells verweisen können,
müssen die unterstützten Basismodelle als AI-Model-Nameplate-Teilmodelle (IDTA 02060) in der
Eclipse BaSyx AAS-Umgebung vorhanden sein.

Diese Teilmodelle sind **statischer Content** — sie werden nicht zur Laufzeit generiert, sondern
einmalig als JSON-Dateien erstellt und beim Start der AAS-Umgebung geladen.

## Umfang

Nameplate-Teilmodelle für alle Basismodelle, die Soofi als Fine-Tuning-Ausgangspunkt unterstützt.
Eine ausführliche Beschreibung der Modelle (Anwendungsfälle, Edge/Cloud-Eignung) ist in der
Knowledge-Base unter `knowledge/models/base_models.md` hinterlegt.

### Edge (≤ 8B)

| Modell | HuggingFace-ID | Größe |
|--------|---------------|-------|
| Qwen2.5 0.5B Instruct | `Qwen/Qwen2.5-0.5B-Instruct` | 0.5B |
| Qwen2.5 1.5B Instruct | `Qwen/Qwen2.5-1.5B-Instruct` | 1.5B |
| Qwen2.5 3B Instruct | `Qwen/Qwen2.5-3B-Instruct` | 3B |
| Qwen2.5 7B Instruct | `Qwen/Qwen2.5-7B-Instruct` | 7B |
| Qwen3 0.6B | `Qwen/Qwen3-0.6B` | 0.6B |
| Qwen3 1.7B | `Qwen/Qwen3-1.7B` | 1.7B |
| Qwen3 4B | `Qwen/Qwen3-4B` | 4B |
| Qwen3 8B | `Qwen/Qwen3-8B` | 8B |
| Llama 3.2 1B Instruct | `meta-llama/Llama-3.2-1B-Instruct` | 1B |
| Llama 3.2 3B Instruct | `meta-llama/Llama-3.2-3B-Instruct` | 3B |
| Llama 3.1 8B Instruct | `meta-llama/Llama-3.1-8B-Instruct` | 8B |
| Mistral 7B Instruct v0.3 | `mistralai/Mistral-7B-Instruct-v0.3` | 7B |
| Phi-4-mini Instruct | `microsoft/Phi-4-mini-instruct` | 3.8B |
| Gemma 3 1B | `google/gemma-3-1b-it` | 1B |
| Gemma 3 4B | `google/gemma-3-4b-it` | 4B |
| Nemotron Mini 4B Instruct | `nvidia/Nemotron-Mini-4B-Instruct` | 4B |
| DeepSeek-R1-Distill-Qwen 1.5B | `deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B` | 1.5B |
| DeepSeek-R1-Distill-Qwen 7B | `deepseek-ai/DeepSeek-R1-Distill-Qwen-7B` | 7B |

### Cloud (> 8B)

| Modell | HuggingFace-ID | Größe |
|--------|---------------|-------|
| Qwen2.5 14B Instruct | `Qwen/Qwen2.5-14B-Instruct` | 14B |
| Qwen2.5 32B Instruct | `Qwen/Qwen2.5-32B-Instruct` | 32B |
| Qwen2.5 72B Instruct | `Qwen/Qwen2.5-72B-Instruct` | 72B |
| Qwen3 14B | `Qwen/Qwen3-14B` | 14B |
| Qwen3 32B | `Qwen/Qwen3-32B` | 32B |
| Qwen3 30B-A3B (MoE) | `Qwen/Qwen3-30B-A3B` | 30B |
| Qwen3.5 27B | `Qwen/Qwen3.5-27B` | 27B |
| Qwen3.5 35B-A3B (MoE) | `Qwen/Qwen3.5-35B-A3B` | 35B |
| Llama 3.1 70B Instruct | `meta-llama/Llama-3.1-70B-Instruct` | 70B |
| Llama 3.3 70B Instruct | `meta-llama/Llama-3.3-70B-Instruct` | 70B |
| Mistral Nemo 12B Instruct | `mistralai/Mistral-Nemo-Instruct-2407` | 12B |
| Mistral Small 3 24B Instruct | `mistralai/Mistral-Small-24B-Instruct-2501` | 24B |
| Mixtral 8x22B Instruct (MoE) | `mistralai/Mixtral-8x22B-Instruct-v0.1` | 141B |
| Phi-4 14B Instruct | `microsoft/phi-4` | 14B |
| Gemma 2 9B Instruct | `google/gemma-2-9b-it` | 9B |
| Gemma 3 12B Instruct | `google/gemma-3-12b-it` | 12B |
| Gemma 3 27B Instruct | `google/gemma-3-27b-it` | 27B |
| Llama 3.3 Nemotron Super 49B | `nvidia/Llama-3_3-Nemotron-Super-49B-v1_5` | 49B |
| Llama 3.1 Nemotron 70B Instruct | `nvidia/Llama-3.1-Nemotron-70B-Instruct-HF` | 70B |
| DeepSeek-R1-Distill-Qwen 14B | `deepseek-ai/DeepSeek-R1-Distill-Qwen-14B` | 14B |
| DeepSeek-R1-Distill-Qwen 32B | `deepseek-ai/DeepSeek-R1-Distill-Qwen-32B` | 32B |

### Cloud (Multi-GPU/Node, ≥ 100B)

| Modell | HuggingFace-ID | Gesamt | Aktiv |
|--------|---------------|--------|-------|
| Qwen3 235B-A22B (MoE) | `Qwen/Qwen3-235B-A22B` | 235B | 22B |
| Llama 3.1 405B Instruct | `meta-llama/Llama-3.1-405B-Instruct` | 405B | 405B |
| Llama 4 Scout (MoE) | `meta-llama/Llama-4-Scout-17B-16E-Instruct` | ~109B | 17B |
| Llama 4 Maverick (MoE) | `meta-llama/Llama-4-Maverick-17B-128E-Instruct` | ~880B | 17B |
| Nemotron-4 340B Instruct | `nvidia/Nemotron-4-340B-Instruct` | 340B | 340B |
| DeepSeek-V3 (MoE) | `deepseek-ai/DeepSeek-V3` | 671B | 37B |
| DeepSeek-R1 (MoE) | `deepseek-ai/DeepSeek-R1` | 671B | 37B |

Weitere Modelle können als JSON-Dateien nach demselben Schema ergänzt werden.

## Dateistruktur

```
compose/aas/
  aasx/
    AIModelCatalogue.aasx          # bestehend — wird manuell erweitert
  base-models/
    qwen3-4b.json                  # AI Model Nameplate Submodell (IDTA 02060, JSON)
    qwen3-8b.json
    llama-3-1-8b-instruct.json
    mistral-7b-instruct-v0-3.json
    ...                            # je eine Datei pro Basismodell

knowledge/
  models/
    base_models.md                 # Modellübersicht für RAG (Anwendungsfälle, Edge/Cloud)
    base_models-meta.yaml
```

Die JSON-Dateien enthalten jeweils **nur das Submodell** (kein vollständiges AAS-Environment).
Sie dienen als Vorlage — der Inhalt wird manuell in `AIModelCatalogue.aasx` eingefügt:

1. Submodell-JSON in das `submodels`-Array der AASX-Umgebung aufnehmen
2. `submodel-ref` mit der Submodell-ID in das `submodels`-Array der `AIModelCatalogue`-AAS-Shell eintragen

BaSyx lädt die erweiterte AASX beim Start und registriert die Verlinkung automatisch.

## Teilmodell-Befüllung

Pro Basismodell werden folgende Standardfelder aus IDTA 02060 befüllt:

| Feld | Inhalt |
|------|--------|
| `URIOfTheProduct` | HuggingFace-URL des Modells |
| `Version` | Modellversion (z.B. `v0.1`) |
| `KindOfLearning` | `Pretraining` |
| `Details/AIFramework` | `PyTorch / Hugging Face Transformers` |
| `Details/ProgramLanguage` | `Python` |

## Verknüpfung mit AIModelCatalogue

Jedes Nameplate-Teilmodell wird als `submodel-ref` in die bestehende
`AIModelCatalogue`-AAS (`AAS_ID`) eingehängt — analog zum dynamischen Push in T-08-6.

## Acceptance Criteria

- [ ] JSON-Dateien für alle unterstützten Basismodelle nach IDTA-02060-Schema erstellt
- [ ] Dateien unter `compose/aas/base-models/` abgelegt (je eine Datei pro Modell)
- [ ] Submodelle und `submodel-refs` manuell in `AIModelCatalogue.aasx` eingepflegt
- [ ] Jedes Teilmodell ist über seine `id` aus T-08-6 referenzierbar (`TransferLearning/AIModelNameplate`)
- [ ] Teilmodelle sind im BaSyx AAS Web UI unter `AIModelCatalogue` sichtbar
- [ ] Knowledge-Datei `knowledge/models/base_models.md` mit Anwendungsfällen und Edge/Cloud-Eignung aller Modelle erstellt und in RAG-Ingestion aufgenommen

# Branches

- feature/T-08-7-aas-base-model-nameplates
