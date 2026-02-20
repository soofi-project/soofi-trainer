import { SignalWatcher } from "@lit-labs/signals";
import { provide } from "@lit/context";
import { LitElement, html, css, nothing } from "lit";
import { customElement, state } from "lit/decorators.js";
import { repeat } from "lit/directives/repeat.js";
import { v0_8 } from "@a2ui/lit";
import * as UI from "@a2ui/lit/ui";

// Import side-effects: registers all <a2ui-*> custom elements
import "@a2ui/lit/ui";

// ---------------------------------------------------------------------------
// AG-UI event types we handle (text streaming layer)
// ---------------------------------------------------------------------------

interface AgUiEvent {
  type: string;
  [key: string]: unknown;
}

// ---------------------------------------------------------------------------
// Chat message model
// ---------------------------------------------------------------------------

interface ChatMessage {
  role: "user" | "assistant";
  text: string;
}

interface DashboardEmbedInfo {
  url: string;
  title: string;
  description: string;
}

// ---------------------------------------------------------------------------
// Minimal A2UI theme — provides base styling for all standard components.
// Full Soofi branding is planned for T-07-2.
// ---------------------------------------------------------------------------

const SOOFI_THEME: v0_8.Types.Theme = {
  components: {
    AudioPlayer: {},
    Button: { "type-lbl-md": true, "layout-p-2": true, "layout-px-4": true },
    Card: {
      "layout-p-4": true,
      "border-rd-3": true,
      "border-w-1": true,
      "border-c-n-20": true,
    },
    Column: { "layout-g-2": true },
    CheckBox: { container: {}, element: {}, label: {} },
    DateTimeInput: { container: {}, element: {}, label: {} },
    Divider: {},
    Image: {
      all: {},
      icon: {},
      avatar: {},
      smallFeature: {},
      mediumFeature: {},
      largeFeature: {},
      header: {},
    },
    Icon: {},
    List: {},
    Modal: { backdrop: {}, element: {} },
    MultipleChoice: { container: {}, element: {}, label: {} },
    Row: { "layout-g-2": true },
    Slider: { container: {}, element: {}, label: {} },
    Tabs: {
      container: {},
      element: {},
      controls: { all: {}, selected: {} },
    },
    Text: {
      all: {},
      h1: { "type-hdl-lg": true },
      h2: { "type-hdl-md": true },
      h3: { "type-hdl-sm": true },
      h4: { "type-lbl-lg": true },
      h5: { "type-lbl-md": true },
      caption: { "type-lbl-sm": true },
      body: { "type-body-md": true },
    },
    TextField: { container: {}, element: {}, label: {} },
    Video: {},
  },
  elements: {
    a: {},
    audio: {},
    body: {},
    button: {},
    h1: {},
    h2: {},
    h3: {},
    h4: {},
    h5: {},
    iframe: {},
    input: {},
    p: {},
    pre: {},
    textarea: {},
    video: {},
  },
  markdown: {
    p: [],
    h1: [],
    h2: [],
    h3: [],
    h4: [],
    h5: [],
    ul: [],
    ol: [],
    li: [],
    a: [],
    strong: [],
    em: [],
  },
};

// ---------------------------------------------------------------------------
// <soofi-chat> — main chat component
// ---------------------------------------------------------------------------

