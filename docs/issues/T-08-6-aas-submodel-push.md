# Task

- user story: [US-08](US-08-training-pipeline.md)
- depends on: [T-08-1](T-08-1-training-gateway.md), [T-08-3](T-08-3-agent-training-flow.md), [T-10-3](T-10-3-aas-submodels.md), [T-08-7](T-08-7-aas-base-model-nameplates.md)

/label ~UserStory_US-08
/label ~Task
/label ~ToDo

# Description

**AAS-Teilmodell-Push nach Trainingsabschluss**

Sobald ein Trainingsauftrag erfolgreich abgeschlossen ist, soll das Training Gateway die
Metadaten des trainierten Modells automatisch als **AI-Model-Nameplate-Teilmodell** (IDTA 02060)
in die Verwaltungsschalenumgebung pushen (Eclipse BaSyx AAS Environment).

Der Push erfolgt über ein einzelnes **MCP-Werkzeug** (`push_aas_submodel`), das intern
einen HTTP-POST auf den konfigurierbaren AAS-REST-Endpunkt absetzt.

## Architektur

```
Training Gateway
  ├── MCP Tool: push_aas_submodel(job_id)
  │     └── POST /submodels  →  Eclipse BaSyx AAS Environment
  │           Body: IDTA-02058-konformes AI-Model-Nameplate-Teilmodell (JSON)
  └── Webhook-Handler (job complete)
        └── ruft push_aas_submodel intern auf
```

Der MCP-Aufruf kann sowohl automatisch nach Job-Abschluss als auch manuell durch den
Interaction Agent ausgelöst werden.

## MCP-Werkzeug: `push_aas_submodel`

```python
@mcp.tool()
async def push_aas_submodel(job_id: str) -> dict:
    """
    Generiert ein AI-Model-Nameplate-Teilmodell (IDTA 02060) aus den Metadaten
    des abgeschlossenen Trainingsauftrags und pusht es in den AAS-Server.
    Gibt die Teilmodell-ID und die AAS-Server-URL zurück.
    """
```

**Eingabe:** `job_id` — ID des abgeschlossenen Trainingsauftrags  
**Ausgabe:** `{ "submodel_id": "...", "aas_url": "...", "status": "published" }`

## Teilmodell-Struktur (AI Model Nameplate, IDTA 02060)

Das Teilmodell folgt der offiziellen IDTA-02060-Spezifikation
(`IDTA 02060-1-0-1_Template_AIModelNameplate_forAASMetamodelV3.1.json`).
Serialisierung als JSON nach AAS-Metamodell Version 3.1.

Für die Dataset-Referenzierung ist folgende Struktur aus der Spec maßgeblich:
Pro verwendetem Datensatz wird eine eigene `AIDataset`-SMC eingefügt (Kardinalität `ZeroToMany`).

