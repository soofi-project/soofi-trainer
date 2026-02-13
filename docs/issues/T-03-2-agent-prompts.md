# Task

- user story: [US-03](US-03-agent-architecture.md)

/label ~UserStory_US-03
/label ~Task
/label ~ToDo
/milestone %Sprint1

# Description

**Agent Prompts & Starter Prompts**

Create the prompts that define the agent's behavior and the starter prompts for Open WebUI. The agent communicates in German, so the actual prompts are in German while the documentation here is in English.

## System Prompt

The agent is called **Soofi** — a friendly and competent advisor for LLM training. The system prompt defines:

- **Role**: Expert advisor for LLM specialization methods
- **Task**: Understand the user's goal, conduct a structured interview, apply decision logic, and generate a recommendation report
- **Communication style**: Friendly but professional, explains technical terms, gives concrete examples, shows pros and cons
- **Source citations**: When using knowledge from the knowledge base, cite the source transparently

## Structured Interview

The agent conducts a structured interview to gather all relevant information:

### 1. Application Context
- Domain (e.g. medicine, law, finance, code, scientific texts)
- Specific task (e.g. Q&A, summarization, classification, NER, text generation)
- Working language

### 2. Data Situation
- Does the user have own training data?
  - Type, amount, format, quality, license
- Is the data labeled (input-output pairs) or unlabeled?
- Should the agent search for public datasets on HuggingFace?

### 3. Quality Goals
- Important metrics (Accuracy, F1, BLEU, ROUGE, Perplexity)
- Minimum acceptable performance

### 4. Technical Requirements
- Preferred base model (e.g. LLaMA, Mistral, Falcon, Phi) or no preference
- Model size preference (e.g. 7B, 13B, 70B) or "as needed"
- Available hardware (GPU type, VRAM)
- Deployment target (Cloud, On-Premise, Edge)

### 5. Constraints
- Budget for compute costs
- Project timeline
- Compliance requirements (GDPR, HIPAA, etc.)

## Source Citations

The agent transparently shows where its knowledge comes from:
- Inline quotes from the knowledge base with source reference
- List of sources at the end when multiple are used
- This increases credibility and demonstrates that RAG is working

## Starter Prompts

Conversation starter prompts displayed in Open WebUI as quick-start options:

### Use Case Discovery
- "Ich möchte einen Chatbot für meinen Kundenservice erstellen. Was empfiehlst du?"
- "Wir haben eine große Dokumentensammlung und wollen diese durchsuchbar machen."
- "Ich will ein Modell trainieren, das in unserem Firmenstil schreibt."

### Comparison Questions
- "Was ist der Unterschied zwischen RAG und Fine-Tuning?"
- "Wann sollte ich RAG verwenden und wann Fine-Tuning?"

### Specific Scenarios
- "Ich habe 500 FAQ-Paare. Soll ich RAG oder Fine-Tuning nutzen?"
- "Meine Wissensbasis ändert sich täglich. Welcher Ansatz ist besser?"

### Technical Questions
- "Wie viele Trainingsdaten brauche ich für Fine-Tuning?"
- "Was kostet Fine-Tuning im Vergleich zu RAG?"

Starter prompts are configured in Open WebUI via Admin Settings or a configuration file.

## Acceptance Criteria

- [ ] System prompt defines agent personality and behavior
- [ ] Structured interview questions cover all five areas
- [ ] Agent cites knowledge base sources transparently
- [ ] Prompts are in German and understandable
- [ ] Communication style is friendly and professional
- [ ] At least 4 starter prompts defined (one per category)
- [ ] Starter prompts are configured in Open WebUI

# Branches

- feature/US-03-agent-architecture