@customElement("soofi-chat")
class SoofiChat extends SignalWatcher(LitElement) {
  static styles = css`
    :host {
      display: flex;
      flex-direction: column;
      height: 100vh;
      width: 100%;
      max-width: 800px;
      background: var(--color-bg, #f5f5f5);
    }

    /* Header */
    header {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 16px 24px;
      background: var(--color-surface, #fff);
      border-bottom: 1px solid var(--color-border, #dadce0);
    }
    header h1 {
      font-size: 20px;
      font-weight: 500;
      color: var(--color-text, #202124);
    }

    /* Messages area */
    .messages {
      flex: 1;
      overflow-y: auto;
      padding: 16px 24px;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }

    /* Single message */
    .message {
      max-width: 85%;
      padding: 12px 16px;
      border-radius: var(--radius, 12px);
      line-height: 1.5;
      white-space: pre-wrap;
      word-break: break-word;
    }
    .message--user {
      align-self: flex-end;
      background: var(--color-user-bg, #e8f0fe);
      color: var(--color-text, #202124);
    }
    .message--assistant {
      align-self: flex-start;
      background: var(--color-assistant-bg, #fff);
      box-shadow: var(--shadow, 0 1px 3px rgba(0, 0, 0, 0.12));
    }

    /* A2UI surface container */
    .surface-container {
      align-self: flex-start;
      width: 100%;
    }

    /* Dashboard link card */
    .dashboard-card {
      align-self: flex-start;
      width: 100%;
      background: var(--color-surface, #fff);
      border: 1px solid var(--color-border, #dadce0);
      border-radius: var(--radius, 12px);
      padding: 20px;
      box-shadow: var(--shadow, 0 1px 3px rgba(0, 0, 0, 0.12));
    }
    .dashboard-card__title {
      font-size: 16px;
      font-weight: 500;
      color: var(--color-text, #202124);
      margin-bottom: 8px;
    }
    .dashboard-card__desc {
      font-size: 14px;
      color: var(--color-text-secondary, #5f6368);
      line-height: 1.5;
      margin-bottom: 16px;
    }
    .dashboard-card__btn {
      display: inline-flex;
      align-items: center;
      padding: 10px 20px;
      background: var(--color-primary, #1a73e8);
      color: #fff;
      border-radius: 24px;
      text-decoration: none;
      font-size: 14px;
      font-weight: 500;
      transition: background 0.15s;
    }
    .dashboard-card__btn:hover {
      background: var(--color-primary-hover, #1557b0);
    }

    /* Input bar */
    .input-bar {
      display: flex;
      gap: 8px;
      padding: 12px 24px;
      background: var(--color-surface, #fff);
      border-top: 1px solid var(--color-border, #dadce0);
    }
    .input-bar input {
      flex: 1;
      padding: 10px 16px;
      font-size: 15px;
      border: 1px solid var(--color-border, #dadce0);
      border-radius: 24px;
      outline: none;
      font-family: inherit;
    }
    .input-bar input:focus {
      border-color: var(--color-primary, #1a73e8);
    }
    .input-bar button {
      padding: 10px 20px;
      font-size: 15px;
      font-family: inherit;
      background: var(--color-primary, #1a73e8);
      color: #fff;
      border: none;
      border-radius: 24px;
      cursor: pointer;
    }
    .input-bar button:hover {
      background: var(--color-primary-hover, #1557b0);
    }
    .input-bar button:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    /* Streaming indicator */
    .streaming-dot::after {
      content: "\u25CF";
      animation: blink 1s infinite;
      color: var(--color-primary, #1a73e8);
      margin-left: 4px;
    }
    @keyframes blink {
      50% {
        opacity: 0;
      }
    }
  `;

  // Provide A2UI theme to all child <a2ui-surface> / <a2ui-root> components
  @provide({ context: UI.Context.themeContext })
  theme: v0_8.Types.Theme = SOOFI_THEME;

  // Signal-reactive A2UI message processor
  #processor = v0_8.Data.createSignalA2uiMessageProcessor();

  @state() private messages: ChatMessage[] = [];
  @state() private inputValue = "";
  @state() private streaming = false;
  @state() private surfaceEntries: Array<[string, v0_8.Types.Surface]> = [];
  @state() private dashboardEmbed: DashboardEmbedInfo | null = null;

  // Current assistant message being streamed
  private currentMsgId: string | null = null;

  // -----------------------------------------------------------------------
  // Render
  // -----------------------------------------------------------------------

