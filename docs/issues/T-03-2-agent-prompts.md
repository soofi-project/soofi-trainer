# Task

- user story: #US-03

/label ~UserStory_US-03
/label ~Task
/label ~ToDo
/milestone %Sprint1

# Description

**Develop Agent Prompts**

Create the prompts that define the agent's behavior. The agent communicates in German, so the actual prompts are in German while the documentation here is in English.

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

### 4. Constraints
- Budget for compute costs
- Project timeline
- Compliance requirements (GDPR, HIPAA, etc.)
- Available hardware (GPU type, VRAM)

## Source Citations

The agent transparently shows where its knowledge comes from:
- Inline quotes from the knowledge base with source reference
- List of sources at the end when multiple are used
- This increases credibility and demonstrates that RAG is working

## Acceptance Criteria

- [ ] System prompt defines agent personality and behavior
- [ ] Structured interview questions cover all four areas
- [ ] Agent cites knowledge base sources transparently
- [ ] Prompts are in German and understandable
- [ ] Communication style is friendly and professional

# Branches

- feature/US-03-agent-architecture
