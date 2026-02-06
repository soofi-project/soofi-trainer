# Task

- user story: #US-03

/label ~UserStory_US-03
/label ~Task
/label ~ToDo
/milestone %Sprint1

# Description

**Define Starter Prompts**

Create conversation starter prompts that help users understand what they can ask the system. These are displayed in Open WebUI as quick-start options.

## Prompt Categories (German)

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

Starter prompts are configured in Open WebUI via Admin Settings or a configuration file.

## Acceptance Criteria

- [ ] At least 4 starter prompts defined (one per category)
- [ ] Prompts are in German
- [ ] Prompts are configured in Open WebUI
- [ ] Each prompt triggers a meaningful agent response

# Branches

- feature/US-03-agent-architecture