  render() {
    return html`
      <header>
        <h1>Soofi Trainer</h1>
      </header>

      <div class="messages" id="messages">
        ${this.messages.map(
          (m, i) =>
            m.role === "user"
              ? html`<div class="message message--user">${m.text}</div>`
              : html`
                  <div class="message message--assistant">
                    ${m.text}${this.streaming && i === this.messages.length - 1
                      ? html`<span class="streaming-dot"></span>`
                      : ""}
                  </div>
                `
        )}
        ${this.surfaceEntries.length > 0
          ? html`
              <div class="surface-container">
                ${this.surfaceEntries.map(
                  ([surfaceId, surface]) => html`
                    <a2ui-surface
                      @a2uiaction=${(
                        evt: v0_8.Events.StateEvent<"a2ui.action">
                      ) => this.handleA2uiAction(evt, surfaceId)}
                      .surfaceId=${surfaceId}
                      .surface=${surface}
                      .processor=${this.#processor}
                      .enableCustomElements=${true}
                    ></a2ui-surface>
                  `
                )}
              </div>
            `
          : nothing}
        ${this.dashboardEmbed
          ? html`
              <div class="dashboard-card">
                <div class="dashboard-card__title">
                  ${this.dashboardEmbed.title}
                </div>
                <div class="dashboard-card__desc">
                  ${this.dashboardEmbed.description}
                </div>
                <a
                  class="dashboard-card__btn"
                  href=${this.dashboardEmbed.url}
                  target="_blank"
                  >${this.dashboardEmbed.title} \u00f6ffnen</a
                >
              </div>
            `
          : nothing}
      </div>

      <div class="input-bar">
        <input
          type="text"
          placeholder="Nachricht eingeben\u2026"
          .value=${this.inputValue}
          @input=${this.onInput}
          @keydown=${this.onKeydown}
          ?disabled=${this.streaming}
        />
        <button
          @click=${this.sendMessage}
          ?disabled=${this.streaming || !this.inputValue.trim()}
        >
          Senden
        </button>
      </div>
    `;
  }

  updated() {
    // Scroll to bottom
    const messagesDiv = this.shadowRoot?.getElementById("messages");
    if (messagesDiv) {
      messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }
    // Keep focus on input field
    const input = this.shadowRoot?.querySelector<HTMLInputElement>(".input-bar input");
    if (input && !this.streaming) {
      input.focus();
    }
  }

  // -----------------------------------------------------------------------
  // A2UI action handling
  // -----------------------------------------------------------------------

