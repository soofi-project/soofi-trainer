"""A2UI surface definitions for demo responses."""

GREETING: list[dict] = [
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
                            "children": {"explicitList": ["welcome-title", "welcome-text"]}
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


def _method_card(method_id: str, title: str, description: str, primary: bool = False) -> list:
    """Generate components for a single method card."""
    return [
        {
            "id": f"{method_id}-card",
            "component": {"Card": {"child": f"{method_id}-content"}},
        },
        {
            "id": f"{method_id}-content",
            "component": {
                "Column": {
                    "children": {
                        "explicitList": [
                            f"{method_id}-title",
                            f"{method_id}-desc",
                            f"{method_id}-btn",
                        ]
                    }
                }
            },
        },
        {
            "id": f"{method_id}-title",
            "component": {
                "Text": {"text": {"literalString": title}, "usageHint": "h3"}
            },
        },
        {
            "id": f"{method_id}-desc",
            "component": {
                "Text": {"text": {"literalString": description}, "usageHint": "body"}
            },
        },
        {
            "id": f"{method_id}-btn",
            "component": {
                "Button": {
                    "child": f"{method_id}-btn-text",
                    **({"primary": True} if primary else {}),
                    "action": {"name": "select_method", "args": {"method": method_id}},
                }
            },
        },
        {
            "id": f"{method_id}-btn-text",
            "component": {
                "Text": {
                    "text": {"literalString": f"{title.split(' ')[0]} auswählen"},
                    "usageHint": "body",
                }
            },
        },
    ]


METHODS: list[dict] = [
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
                *_method_card(
                    "rag",
                    "RAG (Retrieval-Augmented Generation)",
                    "Ideal für wissensbasierte Anwendungen. "
                    "Kombiniert Ihr Domänenwissen mit einem LLM — ohne Training nötig.",
                    primary=True,
                ),
                *_method_card(
                    "lora",
                    "LoRA (Low-Rank Adaptation)",
                    "Effizientes Fine-Tuning mit wenig Ressourcen. "
                    "Gut geeignet für spezialisierte Aufgaben.",
                ),
                *_method_card(
                    "qlora",
                    "QLoRA (Quantized LoRA)",
                    "Wie LoRA, aber mit Quantisierung — "
                    "läuft auf Consumer-Hardware (z.B. einer einzelnen GPU).",
                ),
            ],
        }
    },
    {"beginRendering": {"surfaceId": "main", "root": "root"}},
]

CONFIRMATION: list[dict] = [
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
                            "children": {"explicitList": ["confirm-title", "confirm-text"]}
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