```json
{
  "modelType": "Submodel",
  "id": "https://dfki.de/ids/asset/<XXXX_XXXX_XXXX_XXXX>",
  "idShort": "AIModel_<job_id>",
  "kind": "Instance",
  "semanticId": {
    "type": "ExternalReference",
    "keys": [{ "type": "GlobalReference", "value": "https://admin-shell.io/idta/SubmodelTemplate/AIModelNameplate/1/0" }]
  },
  "submodelElements": [
    {
      "idShort": "URIOfTheProduct",
      "modelType": "Property", "valueType": "xs:string",
      "comment": "Standardfeld — URI des trainierten Modells (z.B. MinIO-URL oder HF-Repo-ID)"
    },
    {
      "idShort": "Version",
      "modelType": "Property", "valueType": "xs:string",
      "comment": "Standardfeld — Modellversion"
    },
    {
      "idShort": "Storage",
      "modelType": "Property", "valueType": "xs:string",
      "comment": "Standardfeld — MinIO-Pfad des Modell-Uploads"
    },
    {
      "idShort": "KindOfLearning",
      "modelType": "MultiLanguageProperty",
      "comment": "Standardfeld — Lernmethode (z.B. 'LoRA fine-tuning', 'QLoRA fine-tuning')"
    },
    {
      "idShort": "TrainingResults",
      "modelType": "SubmodelElementCollection",
      "comment": "Standardfeld",
      "value": [
        {
          "idShort": "ExampleResult",
          "modelType": "Property", "valueType": "xs:string",
          "comment": "Standardfeld — wird mit finalem Loss befüllt (z.B. 'Final loss: 0.42')"
        }
      ]
    },
    {
      "idShort": "Details",
      "modelType": "SubmodelElementCollection",
      "comment": "Standardfeld",
      "value": [
        {
          "idShort": "AIFramework",
          "modelType": "Property", "valueType": "xs:string",
          "comment": "Standardfeld — z.B. 'Hugging Face / PEFT'"
        }
      ]
    },
    {
      "idShort": "AITypeSpecificInformation",
      "modelType": "SubmodelElementCollection",
      "comment": "Standardfeld",
      "value": [
        {
          "idShort": "TransferLearning",
          "modelType": "SubmodelElementCollection",
          "comment": "Standardfeld — Basismodell-Informationen",
          "value": [
            {
              "idShort": "Name",
              "modelType": "Property", "valueType": "xs:string",
              "comment": "Standardfeld — Basismodell-ID (z.B. 'mistralai/Mistral-7B-v0.1')"
            }
          ]
        },
        {
          "idShort": "Hyperparameter",
          "modelType": "SubmodelElementCollection",
          "comment": "Standardfeld — konkrete Sub-Properties werden als Custom-Elemente ergänzt",
          "value": [
            { "idShort": "Epochs",       "modelType": "Property", "valueType": "xs:int" },
            { "idShort": "LearningRate", "modelType": "Property", "valueType": "xs:float" },
            { "idShort": "BatchSize",    "modelType": "Property", "valueType": "xs:int" }
          ]
        }
      ]
    },
    {
      "idShort": "AIDataset",
      "modelType": "SubmodelElementCollection",
      "comment": "Standardfeld — einmal pro verwendetem Datensatz (Kardinalität ZeroToMany)",
      "semanticId": {
        "type": "ExternalReference",
        "keys": [{ "type": "GlobalReference", "value": "https://admin-shell.io/idta/AIModelNameplate/AIDataset/1/0" }]
      },
      "value": [
        {
          "idShort": "AIDatasetReference",
          "modelType": "ReferenceElement",
          "category": "CONSTANT",
          "semanticId": {
            "type": "ExternalReference",
            "keys": [{ "type": "GlobalReference", "value": "https://admin-shell.io/idta/AIModelNameplate/AIDataset/DatasetReference/1/0" }]
          },
          "value": {
            "type": "ExternalReference",
            "keys": [{ "type": "Submodel", "value": "https://dfki.de/ids/asset/<dataset-submodel-id>" }]
          }
        },
        {
          "idShort": "TimeStamp",
          "modelType": "Range", "valueType": "xs:dateTime",
          "semanticId": {
            "type": "ExternalReference",
            "keys": [{ "type": "GlobalReference", "value": "https://admin-shell.io/idta/AIModelNameplate/AIDataset/TimeStamp/1/0" }]
          }
        }
      ]
    }
  ]
}
```

Pro verwendetem Dataset wird ein separates `AIDataset`-SMC-Element in `submodelElements`
eingefügt. Gibt es mehrere Datensätze, werden sie mit eindeutigem `idShort` durchnummeriert
(z.B. `AIDataset`, `AIDataset1`, `AIDataset2`).

## Befüllung aus Trainingsmetadaten

| Teilmodell-Feld | Spec? | Quelle (Training Gateway) |
|----------------|-------|--------------------------|
| `URIOfTheProduct` | ✅ Standard | MinIO-URL oder HF-Repo-ID des Modells |
| `Version` | ✅ Standard | `1.0.0` (initial) |
| `Storage` | ✅ Standard | MinIO-Pfad des Modell-Uploads |
| `KindOfLearning` | ✅ Standard | Methode aus Job-Parametern (z.B. `LoRA fine-tuning`) |
| `TrainingResults/ExampleResult` | ✅ Standard | Finaler Loss als String (z.B. `Final loss: 0.42`) |
| `Details/AIFramework` | ✅ Standard | `Hugging Face / PEFT` (statisch) |
| `AITypeSpecificInformation/TransferLearning/Name` | ✅ Standard | Basismodell-ID (z.B. `mistralai/Mistral-7B-v0.1`) |
| `AITypeSpecificInformation/Hyperparameter/Epochs` | ⚙️ Custom | Epochs aus Job-Konfiguration |
| `AITypeSpecificInformation/Hyperparameter/LearningRate` | ⚙️ Custom | Learning Rate aus Job-Konfiguration |
| `AITypeSpecificInformation/Hyperparameter/BatchSize` | ⚙️ Custom | Batch Size aus Job-Konfiguration |
| `AIDataset[n]/AIDatasetReference` | ✅ Standard | Teilmodell-ID des AI-Dataset-Teilmodells aus dem `AIDatasetCatalogue` |
| `AIDataset[n]/TimeStamp` | ✅ Standard | Startzeitpunkt des Trainingsauftrags |