  private handleA2uiAction(
    evt: v0_8.Events.StateEvent<"a2ui.action">,
    surfaceId: string
  ): void {
    const detail = evt.detail;
    const actionName = detail.action.name;

    // Resolve context values from data bindings
    const context: Record<string, unknown> = {};
    if (detail.action.context) {
      for (const item of detail.action.context) {
        if (item.value.path) {
          const path = this.#processor.resolvePath(
            item.value.path,
            detail.dataContextPath
          );
          context[item.key] = this.#processor.getData(
            detail.sourceComponent!,
            path,
            surfaceId
          );
        } else if (item.value.literalString !== undefined) {
          context[item.key] = item.value.literalString;
        } else if (item.value.literalNumber !== undefined) {
          context[item.key] = item.value.literalNumber;
        } else if (item.value.literalBoolean !== undefined) {
          context[item.key] = item.value.literalBoolean;
        }
      }
    }

    // Send the action as a user message
    const text =
      Object.keys(context).length > 0
        ? `${actionName}: ${JSON.stringify(context)}`
        : actionName;
    this.sendMessageText(text);
  }

  // -----------------------------------------------------------------------
  // Input handling
  // -----------------------------------------------------------------------

  private onInput(e: Event): void {
    this.inputValue = (e.target as HTMLInputElement).value;
  }

  private onKeydown(e: KeyboardEvent): void {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      this.sendMessage();
    }
  }

  // -----------------------------------------------------------------------
  // Send message & process SSE stream
  // -----------------------------------------------------------------------

  private sendMessage(): void {
    const text = this.inputValue.trim();
    if (!text || this.streaming) return;
    this.inputValue = "";
    this.sendMessageText(text);
  }

  private async sendMessageText(text: string): Promise<void> {
    if (!text || this.streaming) return;

    // Add user message
    this.messages = [...this.messages, { role: "user", text }];
    this.streaming = true;
    this.currentMsgId = null;

    // Clear previous surfaces and embeds
    this.#processor.clearSurfaces();
    this.surfaceEntries = [];
    this.dashboardEmbed = null;

    // Add placeholder assistant message
    this.messages = [...this.messages, { role: "assistant", text: "" }];

    try {
      const response = await fetch("/api/agent", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });

      if (!response.ok || !response.body) {
        throw new Error(`HTTP ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // Process complete SSE lines
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const jsonStr = line.slice(6).trim();
          if (!jsonStr) continue;

          try {
            const event: AgUiEvent = JSON.parse(jsonStr);
            this.handleAgUiEvent(event);
          } catch {
            // Skip malformed events
          }
        }
      }
    } catch (err) {
      // Show error in the assistant message
      const msgs = [...this.messages];
      const lastAssistant = msgs[msgs.length - 1];
      if (lastAssistant?.role === "assistant") {
        lastAssistant.text = `Fehler: ${err instanceof Error ? err.message : "Unbekannter Fehler"}`;
      }
      this.messages = msgs;
    } finally {
      this.streaming = false;
    }
  }

  private handleAgUiEvent(event: AgUiEvent): void {
    switch (event.type) {
      case "TEXT_MESSAGE_START":
        this.currentMsgId = event.messageId as string;
        break;

      case "TEXT_MESSAGE_CONTENT":
        if (event.messageId === this.currentMsgId) {
          const msgs = [...this.messages];
          const lastAssistant = msgs[msgs.length - 1];
          if (lastAssistant?.role === "assistant") {
            lastAssistant.text += event.delta as string;
          }
          this.messages = msgs;
        }
        break;

      case "TEXT_MESSAGE_END":
        this.currentMsgId = null;
        break;

      case "STATE_SNAPSHOT": {
        const snapshot = event.snapshot as Record<string, unknown> | undefined;
        if (snapshot?.a2ui) {
          const a2uiMessages =
            snapshot.a2ui as v0_8.Types.ServerToClientMessage[];

          // Check for DashboardEmbed custom components before processing
          this.dashboardEmbed = this.extractDashboardEmbed(a2uiMessages);

          // Filter out DashboardEmbed components — they render natively
          const standardMessages = this.dashboardEmbed
            ? [] // Skip A2UI surface when we have a dashboard embed
            : a2uiMessages;

          if (standardMessages.length > 0) {
            this.#processor.processMessages(standardMessages);
            this.surfaceEntries = [...this.#processor.getSurfaces().entries()];
          }
        }
        break;
      }

      // RUN_STARTED, RUN_FINISHED — no UI action needed
    }
  }

  // -----------------------------------------------------------------------
  // Dashboard embed extraction
  // -----------------------------------------------------------------------

  private extractDashboardEmbed(
    messages: v0_8.Types.ServerToClientMessage[]
  ): DashboardEmbedInfo | null {
    for (const msg of messages) {
      if (!msg.surfaceUpdate) continue;
      for (const comp of msg.surfaceUpdate.components) {
        const def = comp.component as Record<string, unknown> | undefined;
        if (!def) continue;
        const dashDef = def["DashboardEmbed"] as
          | Record<string, unknown>
          | undefined;
        if (dashDef) {
          return {
            url: String(dashDef.url ?? ""),
            title: String(dashDef.title ?? ""),
            description: String(dashDef.description ?? ""),
          };
        }
      }
    }
    return null;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    "soofi-chat": SoofiChat;
  }
}
