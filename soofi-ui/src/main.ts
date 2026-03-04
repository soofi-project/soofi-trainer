import { SignalWatcher } from "@lit-labs/signals";
import { provide } from "@lit/context";
import { LitElement, html, css, nothing } from "lit";
import { customElement, state } from "lit/decorators.js";
import { repeat } from "lit/directives/repeat.js";
import { unsafeHTML } from "lit/directives/unsafe-html.js";
import { marked } from "marked";
import { v0_8 } from "@a2ui/lit";
import * as UI from "@a2ui/lit/ui";

// Import side-effects: registers all <a2ui-*> custom elements
import "@a2ui/lit/ui";

// Configure marked: synchronous, open links in new tab
marked.use({
  async: false,
  renderer: {
    link({ href, title, text }) {
      const titleAttr = title ? ` title="${title}"` : "";
      return `<a href="${href}"${titleAttr} target="_blank" rel="noopener">${text}</a>`;
    },
  },
});

// ---------------------------------------------------------------------------
// Voice config — baked in at build time via Vite (VITE_VOICE_* in .env)
// ---------------------------------------------------------------------------

const voiceControlsVisible: boolean =
  import.meta.env.VITE_VOICE_CONTROLS_VISIBLE !== "false";
const voiceActivation: "push-to-talk" | "toggle" =
  import.meta.env.VITE_VOICE_ACTIVATION === "toggle" ? "toggle" : "push-to-talk";

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
      word-break: break-word;
    }
    .message--user {
      align-self: flex-end;
      background: var(--color-user-bg, #e8f0fe);
      color: var(--color-text, #202124);
      white-space: pre-wrap;
    }
    .message--assistant {
      align-self: flex-start;
      background: var(--color-assistant-bg, #fff);
      box-shadow: var(--shadow, 0 1px 3px rgba(0, 0, 0, 0.12));
    }

    /* Markdown inside assistant messages */
    .message--assistant p { margin: 0 0 8px 0; }
    .message--assistant p:last-child { margin-bottom: 0; }
    .message--assistant h1,
    .message--assistant h2,
    .message--assistant h3,
    .message--assistant h4 {
      margin: 16px 0 8px 0;
      line-height: 1.3;
    }
    .message--assistant h1:first-child,
    .message--assistant h2:first-child,
    .message--assistant h3:first-child {
      margin-top: 0;
    }
    .message--assistant ul,
    .message--assistant ol {
      margin: 4px 0 8px 0;
      padding-left: 24px;
    }
    .message--assistant li { margin-bottom: 4px; }
    .message--assistant a {
      color: var(--color-primary, #1a73e8);
      text-decoration: none;
    }
    .message--assistant a:hover { text-decoration: underline; }
    .message--assistant code {
      background: #f1f3f4;
      padding: 2px 6px;
      border-radius: 4px;
      font-size: 0.9em;
    }
    .message--assistant pre {
      background: #f1f3f4;
      padding: 12px;
      border-radius: 8px;
      overflow-x: auto;
      margin: 8px 0;
    }
    .message--assistant pre code {
      background: none;
      padding: 0;
    }
    .message--assistant strong { font-weight: 600; }
    .message--assistant hr {
      border: none;
      border-top: 1px solid var(--color-border, #dadce0);
      margin: 12px 0;
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
      align-items: center;
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
    .input-bar button.send-btn {
      padding: 10px 20px;
      font-size: 15px;
      font-family: inherit;
      background: var(--color-primary, #1a73e8);
      color: #fff;
      border: none;
      border-radius: 24px;
      cursor: pointer;
    }
    .input-bar button.send-btn:hover {
      background: var(--color-primary-hover, #1557b0);
    }
    .input-bar button.send-btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    /* Searching status bar */
    .searching-bar {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 24px;
      background: var(--color-surface, #fff);
      border-top: 1px solid var(--color-border, #dadce0);
      color: var(--color-text-secondary, #5f6368);
      font-size: 14px;
    }
    .searching-bar__dots span {
      animation: dot-blink 1.2s infinite;
      opacity: 0;
    }
    .searching-bar__dots span:nth-child(2) { animation-delay: 0.2s; }
    .searching-bar__dots span:nth-child(3) { animation-delay: 0.4s; }
    @keyframes dot-blink {
      0%, 80%, 100% { opacity: 0; }
      40%            { opacity: 1; }
    }

    /* Recording status bar */
    .recording-bar {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 24px;
      background: #e53935;
      color: #fff;
      font-size: 14px;
      font-weight: 500;
    }
    .recording-bar svg {
      flex-shrink: 0;
      animation: pulse-icon 1s infinite;
    }
    @keyframes pulse-icon {
      0%, 100% { opacity: 1; }
      50%       { opacity: 0.4; }
    }

    /* Push-to-talk button */
    .ptt-button {
      width: 44px;
      height: 44px;
      border-radius: 50%;
      border: 1px solid var(--color-border, #dadce0);
      background: var(--color-surface, #fff);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      transition: background 0.15s, border-color 0.15s;
      touch-action: none;
      user-select: none;
    }
    .ptt-button:hover {
      background: #f1f3f4;
    }
    .ptt-button.recording {
      background: #e53935;
      border-color: #e53935;
    }
    .ptt-button.recording svg {
      fill: #fff;
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
  @state() private isRecording = false;
  @state() private searching = false;

  // Stable session ID for advisor conversation memory (persists across messages)
  private sessionId = crypto.randomUUID();

  // Current assistant message being streamed
  private currentMsgId: string | null = null;

  // Voice recording state
  private mediaRecorder: MediaRecorder | null = null;
  private audioChunks: Blob[] = [];

  // TTS audio queue — reset on each new message to cancel pending clips
  private audioQueue: Promise<void> = Promise.resolve();
  private ttsGeneration = 0;
  private currentAudio: HTMLAudioElement | null = null;

  // Sentence buffer for streaming TTS — accumulates deltas until a sentence boundary
  private sentenceBuffer = '';
  private ttsSentenceCount = 0;
  private static readonly TTS_MAX_SENTENCES = 2;

  // Set to true when the last message was sent via voice recording
  private lastMessageWasVoice = false;

  // -----------------------------------------------------------------------
  // Lifecycle
  // -----------------------------------------------------------------------

  connectedCallback(): void {
    super.connectedCallback();
    window.addEventListener("keydown", this.onGlobalKeydown);
    window.addEventListener("keyup", this.onGlobalKeyup);
  }

  disconnectedCallback(): void {
    super.disconnectedCallback();
    window.removeEventListener("keydown", this.onGlobalKeydown);
    window.removeEventListener("keyup", this.onGlobalKeyup);
  }

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
                    ${unsafeHTML(marked.parse(m.text) as string)}${this.streaming && i === this.messages.length - 1
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

      ${this.searching
        ? html`
            <div class="searching-bar">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                <path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
              </svg>
              Suche in der Wissensdatenbank
              <span class="searching-bar__dots">
                <span>.</span><span>.</span><span>.</span>
              </span>
            </div>
          `
        : nothing}

      ${this.isRecording
        ? html`
            <div class="recording-bar">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="#fff">
                <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm5.3-3c0 3-2.54 5.1-5.3 5.1S6.7 14 6.7 11H5c0 3.41 2.72 6.23 6 6.72V21h2v-3.28c3.28-.48 6-3.3 6-6.72h-1.7z"/>
              </svg>
              Aufnahme läuft…
            </div>
          `
        : nothing}

      <div class="input-bar">
        <input
          type="text"
          placeholder="Nachricht eingeben\u2026"
          .value=${this.inputValue}
          @input=${this.onInput}
          @keydown=${this.onKeydown}
          ?disabled=${this.streaming}
        />
        ${voiceControlsVisible
          ? html`
              <button
                class="ptt-button ${this.isRecording ? "recording" : ""}"
                title=${voiceActivation === "push-to-talk"
                  ? "Gedrückt halten zum Sprechen"
                  : "Klicken zum Starten/Stoppen"}
                @pointerdown=${voiceActivation === "push-to-talk"
                  ? this.startRecording
                  : nothing}
                @pointerup=${voiceActivation === "push-to-talk"
                  ? this.stopRecording
                  : nothing}
                @pointercancel=${voiceActivation === "push-to-talk"
                  ? this.stopRecording
                  : nothing}
                @click=${voiceActivation === "toggle"
                  ? this.toggleRecording
                  : nothing}
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm5.3-3c0 3-2.54 5.1-5.3 5.1S6.7 14 6.7 11H5c0 3.41 2.72 6.23 6 6.72V21h2v-3.28c3.28-.48 6-3.3 6-6.72h-1.7z"/>
                </svg>
              </button>
            `
          : nothing}
        <button
          class="send-btn"
          @click=${this.sendMessage}
          ?disabled=${this.streaming || !this.inputValue.trim()}
        >
          Senden
        </button>
      </div>
    `;
  }

  updated(changedProperties: Map<string, unknown>) {
    // Scroll to bottom on every update
    const messagesDiv = this.shadowRoot?.getElementById("messages");
    if (messagesDiv) {
      messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }
    // Restore focus to input only when streaming just finished —
    // not on every update, so Space-key PTT can work when input is blurred
    if (changedProperties.has("streaming") && !this.streaming) {
      const input = this.shadowRoot?.querySelector<HTMLInputElement>(".input-bar input");
      input?.focus();
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
  // Global keyboard listeners for push-to-talk (Space key)
  // -----------------------------------------------------------------------

  private onGlobalKeydown = (e: KeyboardEvent): void => {
    if (voiceActivation !== "push-to-talk") return;
    if (e.code !== "Space" || e.repeat) return;
    // Only trigger when focus is outside the text input (shadow DOM: check shadowRoot.activeElement)
    const inputEl = this.shadowRoot?.querySelector<HTMLInputElement>(".input-bar input");
    if (this.shadowRoot?.activeElement === inputEl) return;
    if (!this.isRecording) {
      e.preventDefault();
      this.startRecording();
    }
  };

  private onGlobalKeyup = (e: KeyboardEvent): void => {
    if (voiceActivation !== "push-to-talk") return;
    if (e.code !== "Space") return;
    if (this.isRecording) {
      this.stopRecording();
    }
  };

  // -----------------------------------------------------------------------
  // Voice recording
  // -----------------------------------------------------------------------

  private async startRecording(event?: PointerEvent): Promise<void> {
    if (this.isRecording) return;
    if (event) {
      (event.currentTarget as Element).setPointerCapture(event.pointerId);
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      this.audioChunks = [];
      this.mediaRecorder = new MediaRecorder(stream);
      this.mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) this.audioChunks.push(e.data);
      };
      this.mediaRecorder.onstop = () => this.onRecordingStop(stream);
      this.mediaRecorder.start();
      this.isRecording = true;
    } catch {
      this.inputValue = "⚠ Mikrofon nicht verfügbar";
    }
  }

  private stopRecording(): void {
    if (!this.isRecording || !this.mediaRecorder) return;
    this.mediaRecorder.stop();
    this.isRecording = false;
  }

  private toggleRecording(): void {
    if (this.isRecording) {
      this.stopRecording();
    } else {
      this.startRecording();
    }
  }

  private async onRecordingStop(stream: MediaStream): Promise<void> {
    // Stop all microphone tracks
    stream.getTracks().forEach((t) => t.stop());

    if (this.audioChunks.length === 0) return;

    const blob = new Blob(this.audioChunks, { type: "audio/webm" });
    const formData = new FormData();
    formData.append("file", blob, "audio.webm");

    try {
      const resp = await fetch("/api/stt/transcribe", {
        method: "POST",
        body: formData,
      });
      if (!resp.ok) return;
      const data = (await resp.json()) as { text: string };
      const text = data.text?.trim();
      if (text) {
        this.inputValue = text;
        this.lastMessageWasVoice = true;
        this.sendMessage();
      }
    } catch {
      // Network error — text input remains empty, user can type manually
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

    // Cancel any queued/playing TTS from the previous response
    this.ttsGeneration++;
    this.currentAudio?.pause();
    this.currentAudio = null;
    this.audioQueue = Promise.resolve();

    // Add placeholder assistant message
    this.messages = [...this.messages, { role: "assistant", text: "" }];

    try {
      // Send full conversation history so the agent has context
      const history = this.messages
        .filter((m) => m.text) // skip empty placeholder
        .map((m) => ({ role: m.role, content: m.text }));

      const isVoice = this.lastMessageWasVoice;
      this.lastMessageWasVoice = false;

      const response = await fetch("/api/agent", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: history,
          session_id: this.sessionId,
          voice_input: isVoice,
        }),
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
            this.handleAgUiEvent(event, isVoice);
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

  private handleAgUiEvent(event: AgUiEvent, isVoice = false): void {
    switch (event.type) {
      case "TEXT_MESSAGE_START":
        this.currentMsgId = event.messageId as string;
        this.sentenceBuffer = '';
        this.ttsSentenceCount = 0;
        break;

      case "TEXT_MESSAGE_CONTENT":
        if (event.messageId === this.currentMsgId) {
          const delta = event.delta as string;
          const msgs = [...this.messages];
          const lastAssistant = msgs[msgs.length - 1];
          if (lastAssistant?.role === "assistant") {
            lastAssistant.text += delta;
          }
          this.messages = msgs;

          // TTS: buffer deltas and enqueue each complete sentence immediately
          // Stop after TTS_MAX_SENTENCES to avoid reading the full response aloud
          if (isVoice && this.ttsSentenceCount < SoofiChat.TTS_MAX_SENTENCES) {
            this.sentenceBuffer += delta;
            let pos: number;
            while ((pos = this.sentenceBuffer.search(/[.!?]+\s/)) !== -1) {
              const match = this.sentenceBuffer.slice(pos).match(/[.!?]+\s/)!;
              const endPos = pos + match[0].length;
              const sentence = this.sentenceBuffer.slice(0, endPos).trim();
              this.sentenceBuffer = this.sentenceBuffer.slice(endPos);
              const clean = this.cleanForTTS(sentence);
              if (clean) {
                this.enqueueTTS(clean);
                this.ttsSentenceCount++;
                if (this.ttsSentenceCount >= SoofiChat.TTS_MAX_SENTENCES) {
                  this.sentenceBuffer = '';
                  break;
                }
              }
            }
          }
        }
        break;

      case "TOOL_CALL_START":
        this.searching = true;
        break;

      case "TOOL_CALL_END":
        this.searching = false;
        break;

      case "TEXT_MESSAGE_END":
        // Flush remainder only if we haven't hit the sentence limit yet
        if (isVoice && this.sentenceBuffer.trim() && this.ttsSentenceCount < SoofiChat.TTS_MAX_SENTENCES) {
          const clean = this.cleanForTTS(this.sentenceBuffer);
          if (clean) this.enqueueTTS(clean);
          this.sentenceBuffer = '';
        }
        this.currentMsgId = null;
        this.searching = false;
        break;

      case "RUN_FINISHED":
        this.searching = false;
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

      // RUN_STARTED — no UI action needed
    }
  }

  // -----------------------------------------------------------------------
  // TTS audio queue
  // -----------------------------------------------------------------------

  private cleanForTTS(text: string): string {
    return text
      .replace(/\n?(?:Quellen?|Sources?|Referenzen?)[\s:：][\s\S]*/i, '') // stop at sources
      .replace(/```[\s\S]*?```/g, '')      // code blocks
      .replace(/^#{1,6}\s+/gm, '')         // headings
      .replace(/\*{1,3}(.+?)\*{1,3}/gs, '$1') // bold / italic
      .replace(/_{1,2}(.+?)_{1,2}/gs, '$1')   // underscore emphasis
      .replace(/`[^`]+`/g, '')             // inline code
      .replace(/^\d+\.\s+/gm, '')          // numbered list markers (avoid "eins punkt")
      .replace(/^[-*•]\s+/gm, '')          // bullet points
      .replace(/https?:\/\/\S+/g, '')      // URLs
      .trim();
  }

  private enqueueTTS(text: string): void {
    if (!text.trim()) return;
    const gen = this.ttsGeneration;
    const audioBlobPromise = this.fetchAudio(text);
    this.audioQueue = this.audioQueue.then(() => this.playBlob(audioBlobPromise, gen));
  }

  private async fetchAudio(text: string): Promise<Blob | null> {
    try {
      const resp = await fetch("/api/tts/synthesize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      if (!resp.ok) return null;
      return await resp.blob();
    } catch {
      return null;
    }
  }

  private async playBlob(blobPromise: Promise<Blob | null>, generation: number): Promise<void> {
    const blob = await blobPromise;
    if (!blob || generation !== this.ttsGeneration) return;
    const url = URL.createObjectURL(blob);
    const audio = new Audio(url);
    this.currentAudio = audio;
    await new Promise<void>((resolve) => {
      audio.onended = () => { URL.revokeObjectURL(url); resolve(); };
      audio.onerror = () => { URL.revokeObjectURL(url); resolve(); };
      audio.play().catch(() => resolve());
    });
    if (this.currentAudio === audio) this.currentAudio = null;
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