## Konfiguration

Neue Umgebungsvariablen in `.env`:

```env
# Bereits in .env vorhanden — keine neuen Variablen nötig:
AAS_HOSTNAME=${LANDING_PAGE_HOSTNAME}   # Host der AAS-Umgebung
AAS_ENVIRONMENT_PORT=8289               # Port des Eclipse BaSyx AAS Environment

# Neu:
AAS_ID=https://dfki.de/ids/aas/9849_9446_1501_2526    # ID der Ziel-AAS (AIModelCatalogue)
AAS_PUSH_ON_COMPLETION=true                            # Automatischer Push nach Job-Abschluss
```

Die AAS-Server-URL wird im Training Gateway aus den bestehenden Variablen zusammengesetzt:
`http://${AAS_HOSTNAME}:${AAS_ENVIRONMENT_PORT}` — keine neue `AAS_SERVER_URL` erforderlich.

`AAS_ID` entspricht der ID der `AIModelCatalogue`-Verwaltungsschale, in die das Teilmodell
eingehängt wird. Der Wert ist statisch und entspricht dem Eintrag in `compose/aas/aasx/AIModelCatalogue.aasx`.

Der Push wird nur ausgeführt, wenn `AAS_HOSTNAME` gesetzt ist — kein Pflichtfeld,
damit Deployments ohne AAS-Umgebung weiterhin funktionieren.

## HTTP-Ablauf

Der Push erfolgt in zwei Schritten:

```
# 1. Teilmodell anlegen
POST http://{AAS_HOSTNAME}:{AAS_ENVIRONMENT_PORT}/submodels
Content-Type: application/json
Body: <IDTA-02060-Teilmodell als JSON>
→ Response 201 Created: { "id": "https://dfki.de/ids/asset/XXXX_XXXX_XXXX_XXXX", ... }

# 2. Teilmodell mit der Ziel-AAS verknüpfen (Base64URL-kodierte AAS-ID)
POST http://{AAS_HOSTNAME}:{AAS_ENVIRONMENT_PORT}/shells/{base64url(AAS_ID)}/submodel-refs
Content-Type: application/json
Body: { "type": "ExternalReference", "keys": [{ "type": "Submodel", "value": "<submodel-id>" }] }
→ Response 201 Created
```

Fehlerbehandlung: bei HTTP-Fehler wird der Fehlerstatus im Job gespeichert
(`aas_push_error`), der Trainingsjob selbst bleibt `completed`.

## Acceptance Criteria

- [ ] MCP-Werkzeug `push_aas_submodel(job_id)` im Training Gateway implementiert
- [ ] Werkzeug generiert IDTA-02060-konformes AI-Model-Nameplate-Teilmodell aus Job-Metadaten
- [ ] Teilmodell wird per `POST /submodels` angelegt und anschließend per `POST /shells/{id}/submodel-refs` mit der konfigurierten Ziel-AAS (`AAS_ID`) verknüpft
- [ ] Automatischer Push wird nach Job-Abschluss ausgelöst, wenn `AAS_PUSH_ON_COMPLETION=true`
- [ ] Push ist optional — fehlendes `AAS_SERVER_URL` deaktiviert den Push ohne Fehler
- [ ] Verwendete Datasets werden als `ReferenceElement`-Liste (`TrainingDatasets`) referenziert, die auf die jeweiligen AI-Dataset-Teilmodell-IDs im `AIDatasetCatalogue` zeigen
- [ ] Teilmodell-ID und AAS-URL werden im Job-Status gespeichert
- [ ] HTTP-Fehler beim Push werden geloggt und im Job als `aas_push_error` vermerkt
- [ ] Interaction Agent kann `push_aas_submodel` manuell aufrufen
- [ ] Konfiguration dokumentiert in `.env` (mit Kommentar)

# Branches

- feature/T-08-6-aas-submodel-push
