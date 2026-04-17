# Soofi Trainer — Demo / User Script

This script walks through the Soofi Trainer end-to-end — from picking a use
case to launching the model training job. It also provides **side-question
blocks** that can be inserted at any point in the conversation (agent cards,
training overview, knowledge content).

All user lines are phrased so they can be spoken or typed directly into the
Soofi UI (`https://localhost/` or `http://localhost:3001`). Expected agent
reactions are shown in *italics*.

> **Language note:** The Soofi stack ships with German as the default. Switch
> the UI to English via the language toggle before running this script (the
> Interaction Agent loads `system_en.md` / `slot_extraction_en.md` accordingly).

---

## 0. Prerequisites

- Stack is up: `./up.sh` (default backend `chatgpt`, profile `local`).
- UI reachable at `https://localhost/` (Caddy, self-signed) or `:3001`.
- Microphone allowed, speakers active (TTS).

---

## 1. Happy path — from use case to training start

### 1.1 Entry

> **User:** Can you help me specialize a model for my use case?

*→ Soofi asks which use case.*

### 1.2 State the use case

> **User:** I need an assistant for compliance topics.

*→ Soofi confirms "Compliance" and offers to search for datasets.*

### 1.3 Dataset search — Dataspace first

> **User:** Yes, please look for datasets.

*→ Dataset Agent is invoked (Eclipse Dataspace first). If nothing is found,
Soofi suggests HuggingFace as a fallback.*

### 1.4 Dataset search — HuggingFace

> **User:** Sure, check HuggingFace.

*→ Soofi lists 5 datasets (e.g. `refusal-compliance-pairs`,
`Akshata/autotrain-data-compliance`, …).*

### 1.5 Pick a dataset

> **User:** Take the first dataset.

*→ Soofi recommends matching base models (Soofi 8B / 30B MoE / 120B MoE), each
with a short fit rationale (digital sovereignty, scale).*

### 1.6 Pick a base model

> **User:** Use the Soofi 120B MoE.

*→ Soofi proposes training methods (e.g. RAG, SFT, DPO, LoRA, QLoRA) and asks
which one to use.*

### 1.7 Pick a method

> **User:** Let's go with QLoRA.

*→ Soofi summarizes all four slots (use case, dataset, base model, method) and
asks whether to start the training.*

### 1.8 Start training

> **User:** Yes, start the training!

*→ Training Agent is invoked, the side panel opens the **training overview**
(`training_view`). Soofi confirms: "The training job has been started."*

---

## 2. Side questions — insertable anywhere

The blocks below work at any point in the conversation. After the side
question, Soofi picks up the main thread again (optionally via
"Where did we leave off?").

### 2.A Show agent cards

> **User:** Show me the agent cards.

*→ Side panel opens `agent_cards` — 4 cards: Interaction, Advisor, Training,
Dataset agent.*

> **User:** Close the view again.

*→ Side panel closes.*

### 2.B Open / close the training overview

> **User:** Open the training overview.

*→ Side panel `training_view` shows phases (data preparation, training,
evaluation) and progress.*

> **User:** Close the training overview again.

### 2.C Orientation inside the dialog

> **User:** Where did we leave off? What's still missing?

*→ Soofi lists the filled slots (use case / dataset / base model / method) and
names the next missing one.*

### 2.D Knowledge — method comparison

> **User:** Can you compare the methods? What's the difference between RAG, LoRA, QLoRA, SFT and DPO?

*→ Advisor Agent answers via RAG based on `rag_vs_fine_tuning.md`, `lora.md`,
`qlora.md`, `dpo.md`. Sources are shown on the chat turn.*

### 2.E Knowledge — base models

> **User:** Which open models do you know? Can you compare them?

*→ Advisor explains Soofi/8ra, OLMo, Mistral, Qwen, DeepSeek using
`base_models.md` and `rag_vs_fine_tuning.md` (sovereignty, transparency,
license).*

### 2.F Knowledge — 8ra initiative

> **User:** What can you tell me about the 8ra initiative?

*→ Advisor answers from `8ra_initiative.md` and `soofi-project.md` (EU member
states, IPCEI-CIS, BMWE coordination).*

### 2.G Knowledge — RAG vs. fine-tuning

> **User:** When should I use RAG, when fine-tuning?

*→ Advisor explains using `rag_vs_fine_tuning.md` — RAG for dynamic knowledge,
fine-tuning for language style / output format.*

### 2.H Knowledge — use-case examples

> **User:** What use cases is Soofi typically used for?

*→ Advisor lists examples from `01_compliance_copilot.md`,
`02_wissensmanagement.md`, `03_engineering_copilot.md`,
`07_digital_product_passport.md`, `08_vergabe_assistent.md`,
`09_verwaltungsassistent.md`.*

---

## 3. Variations for further demo runs

| Use case              | Dataset source    | Base model        | Method |
|-----------------------|-------------------|-------------------|--------|
| Compliance            | HuggingFace       | Soofi 120B MoE    | QLoRA  |
| Materials research    | Eclipse Dataspace | Soofi 30B MoE     | LoRA   |
| Knowledge management  | HuggingFace       | Soofi 8B Dense    | RAG    |
| Engineering copilot   | Eclipse Dataspace | Soofi 30B MoE     | SFT    |

**Tip for Eclipse Dataspace:** first say "look for datasets"; on a miss, ask
specifically for `Materials research` in the Dataspace — the Dataset Agent
then returns the catalog entry with `counterPartyAddress`.

---

## 4. Reset / new session

- Close the browser tab or reload the page → new session id.
- Session logs land under `session-logs/YYYY-MM-DD_HH-MM-SS_<id>.md` (if
  `SESSION_LOG_ENABLED=true`).

---

## 5. Failure scenarios (good for demo robustness)

- **No Dataspace hit** → "Try HuggingFace" as a fallback.
- **No HuggingFace hit** → ask for alternative search terms.
- **Advisor answer is too short** → "Can you elaborate on that?" — the Advisor
  continues on the existing `advisor_context_id`.
- **Agent card missing** → `./down.sh && ./up.sh --build` re-checks the A2A
  registration.
