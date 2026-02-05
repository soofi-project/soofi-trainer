# Task

- user story: #US-03

/label ~UserStory_US-03
/label ~Task
/label ~ToDo
/milestone %Sprint1

# Description

**Define Starter Prompts**

Create conversation starter prompts that help users understand what they can ask the system. These will be displayed in Open WebUI as quick-start options.

## Starter Prompts (German)

### Use Case Discovery
- "Ich möchte einen Chatbot für meinen Kundenservice erstellen. Was empfiehlst du?"
- "Wir haben eine große Dokumentensammlung und wollen diese durchsuchbar machen."
- "Ich will ein Modell trainieren, das in unserem Firmenstil schreibt."

### Comparison Questions
- "Was ist der Unterschied zwischen RAG und Fine-Tuning?"
- "Wann sollte ich RAG verwenden und wann Fine-Tuning?"
- "Welche Vor- und Nachteile hat Fine-Tuning gegenüber RAG?"

### Specific Scenarios
- "Ich habe 500 FAQ-Paare. Soll ich RAG oder Fine-Tuning nutzen?"
- "Meine Wissensbasis ändert sich täglich. Welcher Ansatz ist besser?"
- "Ich brauche sehr schnelle Antwortzeiten. Was empfiehlst du?"

### Technical Questions
- "Wie viele Trainingsdaten brauche ich für Fine-Tuning?"
- "Welche Embedding-Modelle eignen sich für deutsche Texte?"
- "Was kostet Fine-Tuning im Vergleich zu RAG?"

## Open WebUI Integration

Starter prompts can be configured in Open WebUI:
1. Admin Settings → Interface → Default Prompt Suggestions
2. Or via environment variable / config file

## File to Create

Create `config/starter_prompts.json`:

```json
{
  "prompts": [
    {
      "title": "Chatbot erstellen",
      "content": "Ich möchte einen Chatbot für meinen Kundenservice erstellen. Was empfiehlst du?"
    },
    {
      "title": "RAG vs Fine-Tuning",
      "content": "Was ist der Unterschied zwischen RAG und Fine-Tuning?"
    },
    {
      "title": "FAQ-Daten nutzen",
      "content": "Ich habe 500 FAQ-Paare. Soll ich RAG oder Fine-Tuning nutzen?"
    },
    {
      "title": "Schnelle Antworten",
      "content": "Ich brauche sehr schnelle Antwortzeiten. Was empfiehlst du?"
    }
  ]
}
```

# Branches

- feature/US-03-agent-architecture
