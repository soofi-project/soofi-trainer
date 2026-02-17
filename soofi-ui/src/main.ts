import { LitElement, html, css } from "lit";
import { customElement, state } from "lit/decorators.js";
import { A2uiRenderer, type A2uiMessage } from "./a2ui-renderer.js";

// ---------------------------------------------------------------------------
// AG-UI event types we handle
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
  surface?: A2uiMessage[];
}

// ---------------------------------------------------------------------------
// <soofi-chat> — main chat component
// ---------------------------------------------------------------------------

@customElement("soofi-chat")
export class SoofiChat extends LitElement {
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
    .surface {
      align-self: flex-start;
      width: 100%;
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

    /* A2UI component styles (rendered into light DOM via ref) */

    /* Streaming indicator */
    .streaming-dot::after {
      content: "●";
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

  @state() private messages: ChatMessage[] = [];
  @state() private inputValue = "";
  @state() private streaming = false;

  // Current assistant message being streamed
  private currentMsgId: string | null = null;
  private pendingSurface: A2uiMessage[] = [];

  // -----------------------------------------------------------------------
  // Render
  // -----------------------------------------------------------------------

  render() {
    return html`
      <header>
        <h1>Soofi Trainer</h1>
      </header>

      <div class="messages" id="messages">
        ${this.messages.map((m, i) =>
          m.role === "user"
            ? html`<div class="message message--user">${m.text}</div>`
            : html`
                <div class="message message--assistant">
                  ${m.text}${this.streaming && i === this.messages.length - 1
                    ? html`<span class="streaming-dot"></span>`
                    : ""}
                </div>
                ${m.surface && m.surface.length > 0
                  ? html`<div class="surface" id="surface-${i}"></div>`
                  : ""}
              `
        )}
      </div>

      <div class="input-bar">
        <input
          type="text"
          placeholder="Nachricht eingeben…"
          .value=${this.inputValue}
          @input=${this.onInput}
          @keydown=${this.onKeydown}
          ?disabled=${this.streaming}
        />
        <button @click=${this.sendMessage} ?disabled=${this.streaming || !this.inputValue.trim()}>
          Senden
        </button>
      </div>
    `;
  }

  updated() {
    // Render A2UI surfaces into their containers after DOM update
    for (let i = 0; i < this.messages.length; i++) {
      const msg = this.messages[i];
      if (msg.surface && msg.surface.length > 0) {
        const container = this.shadowRoot?.getElementById(`surface-${i}`);
        if (container && container.children.length === 0) {
          this.renderSurface(container, msg.surface);
        }
      }
    }
    // Scroll to bottom
    const messagesDiv = this.shadowRoot?.getElementById("messages");
    if (messagesDiv) {
      messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }
  }

  // -----------------------------------------------------------------------
  // A2UI rendering
  // -----------------------------------------------------------------------

  private renderSurface(container: HTMLElement, surface: A2uiMessage[]): void {
    // Inject scoped styles for A2UI components
    const style = document.createElement("style");
    style.textContent = `
      .a2ui-card {
        background: #fff;
        border: 1px solid #dadce0;
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
      }
      .a2ui-column { display: flex; flex-direction: column; gap: 8px; }
      .a2ui-row { display: flex; flex-direction: row; gap: 8px; flex-wrap: wrap; }
      .a2ui-text { margin: 0; }
      h2.a2ui-text { font-size: 18px; font-weight: 500; margin-bottom: 4px; }
      h3.a2ui-text { font-size: 16px; font-weight: 500; margin-bottom: 2px; }
      p.a2ui-text { font-size: 14px; color: #5f6368; line-height: 1.5; }
      .a2ui-button {
        display: inline-flex;
        align-items: center;
        padding: 8px 16px;
        border: 1px solid #dadce0;
        border-radius: 20px;
        background: #fff;
        cursor: pointer;
        font-family: inherit;
        font-size: 14px;
        transition: background 0.15s;
      }
      .a2ui-button:hover { background: #f1f3f4; }
      .a2ui-button--primary {
        background: #1a73e8;
        color: #fff;
        border-color: #1a73e8;
      }
      .a2ui-button--primary:hover { background: #1557b0; }
      .a2ui-button p { margin: 0; color: inherit; }
      .a2ui-textfield {
        display: flex;
        flex-direction: column;
        gap: 4px;
      }
      .a2ui-textfield input {
        padding: 8px 12px;
        border: 1px solid #dadce0;
        border-radius: 8px;
        font-size: 14px;
      }
    `;
    container.appendChild(style);

    const renderer = new A2uiRenderer(container, (actionName, args) => {
      this.handleAction(actionName, args);
    });

    for (const msg of surface) {
      renderer.process(msg);
    }
  }

  private handleAction(actionName: string, args?: Record<string, unknown>): void {
    // Send the action directly as a new user message (bypass input field)
    const text = args
      ? `${actionName}: ${JSON.stringify(args)}`
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
    this.pendingSurface = [];

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

      // Finalize: attach surface to last assistant message
      if (this.pendingSurface.length > 0) {
        const msgs = [...this.messages];
        const lastAssistant = msgs[msgs.length - 1];
        if (lastAssistant?.role === "assistant") {
          lastAssistant.surface = this.pendingSurface;
        }
        this.messages = msgs;
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
          this.pendingSurface = snapshot.a2ui as A2uiMessage[];
        }
        break;
      }

      // RUN_STARTED, RUN_FINISHED — no UI action needed
    }
  }
}

declare global {
  interface HTMLElementTagNameMap {
    "soofi-chat": SoofiChat;
  }
}
