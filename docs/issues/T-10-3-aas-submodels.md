# Task

- user story: [US-10](US-10-demo-preparation.md)

/label ~UserStory_US-10
/label ~Task
/label ~ToDo

# Description

**AAS Submodels — Generierung von AI-Dataset-Teilmodellen**

Trainingsartefakte (Modell, Dataset, Hyperparameter, Metriken) sollen als
Asset Administration Shell (AAS) Teilmodelle exportierbar sein. Damit können trainierte
Modelle und ihre Datensätze im industrie-standardisierten Digital-Twin-Format
(IDTA / IEC 63278) dargestellt werden — relevant für Industrie-4.0-Publikum auf der
Hannover Messe.

## Hintergrund: AAS & AI-Dataset Submodel

Die Industrial Digital Twin Association (IDTA) definiert standardisierte Teilmodell-
Spezifikationen. Relevant für Soofi:

- **IDTA 02060 — AI Dataset** (Spezifikation für KI-Datensätze als AAS-Teilmodell)
- Enthält: Datensatzbeschreibung, Datenherkunft, Splits (Train/Val/Test), Lizenz,
  verwendete Modellarchitektur

Ein AAS-Teilmodell wird als JSON oder XML nach dem AAS-Metamodell (Basyx, AASX Package
Explorer) serialisiert.

## Scope

Für die Hannover-Messe-Demo reicht ein **statisches Beispiel-Teilmodell**, das zeigt,
wie ein durch Soofi trainiertes Modell im AAS-Format beschrieben wird. Eine vollautomatische
Live-Generierung aus dem Training Gateway ist als Erweiterung möglich, aber nicht
zwingend für T-10-3.

## Teilmodell-Struktur (AI Dataset, vereinfacht)

```json
{
  "modelType": "Submodel",
  "idShort": "AIDataset",
  "id": "urn:soofi:dataset:qc-classifier-v1",
  "semanticId": {
    "type": "ExternalReference",
    "keys": [{ "type": "GlobalReference", "value": "https://admin-shell.io/idta/AIDataset/1/0" }]
  },
  "submodelElements": [
    {
      "modelType": "Property",
      "idShort": "Name",
      "valueType": "xs:string",
      "value": "QS-Fehlerklassifikation Demo-Dataset"
    },
    {
      "modelType": "Property",
      "idShort": "Version",
      "valueType": "xs:string",
      "value": "1.0.0"
    },
    {
      "modelType": "Property",
      "idShort": "Task",
      "valueType": "xs:string",
      "value": "text-classification"
    },
    {
      "modelType": "Property",
      "idShort": "NumberOfSamples",
      "valueType": "xs:int",
      "value": "2000"
    },
    {
      "modelType": "Property",
      "idShort": "TrainingMethod",
      "valueType": "xs:string",
      "value": "LoRA fine-tuning"
    },
    {
      "modelType": "Property",
      "idShort": "BaseModel",
      "valueType": "xs:string",
      "value": "mistralai/Mistral-7B-v0.1"
    },
    {
      "modelType": "SubmodelElementCollection",
      "idShort": "DataSplits",
      "value": [
        { "modelType": "Property", "idShort": "Train", "valueType": "xs:float", "value": "0.8" },
        { "modelType": "Property", "idShort": "Validation", "valueType": "xs:float", "value": "0.1" },
        { "modelType": "Property", "idShort": "Test", "valueType": "xs:float", "value": "0.1" }
      ]
    }
  ]
}
```

## Deliverables

| Artefakt | Beschreibung |
|----------|-------------|
| `aas/ai-dataset-example.json` | Beispiel-Teilmodell für Demo-Dataset (Szenario B aus T-10-2) |
| `aas/ai-dataset-example.aasx` | Optional: AASX-Package für AASX Package Explorer |
| Dokumentation | Kurze Erklärung im Demo-Skript, wie das Teilmodell entstand |

## Mögliche Erweiterung (Post-Demo)

Integration in Training Gateway: Nach Abschluss eines Trainingsauftrags automatisch ein
AAS-Teilmodell generieren und in MinIO ablegen. Erfordert:
- IDTA 02060 Schema als Python-Datenklassen (z.B. via `basyx-python-sdk`)
- Neuer Endpoint `GET /jobs/{id}/aas` im Training Gateway
- Verlinkung aus der Soofi UI

## Acceptance Criteria

- [ ] Mindestens ein vollständiges AAS-Teilmodell (AI Dataset) für einen Demo-Use-Case erstellt
- [ ] Teilmodell validiert gegen IDTA 02060 Schema (oder manuell geprüft)
- [ ] Teilmodell im AASX Package Explorer darstellbar (optional aber empfohlen)
- [ ] Kurzbeschreibung für Demo-Präsentation verfasst (was zeigt das Teilmodell, warum ist das relevant)
- [ ] JSON-Datei im Repository unter `aas/` abgelegt

# Branches

- feature/T-10-3-aas-submodels
