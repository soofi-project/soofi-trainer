# Soofi Trainer

Ein agentisches System, das Benutzer durch den LLM-Training-Prozess führt.

## Features

- **Interaktive Beratung**: Der Agent analysiert deinen Anwendungsfall und empfiehlt den besten Ansatz
- **RAG vs. Fine-Tuning**: Intelligente Empfehlung basierend auf deinen Anforderungen
- **Training Pipeline**: Orchestrierung des gesamten Training-Prozesses (gemockt)
- **Zwei Phasen**:
  - Phase 1 (Prototyping): n8n für schnelle Iteration
  - Phase 2 (Production): LangGraph State-Machine

## Architektur

```
┌─────────────────┐     ┌─────────────────┐     ┌──────────────┐
│   Open WebUI    │────▶│  n8n / Agent    │────▶│  MCP Tools   │
│  (Chat UI)      │     │  (Orchestrator) │     │  (Pipeline)  │
└─────────────────┘     └─────────────────┘     └──────────────┘
                                                       │
                                                ┌──────────────┐
                                                │ MCP Inspector│
                                                │  (Debugging) │
                                                └──────────────┘
```

## Quick Start

### Voraussetzungen

- Docker und Docker Compose
- OpenAI API Key

### Installation

1. Repository klonen:
   ```bash
   git clone https://mrk40.dfki.de/soofi/soofi-trainer.git
   cd soofi-trainer
   ```

2. Environment-Datei erstellen:
   ```bash
   cp .env.example .env
   # Editiere .env und füge deinen OPENAI_API_KEY ein
   ```

3. Stack starten:
   ```bash
   ./up.sh
   ```

4. Services aufrufen:
   - **Open WebUI**: http://localhost:3000
   - **n8n**: http://localhost:5678
   - **MCP Server**: http://localhost:8000
   - **MCP Inspector**: http://localhost:5173
   - **Agent API**: http://localhost:8001

### Stack stoppen

```bash
./down.sh
```

Mit Daten löschen:
```bash
./down.sh --clean
```

## Komponenten

### MCP Server (Port 8000)

Stellt die Training-Pipeline Tools bereit:

| Tool | Beschreibung |
|------|-------------|
| `check_dataset_availability` | HuggingFace Datasets prüfen |
| `analyze_use_case` | Anwendungsfall analysieren |
| `recommend_approach` | RAG vs. Fine-Tuning empfehlen |
| `configure_training` | Training-Parameter konfigurieren |
| `start_training_pipeline` | Pipeline starten |
| `get_training_status` | Status abfragen |

### n8n (Port 5678)

Workflow-Automation für Prototyping:
- Webhook-basierte Integration
- Visuelle Flow-Erstellung
- Einfache MCP-Tool-Aufrufe

### LangGraph Agent (Port 8001)

State-Machine basierter Agent für Production:

```
GREETING → ANALYSIS → RECOMMENDATION → CONFIGURATION → EXECUTION → MONITORING → COMPLETED
```

### Open WebUI (Port 3000)

Chat-Interface für Benutzerinteraktion.

## API Beispiele

### Chat mit dem Agent

```bash
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Ich möchte einen Chatbot für Kundenservice erstellen",
    "session_id": "user123"
  }'
```

### MCP Tool aufrufen

```bash
curl -X POST http://localhost:8000/tools/analyze_use_case \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "Ich möchte einen Chatbot für technischen Support",
    "session_id": "test"
  }'
```

## Entwicklung

### Projektstruktur

```
soofi-trainer/
├── agent/                 # LangGraph Agent (Phase 2)
│   ├── graph.py          # State-Machine Definition
│   ├── prompts.py        # Agent Prompts
│   ├── state.py          # State Definitionen
│   ├── tools.py          # LangChain Tools
│   └── server.py         # FastAPI Server
├── mcp-server/           # MCP Tools Server
│   └── main.py           # FastAPI + Tools
├── n8n/                  # n8n Workflows (Phase 1)
│   └── workflows/        # Workflow JSON Dateien
├── docker-compose.yml    # Service Orchestration
├── up.sh                 # Stack starten
├── down.sh               # Stack stoppen
└── .env.example          # Environment Template
```

## Lizenz

MIT License - siehe [LICENSE](LICENSE)
