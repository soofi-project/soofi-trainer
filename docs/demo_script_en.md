# Soofi Trainer — Demo / User Script

This script walks through the Soofi Trainer end-to-end — from picking a use
case to launching the model training job. It also provides **side-question
blocks** that can be inserted at any point in the conversation (agent cards,
training overview, knowledge content).

All user lines are phrased so they can be spoken or typed directly into the
Soofi UI. Expected agent reactions are shown in *italics*.

Soofi Trainer is a demonstrator — the suggested methods and models are not
always the technically optimal choice. That's beside the point for this demo:
the focus is on showing how effortlessly companies will be able to arrive at
application-specific, sovereign models built on their own data.

Feel free to play with the system, try your own dialogues and dive in — it's
absolutely fine if something doesn't work on the first try. **Session logs**
are written in the background, and we'd be happy to review them with you
afterwards. These logs are **text-only transcripts** of the dialogue — **no
voice recordings** are stored.

> **Language note:** The Soofi stack ships with German as the default. Switch
> the UI to English via the language toggle before running this script.

---

## 0. Prerequisites

### Backend & access

- The dockerized backend runs on DFKI servers in Saarbrücken.
- Access requires an active VPN connection. The VPN is already configured on
  the iPads — when it's up, a **VPN icon** appears in the top-right status
  bar.
- For failover, three VMs are running in parallel, differing only in the
  underlying model:

  | URL                                                       | Model                     |
  |-----------------------------------------------------------|---------------------------|
  | [https://soofi-1.mrk40.de](https://soofi-1.mrk40.de)      | local Qwen3.5 122B        |
  | [https://soofi-2.mrk40.de](https://soofi-2.mrk40.de)      | local Qwen3.5 122B        |
  | [https://soofi-3.mrk40.de](https://soofi-3.mrk40.de)      | gpt-4o-mini (cloud)       |

- The iPads have matching **app icons on the home screen** — just tap;
  no need to type a URL manually.

### iPads — usage & return

- **Important:** the iPads are rented and must never be left unattended.
- Return: the rental company picks up the devices on the **last fair day
  (Friday) around 15:30**. Since the fair ends at 15:00, only **half an
  hour** remains to reset the iPads to **factory state**.
- During the reset flow a **confirmation code** is sent to the
  registered contact email. Please call the iPad lead in advance so
  the code can be forwarded without delay.

---

## 0.1 Terminology for newcomers — Dataspace & Asset Administration Shell

**Dataspace.** A Dataspace is a federated, rule-based space in which
organizations offer and consume data or models without giving up control
over them. The data stays with the provider; only metadata (catalogs) is
published, and access is governed through usage contracts (policies). The
technical foundation is typically the **Eclipse Dataspace Connector (EDC)**
— an open-source connector based on IDSA standards that standardizes
catalog exchange, contract negotiation, and data transfer. Typical
initiatives: Gaia-X, Catena-X, Manufacturing-X, Mobility Data Space, 8ra.

**Asset Administration Shell (AAS, German: "Verwaltungsschale").** The AAS
is the digital twin of an asset (machine, component, product, software) as
defined by **Industrie 4.0 / Plattform Industrie 4.0**. It bundles all
relevant information about an asset — properties, state, documents,
capabilities — in standardized **submodels** (e.g. Digital Nameplate,
Technical Data, Documentation) and exposes them via a uniform API (REST,
OPC UA, MQTT). Here it is implemented with **Eclipse BaSyx**. This makes
assets machine-readable, vendor-independent, and linkable across Dataspace
boundaries.

## 0.2 How Soofi Trainer uses them

In Soofi Trainer, the **Dataspace** serves as a sovereign source for
training datasets. The Dataset Agent first queries the **EDC Consumer**
(via MCP) and searches the catalog of the connected **EDC Provider** (stack
for suitable datasets — e.g. for materials research or engineering. Only when the Dataspace yields nothing does it fall back to
HuggingFace. This demonstrates how a company can feed internal or
contractually regulated data into LLM training without making it publicly
available.

The **Asset Administration Shell** provides Soofi with the domain context
of the assets involved in the use case. The AAS stack (Eclipse BaSyx) hosts
submodels for typical SME / engineering scenarios
(machines, components, data sheets). Agents can read this information as
structured domain knowledge — e.g. to tailor datasets to a specific asset,
enrich training data with metadata, or later power an Engineering Copilot
with grounded answers about the real machine. Dataspace and AAS together
form the bridge between sovereign data exchange and machine-readable asset
knowledge on which Soofi's training is built.

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

- Press the **reset button** in the Soofi UI → starts a fresh session.
- Alternatively: close the browser tab or reload the page → new session id.

---

## 5. Failure scenarios (good for demo robustness)

- **No Dataspace hit** → "Try HuggingFace" as a fallback.
- **No HuggingFace hit** → ask for alternative search terms.
- **Advisor answer is too short** → "Can you elaborate on that?"
