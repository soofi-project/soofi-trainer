"""Mock AG-UI backend that streams hardcoded demo responses."""

import asyncio
import json
import os
import uuid
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

app = FastAPI(title="Soofi Interaction Agent (Mock)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# A2UI surface helpers
# ---------------------------------------------------------------------------

GREETING_SURFACE: list[dict] = [
    {
        "surfaceUpdate": {
            "surfaceId": "main",
            "components": [
                {
                    "id": "root",
                    "component": {"Column": {"children": {"explicitList": ["welcome-card"]}}},
                },
                {
                    "id": "welcome-card",
                    "component": {"Card": {"child": "welcome-content"}},
                },
                {
                    "id": "welcome-content",
                    "component": {
                        "Column": {
                            "children": {
                                "explicitList": ["welcome-title", "welcome-text"]
                            }
                        }
                    },
                },
                {
                    "id": "welcome-title",
                    "component": {
                        "Text": {
                            "text": {"literalString": "Willkommen beim Soofi Trainer"},
                            "usageHint": "h2",
                        }
                    },
                },
                {
                    "id": "welcome-text",
                    "component": {
                        "Text": {
                            "text": {
                                "literalString": (
                                    "Ich helfe Ihnen, die passende Methode zur "
                                    "LLM-Spezialisierung zu finden. Beschreiben Sie "
                                    "Ihren Anwendungsfall!"
                                )
                            },
                            "usageHint": "body",
                        }
                    },
                },
            ],
        }
    },
    {"beginRendering": {"surfaceId": "main", "root": "root"}},
]

METHOD_SURFACE: list[dict] = [
    {
        "surfaceUpdate": {
            "surfaceId": "main",
            "components": [
                {
                    "id": "root",
                    "component": {
                        "Column": {
                            "children": {
                                "explicitList": [
                                    "method-title",
                                    "rag-card",
                                    "lora-card",
                                    "qlora-card",
                                ]
                            }
                        }
                    },
                },
                {
                    "id": "method-title",
                    "component": {
                        "Text": {
                            "text": {"literalString": "Empfohlene Methoden"},
                            "usageHint": "h2",
                        }
                    },
                },
                # RAG Card
                {
                    "id": "rag-card",
                    "component": {"Card": {"child": "rag-content"}},
                },
                {
                    "id": "rag-content",
                    "component": {
                        "Column": {
                            "children": {
                                "explicitList": ["rag-title", "rag-desc", "rag-btn"]
                            }
                        }
                    },
                },
                {
                    "id": "rag-title",
                    "component": {
                        "Text": {
                            "text": {"literalString": "RAG (Retrieval-Augmented Generation)"},
                            "usageHint": "h3",
                        }
                    },
                },
                {
                    "id": "rag-desc",
                    "component": {
                        "Text": {
                            "text": {
                                "literalString": (
                                    "Ideal für wissensbasierte Anwendungen. "
                                    "Kombiniert Ihr Domänenwissen mit einem LLM — "
                                    "ohne Training nötig."
                                )
                            },
                            "usageHint": "body",
                        }
                    },
                },
                {
                    "id": "rag-btn",
                    "component": {
                        "Button": {
                            "child": "rag-btn-text",
                            "primary": True,
                            "action": {
                                "name": "select_method",
                                "context": [
                                    {
                                        "key": "method",
                                        "value": {"literalString": "rag"},
                                    }
                                ],
                            },
                        }
                    },
                },
                {
                    "id": "rag-btn-text",
                    "component": {
                        "Text": {"text": {"literalString": "RAG auswählen"}, "usageHint": "body"}
                    },
                },
                # LoRA Card
                {
                    "id": "lora-card",
                    "component": {"Card": {"child": "lora-content"}},
                },
                {
                    "id": "lora-content",
                    "component": {
                        "Column": {
                            "children": {
                                "explicitList": ["lora-title", "lora-desc", "lora-btn"]
                            }
                        }
                    },
                },
                {
                    "id": "lora-title",
                    "component": {
                        "Text": {
                            "text": {"literalString": "LoRA (Low-Rank Adaptation)"},
                            "usageHint": "h3",
                        }
                    },
                },
                {
                    "id": "lora-desc",
                    "component": {
                        "Text": {
                            "text": {
                                "literalString": (
                                    "Effizientes Fine-Tuning mit wenig Ressourcen. "
                                    "Gut geeignet für spezialisierte Aufgaben."
                                )
                            },
                            "usageHint": "body",
                        }
                    },
                },
                {
                    "id": "lora-btn",
                    "component": {
                        "Button": {
                            "child": "lora-btn-text",
                            "action": {
                                "name": "select_method",
                                "context": [
                                    {
                                        "key": "method",
                                        "value": {"literalString": "lora"},
                                    }
                                ],
                            },
                        }
                    },
                },
                {
                    "id": "lora-btn-text",
                    "component": {
                        "Text": {
                            "text": {"literalString": "LoRA auswählen"},
                            "usageHint": "body",
                        }
                    },
                },
                # QLoRA Card
                {
                    "id": "qlora-card",
                    "component": {"Card": {"child": "qlora-content"}},
                },
                {
                    "id": "qlora-content",
                    "component": {
                        "Column": {
                            "children": {
                                "explicitList": ["qlora-title", "qlora-desc", "qlora-btn"]
                            }
                        }
                    },
                },
                {
                    "id": "qlora-title",
                    "component": {
                        "Text": {
                            "text": {"literalString": "QLoRA (Quantized LoRA)"},
                            "usageHint": "h3",
                        }
                    },
                },
                {
                    "id": "qlora-desc",
                    "component": {
                        "Text": {
                            "text": {
                                "literalString": (
                                    "Wie LoRA, aber mit Quantisierung — "
                                    "läuft auf Consumer-Hardware (z.B. einer einzelnen GPU)."
                                )
                            },
                            "usageHint": "body",
                        }
                    },
                },
                {
                    "id": "qlora-btn",
                    "component": {
                        "Button": {
                            "child": "qlora-btn-text",
                            "action": {
                                "name": "select_method",
                                "context": [
                                    {
                                        "key": "method",
                                        "value": {"literalString": "qlora"},
                                    }
                                ],
                            },
                        }
                    },
                },
                {
                    "id": "qlora-btn-text",
                    "component": {
                        "Text": {
                            "text": {"literalString": "QLoRA auswählen"},
                            "usageHint": "body",
                        }
                    },
                },
            ],
        }
    },
    {"beginRendering": {"surfaceId": "main", "root": "root"}},
]

# ---------------------------------------------------------------------------
# Dashboard embed surfaces (MCP Inspector, N8N)
# ---------------------------------------------------------------------------


def _dashboard_surface(url: str, title: str, description: str) -> list[dict]:
    """Create an A2UI surface with a DashboardEmbed component (rendered as link card)."""
    return [
        {
            "surfaceUpdate": {
                "surfaceId": "main",
                "components": [
                    {
                        "id": "root",
                        "component": {
                            "Column": {"children": {"explicitList": ["dash-card"]}}
                        },
                    },
                    {
                        "id": "dash-card",
                        "component": {"Card": {"child": "dash-embed"}},
                    },
                    {
                        "id": "dash-embed",
                        "component": {
                            "DashboardEmbed": {
                                "url": url,
                                "title": title,
                                "description": description,
                            }
                        },
                    },
                ],
            }
        },
        {"beginRendering": {"surfaceId": "main", "root": "root"}},
    ]


CONFIRMATION_SURFACE: list[dict] = [
    {
        "surfaceUpdate": {
            "surfaceId": "main",
            "components": [
                {
                    "id": "root",
                    "component": {"Column": {"children": {"explicitList": ["confirm-card"]}}},
                },
                {
                    "id": "confirm-card",
                    "component": {"Card": {"child": "confirm-content"}},
                },
                {
                    "id": "confirm-content",
                    "component": {
                        "Column": {
                            "children": {
                                "explicitList": ["confirm-title", "confirm-text"]
                            }
                        }
                    },
                },
                {
                    "id": "confirm-title",
                    "component": {
                        "Text": {
                            "text": {"literalString": "Methode ausgewählt"},
                            "usageHint": "h2",
                        }
                    },
                },
                {
                    "id": "confirm-text",
                    "component": {
                        "Text": {
                            "text": {
                                "literalString": (
                                    "Ihre Auswahl wurde gespeichert. "
                                    "Im nächsten Schritt konfigurieren wir die Details."
                                )
                            },
                            "usageHint": "body",
                        }
                    },
                },
            ],
        }
    },
    {"beginRendering": {"surfaceId": "main", "root": "root"}},
]

# ---------------------------------------------------------------------------
# Demo response logic
# ---------------------------------------------------------------------------

GREETING_TEXT = (
    "Hallo! Ich bin der Soofi Trainer — Ihr Assistent für LLM-Spezialisierung. "
    "Beschreiben Sie mir Ihren Anwendungsfall und ich empfehle Ihnen "
    "die passende Methode.\n\n"
    "Sie können auch sagen:\n"
    '- "Zeig mir den MCP Inspector" — Semantic-Search-Tools\n'
    '- "Zeig mir N8N" — Workflow-Automation\n'
    '- "Welche Methoden gibt es?" — Methodenempfehlung'
)

METHOD_TEXT = (
    "Basierend auf Ihrer Beschreibung habe ich drei mögliche Methoden "
    "identifiziert. Jede hat unterschiedliche Stärken — wählen Sie die "
    "passendste für Ihren Anwendungsfall."
)

MCP_INSPECTOR_TEXT = (
    "Hier sehen Sie den MCP Inspector — unser Tool für semantische Suche. "
    "Darüber kommuniziert der Agent mit der Weaviate-Vektordatenbank, "
    "um relevantes Domänenwissen abzurufen."
)

N8N_TEXT = (
    "Hier sehen Sie N8N — unsere Workflow-Automation-Plattform. "
    "Damit orchestrieren wir Verarbeitungs-Pipelines und "
    "können komplexe Abläufe visuell modellieren."
)

# Direct URLs -- opened in new tab (iframe embedding blocked by X-Frame-Options).
# Constructed from environment variables set via .env / docker-compose.
_mcp_port = os.environ["MCPINSPECTOR_CLIENT_PORT"]
_mcp_token = os.environ["MCP_AUTH_TOKEN"]
MCP_INSPECTOR_URL = (
    f"http://localhost:{_mcp_port}"
    f"/?transport=streamable-http"
    f"&serverUrl=http://vector-mcp:8000/mcp/"
    f"&MCP_PROXY_AUTH_TOKEN={_mcp_token}"
)
N8N_URL = f"http://localhost:{os.environ['N8N_EXTERNAL_PORT']}"

MCP_INSPECTOR_DESC = (
    "Der MCP Inspector zeigt die verfügbaren Semantic-Search-Tools "
    "(search_documents, list_metadata) und ermöglicht Testaufrufe "
    "gegen die Weaviate-Vektordatenbank."
)
N8N_DESC = (
    "N8N ist unsere visuelle Workflow-Automation-Plattform. "
    "Hier können Sie Verarbeitungs-Pipelines und "
    "Integrationen grafisch modellieren und ausführen."
)


def _choose_response(message: str) -> tuple[str, list[dict]]:
    """Pick a demo response based on simple keyword matching."""
    lower = message.lower()

    # --- Dashboard embeds (fuzzy matching) ---
    if any(kw in lower for kw in (
        "mcp inspector", "mcp inspektor", "inspector", "inspektor",
        "mcp tools", "mcp-inspector", "semantic search", "semantische suche",
        "vektordatenbank", "vektor", "weaviate", "suche zeigen",
    )):
        return MCP_INSPECTOR_TEXT, _dashboard_surface(
            MCP_INSPECTOR_URL, "MCP Inspector", MCP_INSPECTOR_DESC
        )
    if any(kw in lower for kw in (
        "n8n", "workflow", "workflows", "pipeline", "automation",
        "automatisierung", "orchestrierung", "ablauf", "ablaeufe",
    )):
        return N8N_TEXT, _dashboard_surface(N8N_URL, "N8N Workflows", N8N_DESC)

    # --- Method selection flow ---
    if any(kw in lower for kw in (
        "select_method", "auswählen", "wähle", "nehme", "das nehme",
        "diese methode", "starten", "konfigur",
    )):
        return (
            "Ausgezeichnete Wahl! Ich bereite die Konfiguration vor.",
            CONFIRMATION_SURFACE,
        )
    if any(kw in lower for kw in (
        "methode", "methoden", "rag", "lora", "fine-tun", "finetuning",
        "training", "empfehlung", "empfiehl", "vorschlag", "spezialisier",
        "anwendungsfall", "use case", "usecase",
    )):
        return METHOD_TEXT, METHOD_SURFACE

    return GREETING_TEXT, GREETING_SURFACE


# ---------------------------------------------------------------------------
# SSE streaming
# ---------------------------------------------------------------------------

STREAM_DELAY = 0.03  # seconds between text chunks


async def _stream_ag_ui_events(
    user_message: str,
) -> AsyncGenerator[str, None]:
    """Yield AG-UI SSE events as `data: {json}\n\n` lines."""
    thread_id = str(uuid.uuid4())
    run_id = str(uuid.uuid4())
    msg_id = str(uuid.uuid4())

    text, surface = _choose_response(user_message)

    # --- RUN_STARTED ---
    yield _sse({"type": "RUN_STARTED", "threadId": thread_id, "runId": run_id})

    # --- TEXT_MESSAGE streaming ---
    yield _sse({"type": "TEXT_MESSAGE_START", "messageId": msg_id, "role": "assistant"})

    # Stream text word-by-word for realistic effect
    words = text.split(" ")
    for i, word in enumerate(words):
        delta = word if i == len(words) - 1 else word + " "
        yield _sse({"type": "TEXT_MESSAGE_CONTENT", "messageId": msg_id, "delta": delta})
        await asyncio.sleep(STREAM_DELAY)

    yield _sse({"type": "TEXT_MESSAGE_END", "messageId": msg_id})

    # --- STATE_SNAPSHOT with A2UI surface ---
    yield _sse({"type": "STATE_SNAPSHOT", "snapshot": {"a2ui": surface}})

    # --- RUN_FINISHED ---
    yield _sse({"type": "RUN_FINISHED", "threadId": thread_id, "runId": run_id})


def _sse(event: dict) -> str:
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.post("/agent")
async def agent_endpoint(request: Request) -> StreamingResponse:
    body = await request.json()
    user_message = ""
    # Accept both {message: "..."} and {messages: [{content: "..."}]}
    if "message" in body:
        user_message = body["message"]
    elif "messages" in body and body["messages"]:
        last = body["messages"][-1]
        user_message = last.get("content", "") if isinstance(last, dict) else str(last)

    return StreamingResponse(
        _stream_ag_ui_events(user_message),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
