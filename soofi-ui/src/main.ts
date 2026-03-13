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

import "./components/agent-flow.js";
import type { FlowState } from "./components/agent-flow.js";
import { tr, type Language } from "./i18n.js";

// Slugify helper — must match _slugify() in knowledge ingestion
function slugify(text: string): string {
  return text
    .toLowerCase()
    .trim()
    .replace(/[^\p{L}\p{N}\s_-]/gu, "")
    .replace(/\s+/g, "-");
}

// Configure marked: synchronous, open links in new tab, heading IDs
marked.use({
  async: false,
  renderer: {
    link({ href, title, text }) {
      const titleAttr = title ? ` title="${title}"` : "";
      // Normalize /docs/ URLs: strip any domain the LLM may have prepended
      const docsIdx = href?.indexOf("/docs/") ?? -1;
      if (docsIdx >= 0) {
        const cleanHref = href!.slice(docsIdx);
        return `<a href="${cleanHref}"${titleAttr}>${text}</a>`;
      }
      return `<a href="${href}"${titleAttr} target="_blank" rel="noopener">${text}</a>`;
    },
    heading({ text, depth }) {
      const id = slugify(text);
      return `<h${depth} id="${id}">${text}</h${depth}>`;
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

interface AgentCardData {
  name: string;
  description?: string;
  url?: string;
  version?: string;
  protocolVersion?: string;
  preferredTransport?: string;
  defaultInputModes?: string[];
  defaultOutputModes?: string[];
  capabilities?: { streaming?: boolean; [key: string]: unknown };
  skills?: Array<{
    id?: string;
    name?: string;
    description?: string;
    tags?: string[];
  }>;
  _status: "online" | "offline";
  _error?: string;
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
      flex-direction: row;
      justify-content: center;
      height: 100vh;
      width: 100%;
      background: var(--color-bg, #f5f5f5);
    }

    .chat-column {
      display: flex;
      flex-direction: column;
      flex: 1;
      min-width: 0;
      max-width: 800px;
      height: 100%;
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
      flex: 1;
    }
    .lang-toggle {
      display: flex;
      border-radius: 16px;
      font-size: 13px;
      font-weight: 600;
      letter-spacing: 0.5px;
      cursor: pointer;
      background: var(--color-hover, #f1f3f4);
      box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.15);
    }
    .lang-toggle span {
      padding: 4px 10px;
      border-radius: 16px;
      color: var(--color-text-secondary, #5f6368);
      transition: all 0.2s;
    }
    .lang-toggle span.active {
      background: var(--color-primary, #1a73e8);
      color: #fff;
      box-shadow: 0 2px 4px rgba(26, 115, 232, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.2);
    }
    .lang-toggle span:not(.active):hover {
      color: var(--color-text, #202124);
    }
    .reset-btn {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 32px;
      height: 32px;
      border: none;
      border-radius: 50%;
      background: transparent;
      color: var(--color-text-secondary, #5f6368);
      cursor: pointer;
      transition: background 0.15s, color 0.15s;
    }
    .reset-btn:hover {
      background: var(--color-hover, #f1f3f4);
      color: var(--color-text, #202124);
    }
    .reset-btn svg {
      width: 18px;
      height: 18px;
    }

    /* Reset confirmation dialog */
    .dialog-overlay {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.4);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 1000;
      animation: fadeIn 0.15s ease-out;
    }
    @keyframes fadeIn {
      from { opacity: 0; }
      to { opacity: 1; }
    }
    .dialog {
      background: var(--color-surface, #fff);
      border-radius: 16px;
      padding: 24px;
      min-width: 320px;
      max-width: 400px;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
    }
    .dialog h2 {
      margin: 0 0 8px;
      font-size: 18px;
      font-weight: 600;
      color: var(--color-text, #202124);
    }
    .dialog p {
      margin: 0 0 20px;
      font-size: 14px;
      color: var(--color-text-secondary, #5f6368);
      line-height: 1.5;
    }
    .dialog-actions {
      display: flex;
      justify-content: flex-end;
      gap: 8px;
    }
    .dialog-actions button {
      padding: 8px 20px;
      border-radius: 20px;
      font-size: 14px;
      font-weight: 500;
      cursor: pointer;
      transition: background 0.15s;
    }
    .dialog-actions .cancel {
      background: transparent;
      border: 1px solid var(--color-border, #dadce0);
      color: var(--color-text, #202124);
    }
    .dialog-actions .cancel:hover {
      background: var(--color-hover, #f1f3f4);
    }
    .dialog-actions .confirm {
      background: #d93025;
      border: none;
      color: #fff;
    }
    .dialog-actions .confirm:hover {
      background: #c5221f;
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

    /* Doc viewer panel */
    .doc-viewer {
      flex: 0 0 500px;
      height: 100%;
      display: flex;
      flex-direction: column;
      border-left: 1px solid var(--color-border, #dadce0);
      background: var(--color-surface, #fff);
    }
    .doc-viewer__header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 12px 16px;
      border-bottom: 1px solid var(--color-border, #dadce0);
      font-size: 14px;
      font-weight: 500;
      color: var(--color-text, #202124);
    }
    .doc-viewer__close {
      background: none;
      border: none;
      cursor: pointer;
      font-size: 20px;
      color: var(--color-text-secondary, #5f6368);
      padding: 0 4px;
      line-height: 1;
    }
    .doc-viewer__close:hover {
      color: var(--color-text, #202124);
    }
    .doc-viewer__jump-list {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      padding: 8px 16px;
      border-bottom: 1px solid var(--color-border, #dadce0);
      background: #fafafa;
    }
    .doc-viewer__jump-link {
      font-size: 12px;
      color: var(--color-primary, #1a73e8);
      cursor: pointer;
      text-decoration: none;
      padding: 2px 8px;
      border-radius: 12px;
      background: #e8f0fe;
    }
    .doc-viewer__jump-link:hover {
      text-decoration: underline;
    }
    .doc-viewer__body {
      flex: 1;
      overflow-y: auto;
      padding: 16px;
      line-height: 1.6;
    }
    .doc-viewer__body h1,
    .doc-viewer__body h2,
    .doc-viewer__body h3,
    .doc-viewer__body h4 {
      margin: 20px 0 8px 0;
      line-height: 1.3;
    }
    .doc-viewer__body h1:first-child,
    .doc-viewer__body h2:first-child,
    .doc-viewer__body h3:first-child {
      margin-top: 0;
    }
    .doc-viewer__body p { margin: 0 0 12px 0; }
    .doc-viewer__body ul,
    .doc-viewer__body ol {
      margin: 4px 0 12px 0;
      padding-left: 24px;
    }
    .doc-viewer__body a {
      color: var(--color-primary, #1a73e8);
      text-decoration: none;
    }
    .doc-viewer__body a:hover { text-decoration: underline; }
    .doc-viewer__body code {
      background: #f1f3f4;
      padding: 2px 6px;
      border-radius: 4px;
      font-size: 0.9em;
    }
    .doc-viewer__body pre {
      background: #f1f3f4;
      padding: 12px;
      border-radius: 8px;
      overflow-x: auto;
      margin: 8px 0;
    }
    .doc-viewer__body pre code { background: none; padding: 0; }
    .doc-viewer__body .highlighted-section {
      border-left: 3px solid #f9a825;
      padding-left: 8px;
      margin-left: -11px;
    }

    /* Responsive: narrower doc viewer on tablets */
    @media (min-width: 1024px) and (max-width: 1279px) {
      .doc-viewer {
        flex: 0 0 360px;
      }
    }

    /* Responsive: overlay on narrow viewports */
    @media (max-width: 1023px) {
      .doc-viewer {
        position: fixed;
        inset: 0;
        width: 100%;
        z-index: 100;
      }
      .doc-viewer__header {
        padding: 12px 16px;
      }
    }

    /* Agent card accordion */
    .agent-cards {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .agent-card-accordion {
      border: 1px solid var(--color-border, #dadce0);
      border-radius: 8px;
      overflow: hidden;
    }
    .agent-card-accordion summary {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 12px 16px;
      cursor: pointer;
      font-weight: 500;
      background: #fafafa;
      list-style: none;
      user-select: none;
    }
    .agent-card-accordion summary::-webkit-details-marker { display: none; }
    .agent-card-accordion summary::before {
      content: "\\25B6";
      font-size: 10px;
      margin-right: 8px;
      transition: transform 0.2s;
    }
    .agent-card-accordion[open] summary::before {
      transform: rotate(90deg);
    }
    .agent-card-accordion[open] summary {
      border-bottom: 1px solid var(--color-border, #dadce0);
    }
    .agent-card-details {
      padding: 12px 16px;
    }
    .agent-card-name {
      flex: 1;
    }
    .agent-card-status {
      font-size: 12px;
      padding: 2px 8px;
      border-radius: 12px;
      font-weight: 500;
    }
    .agent-card-status--offline {
      background: #fce8e6;
      color: #c5221f;
    }
    .agent-card__desc {
      margin: 0 0 12px 0;
      color: var(--color-text-secondary, #5f6368);
    }
    .agent-card__row {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 6px 0;
      border-bottom: 1px solid #f1f3f4;
    }
    .agent-card__row:last-child { border-bottom: none; }
    .agent-card__label {
      font-weight: 500;
      font-size: 13px;
      color: var(--color-text-secondary, #5f6368);
      min-width: 80px;
    }
    .agent-card__offline-msg {
      margin: 8px 0 0;
      color: var(--color-text-secondary, #5f6368);
      font-style: italic;
    }
    .agent-card__skills {
      margin-top: 12px;
    }
    .agent-card__skill {
      margin: 8px 0;
      padding: 8px 12px;
      background: #f8f9fa;
      border-radius: 6px;
    }
    .agent-card__skill strong {
      display: block;
      margin-bottom: 4px;
    }
    .agent-card__skill p {
      margin: 0 0 6px 0;
      font-size: 13px;
      color: var(--color-text-secondary, #5f6368);
    }
    .agent-card__tags {
      display: flex;
      flex-wrap: wrap;
      gap: 4px;
    }
    .agent-card__tag {
      font-size: 11px;
      padding: 1px 6px;
      border-radius: 10px;
      background: #e8f0fe;
      color: var(--color-primary, #1a73e8);
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

  @state() private language: Language = "de";
  @state() private messages: ChatMessage[] = [];
  @state() private inputValue = "";
  @state() private streaming = false;
  @state() private surfaceEntries: Array<[string, v0_8.Types.Surface]> = [];
  @state() private dashboardEmbed: DashboardEmbedInfo | null = null;
  @state() private isRecording = false;
  @state() private searching = false;
  @state() private searchStatusLabel = "";
  @state() private flowState: FlowState = "idle";
  private _flowTimer: ReturnType<typeof setTimeout> | null = null;
  private _fetchController: AbortController | null = null;
  @state() private docViewerUrl: string | null = null;
  @state() private docContent = "";
  @state() private docViewerAnchors: string[] = [];
  @state() private agentCards: Array<[string, AgentCardData]> | null = null;
  @state() private showResetDialog = false;

  // All /docs/ links seen in the conversation, in order of appearance
  private docLinks: string[] = [];
  private docLinksCurrentIdx = -1;

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
  private sttGeneration = 0;
  private currentAudio: HTMLAudioElement | null = null;

  // True while streaming a response that was triggered by voice input (no input focus after)
  private _voiceSession = false;

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
    const docFileName = this.docViewerUrl
      ? decodeURIComponent(this.docViewerUrl.split("/").pop()?.split("#")[0] ?? "")
      : "";

    return html`
      <div class="chat-column">
      <header>
        <h1>Soofi Trainer</h1>
        <div class="lang-toggle" @click=${this.toggleLanguage}>
          <span class=${this.language === "de" ? "active" : ""}>DE</span>
          <span class=${this.language === "en" ? "active" : ""}>EN</span>
        </div>
        <button class="reset-btn" title=${tr("reset_title", this.language)} @click=${() => { this.showResetDialog = true; }}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 12a9 9 0 1 1 3 6.36"/>
            <polyline points="3 16 3 12 7 12"/>
          </svg>
        </button>
      </header>

      <div class="messages" id="messages" @click=${this.onMessagesClick}>
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
                  >${this.dashboardEmbed.title} ${tr("open_dashboard", this.language)}</a
                >
              </div>
            `
          : nothing}
      </div>

      <soofi-agent-flow .flowState=${this.flowState}></soofi-agent-flow>

      ${this.searching
        ? html`
            <div class="searching-bar">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                <path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
              </svg>
              ${this.searchStatusLabel || tr("thinking", this.language)}
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
              ${tr("recording", this.language)}
            </div>
          `
        : nothing}

      <div class="input-bar">
        <input
          type="text"
          placeholder=${tr("placeholder", this.language)}
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
                  ? tr("ptt_hold", this.language)
                  : tr("ptt_toggle", this.language)}
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
          ${tr("send", this.language)}
        </button>
      </div>
      </div>

      ${this.docViewerUrl
        ? html`
            <div class="doc-viewer">
              <div class="doc-viewer__header">
                <span>${docFileName}</span>
                <button class="doc-viewer__close" @click=${this.closeDocViewer}>&times;</button>
              </div>
              ${this.docViewerAnchors.length > 1
                ? html`
                    <div class="doc-viewer__jump-list">
                      ${this.docViewerAnchors.map(
                        (anchor) => html`
                          <a class="doc-viewer__jump-link" @click=${() => this.scrollToAnchor(anchor)}>
                            ${anchor.replace(/-/g, " ")}
                          </a>
                        `
                      )}
                    </div>
                  `
                : nothing}
              <div class="doc-viewer__body" id="doc-viewer-body">
                ${this.docViewerUrl.endsWith(".pdf")
                  ? html`<iframe src=${this.docViewerUrl} style="width:100%;height:100%;border:none;"></iframe>`
                  : unsafeHTML(this.docContent)}
              </div>
            </div>
          `
        : this.agentCards
          ? html`
              <div class="doc-viewer">
                <div class="doc-viewer__header">
                  <span>${tr("agent_cards", this.language)}</span>
                  <button class="doc-viewer__close" @click=${this.closeAgentCards}>&times;</button>
                </div>
                <div class="doc-viewer__body agent-cards">
                  ${this.agentCards.length === 1
                    ? this.renderAgentCard(this.agentCards[0][1])
                    : this.agentCards.map(
                        ([name, card]) => html`
                          <details class="agent-card-accordion">
                            <summary>
                              <span class="agent-card-name">${card.name || name}</span>
                              ${card._status === "offline"
                                ? html`<span class="agent-card-status agent-card-status--offline">${tr("agent_offline", this.language)}</span>`
                                : nothing}
                            </summary>
                            <div class="agent-card-details">
                              ${this.renderAgentCard(card)}
                            </div>
                          </details>
                        `
                      )}
                </div>
              </div>
            `
          : nothing}

      ${this.showResetDialog
        ? html`
          <div class="dialog-overlay" @click=${this.cancelReset}>
            <div class="dialog" @click=${(e: Event) => e.stopPropagation()}>
              <h2>${tr("reset_title", this.language)}</h2>
              <p>${tr("reset_body", this.language)}</p>
              <div class="dialog-actions">
                <button class="cancel" @click=${this.cancelReset}>${tr("reset_cancel", this.language)}</button>
                <button class="confirm" @click=${this.confirmReset}>${tr("reset_confirm", this.language)}</button>
              </div>
            </div>
          </div>`
        : nothing}
    `;
  }

  updated(changedProperties: Map<string, unknown>) {
    // Scroll to bottom on every update
    const messagesDiv = this.shadowRoot?.getElementById("messages");
    if (messagesDiv) {
      messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }
    // Restore focus to input only when streaming just finished AND the session was text-based.
    // For voice sessions, we leave focus off the input so Space-key PTT keeps working.
    if (changedProperties.has("streaming") && !this.streaming) {
      if (!this._voiceSession) {
        const input = this.shadowRoot?.querySelector<HTMLInputElement>(".input-bar input");
        input?.focus();
      }
      this._voiceSession = false;
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

    const sttGen = this.sttGeneration;
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
      if (text && sttGen === this.sttGeneration) {
        this.inputValue = text;
        this._voiceSession = true;
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

    this._fetchController = new AbortController();
    try {
      // Send full conversation history so the agent has context
      const history = this.messages
        .filter((m) => m.text) // skip empty placeholder
        .map((m) => ({ role: m.role, content: m.text }));

      const response = await fetch("/api/agent", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: history,
          session_id: this.sessionId,
          language: this.language,
        }),
        signal: this._fetchController.signal,
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
      // Abort signals a deliberate reset — suppress the error
      if (err instanceof Error && err.name === "AbortError") return;
      // Show error in the assistant message
      const msgs = [...this.messages];
      const lastAssistant = msgs[msgs.length - 1];
      if (lastAssistant?.role === "assistant") {
        lastAssistant.text = `${tr("error_prefix", this.language)}: ${err instanceof Error ? err.message : tr("error_unknown", this.language)}`;
      }
      this.messages = msgs;
    } finally {
      this._fetchController = null;
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
          const delta = event.delta as string;
          const msgs = [...this.messages];
          const lastAssistant = msgs[msgs.length - 1];
          if (lastAssistant?.role === "assistant") {
            lastAssistant.text += delta;
            // Track /docs/ links as they appear
            this.extractDocLinks(lastAssistant.text);
          }
          this.messages = msgs;
        }
        break;

      case "TOOL_CALL_START":
        if (this._flowTimer) clearTimeout(this._flowTimer);
        this.searching = true;
        this.searchStatusLabel = "";
        if (event.tool === "ask_training_agent_tool") {
          this.flowState = "asking-training-agent";
        } else if (event.tool === "ask_advisor_tool") {
          this.flowState = "asking-advisor";
        }
        break;

      case "TOOL_CALL_END":
        this.searching = false;
        this.searchStatusLabel = "";
        if (this._flowTimer) clearTimeout(this._flowTimer);
        if (this.flowState === "asking-training-agent" || this.flowState === "training-searching"
            || this.flowState === "training-mcp-returning" || this.flowState === "ta-returning") {
          // Training Agent: MCP back → A2A back → idle
          this.flowState = "training-mcp-returning";
          this._flowTimer = setTimeout(() => {
            this.flowState = "ta-returning";
            this._flowTimer = setTimeout(() => { this.flowState = "idle"; }, 900);
          }, 900);
        } else if (this.flowState === "asking-advisor" || this.flowState === "searching"
            || this.flowState === "mcp-returning" || this.flowState === "a2a-returning") {
          // Advisor: MCP back → A2A back → idle
          this.flowState = "mcp-returning";
          this._flowTimer = setTimeout(() => {
            this.flowState = "a2a-returning";
            this._flowTimer = setTimeout(() => { this.flowState = "idle"; }, 900);
          }, 900);
        }
        // Other tools (show_agent_card, show_dashboard, etc.): no flow animation
        break;

      case "SEARCH_STATUS":
        this.searchStatusLabel = (event.label as string) || "";
        if (this.flowState === "asking-training-agent") {
          this.flowState = "training-searching";
        } else if (this.flowState === "asking-advisor") {
          this.flowState = "searching";
        }
        // Other tools (show_agent_card, etc.): label shown but no flow animation
        break;

      case "SPEECH_TEXT":
        // TTS plays for all responses (text and voice) — intentional: the system always speaks.
        if (event.text) this.enqueueTTS(event.text as string);
        break;

      case "DOC_VIEWER":
        this.handleDocViewerEvent(event);
        break;

      case "AGENT_CARD":
        this.handleAgentCardEvent(event);
        break;

      case "TEXT_MESSAGE_END":
        this.currentMsgId = null;
        this.searching = false;
        break;

      case "RUN_FINISHED": {
        if (this._flowTimer) clearTimeout(this._flowTimer);
        this._flowTimer = null;
        this.flowState = "idle";
        this.searching = false;
        // Safety net: if the flow is still in an active (pre-return) state,
        // TOOL_CALL_END was likely never received — reset to idle.
        // Don't interrupt return animations (they have their own timers).
        const stuck = ["asking-advisor", "asking-training-agent", "searching", "training-searching"];
        if (stuck.includes(this.flowState)) {
          if (this._flowTimer) clearTimeout(this._flowTimer);
          this._flowTimer = null;
          this.flowState = "idle";
        }
        break;
      }

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

    }
  }

  // -----------------------------------------------------------------------
  // TTS audio queue
  // -----------------------------------------------------------------------

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
  // Doc viewer
  // -----------------------------------------------------------------------

  private onMessagesClick(e: MouseEvent): void {
    const target = e.target as HTMLElement;
    const anchor = target.closest("a");
    if (!anchor) return;
    const href = anchor.getAttribute("href");
    if (!href || !href.startsWith("/docs/")) return;
    e.preventDefault();
    this.openDocViewer(href);
  }

  private async openDocViewer(url: string): Promise<void> {
    // Close agent cards if open — they share the panel
    this.agentCards = null;
    this.docViewerUrl = url;
    // Sync index for next/previous navigation
    const idx = this.docLinks.indexOf(url);
    if (idx >= 0) this.docLinksCurrentIdx = idx;
    const [basePath, fragment] = url.split("#", 2);
    this.docViewerAnchors = this.collectDocAnchors(basePath);

    if (basePath.endsWith(".pdf")) return;

    try {
      const resp = await fetch(basePath);
      if (!resp.ok) {
        this.docContent = `<p>${tr("doc_load_error", this.language)}: HTTP ${resp.status}</p>`;
        return;
      }
      const mdText = await resp.text();
      this.docContent = marked.parse(mdText) as string;

      // Highlight referenced sections
      if (this.docViewerAnchors.length > 0) {
        await this.updateComplete;
        for (const anchor of this.docViewerAnchors) {
          const el = this.shadowRoot?.getElementById(anchor);
          if (el) el.classList.add("highlighted-section");
        }
      }

      // Scroll to fragment
      if (fragment) {
        await this.updateComplete;
        this.scrollToAnchor(fragment);
      }
    } catch {
      this.docContent = `<p>${tr("doc_load_error_generic", this.language)}</p>`;
    }
  }

  private closeDocViewer(): void {
    this.docViewerUrl = null;
    this.docContent = "";
    this.docViewerAnchors = [];
  }

  private scrollToAnchor(anchor: string): void {
    const el = this.shadowRoot?.getElementById(anchor);
    el?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  private extractDocLinks(text: string): void {
    const re = /\]\(\/docs\/[^)]+\)/g;
    let match: RegExpExecArray | null;
    while ((match = re.exec(text)) !== null) {
      const url = match[0].slice(2, -1); // strip ]( and )
      if (!this.docLinks.includes(url)) {
        this.docLinks.push(url);
      }
    }
  }

  private handleDocViewerEvent(event: AgUiEvent): void {
    const action = event.action as string;
    if (action === "close") {
      this.closeDocViewer();
      return;
    }
    if (action === "next") {
      const nextIdx = this.docLinksCurrentIdx + 1;
      if (nextIdx < this.docLinks.length) {
        this.docLinksCurrentIdx = nextIdx;
        this.openDocViewer(this.docLinks[nextIdx]);
      }
      return;
    }
    if (action === "previous") {
      const prevIdx = this.docLinksCurrentIdx - 1;
      if (prevIdx >= 0) {
        this.docLinksCurrentIdx = prevIdx;
        this.openDocViewer(this.docLinks[prevIdx]);
      }
      return;
    }
    if (action === "open") {
      const idx = (event.index as number) - 1; // 1-based → 0-based
      if (idx >= 0 && idx < this.docLinks.length) {
        this.docLinksCurrentIdx = idx;
        this.openDocViewer(this.docLinks[idx]);
      }
    }
  }

  // -----------------------------------------------------------------------
  // Agent card viewer
  // -----------------------------------------------------------------------

  private renderAgentCard(card: AgentCardData) {
    if (card._status === "offline") {
      return html`
        <div class="agent-card">
          <div class="agent-card__row">
            <span class="agent-card__label">Status</span>
            <span class="agent-card-status agent-card-status--offline">${tr("agent_offline", this.language)}</span>
          </div>
          <p class="agent-card__offline-msg">
            ${tr("agent_offline_msg", this.language)}
          </p>
        </div>
      `;
    }
    return html`
      <div class="agent-card">
        ${card.description
          ? html`<p class="agent-card__desc">${card.description}</p>`
          : nothing}
        ${card.version
          ? html`<div class="agent-card__row">
              <span class="agent-card__label">${tr("agent_field_version", this.language)}</span>
              <span>${card.version}</span>
            </div>`
          : nothing}
        ${card.protocolVersion
          ? html`<div class="agent-card__row">
              <span class="agent-card__label">${tr("agent_field_protocol", this.language)}</span>
              <span>A2A ${card.protocolVersion}</span>
            </div>`
          : nothing}
        ${card.preferredTransport
          ? html`<div class="agent-card__row">
              <span class="agent-card__label">${tr("agent_field_transport", this.language)}</span>
              <span>${card.preferredTransport}</span>
            </div>`
          : nothing}
        ${card.capabilities
          ? html`<div class="agent-card__row">
              <span class="agent-card__label">${tr("agent_field_streaming", this.language)}</span>
              <span>${card.capabilities.streaming ? tr("streaming_yes", this.language) : tr("streaming_no", this.language)}</span>
            </div>`
          : nothing}
        ${card.defaultInputModes?.length
          ? html`<div class="agent-card__row">
              <span class="agent-card__label">${tr("agent_field_input", this.language)}</span>
              <span>${card.defaultInputModes.join(", ")}</span>
            </div>`
          : nothing}
        ${card.defaultOutputModes?.length
          ? html`<div class="agent-card__row">
              <span class="agent-card__label">${tr("agent_field_output", this.language)}</span>
              <span>${card.defaultOutputModes.join(", ")}</span>
            </div>`
          : nothing}
        ${card.skills?.length
          ? html`
              <div class="agent-card__skills">
                <span class="agent-card__label">${tr("agent_field_skills", this.language)}</span>
                ${card.skills.map(
                  (skill) => html`
                    <div class="agent-card__skill">
                      <strong>${skill.name || skill.id}</strong>
                      ${skill.description
                        ? html`<p>${skill.description}</p>`
                        : nothing}
                      ${skill.tags?.length
                        ? html`<div class="agent-card__tags">
                            ${skill.tags.map(
                              (tag) =>
                                html`<span class="agent-card__tag">${tag}</span>`
                            )}
                          </div>`
                        : nothing}
                    </div>
                  `
                )}
              </div>
            `
          : nothing}
      </div>
    `;
  }

  private handleAgentCardEvent(event: AgUiEvent): void {
    const action = event.action as string;
    if (action === "close") {
      this.closeAgentCards();
      return;
    }
    if (action === "open") {
      const cards = event.cards as Array<[string, AgentCardData]>;
      if (cards?.length) {
        // Close doc viewer if open — they share the panel
        this.closeDocViewer();
        this.agentCards = cards;
      }
    }
  }

  private closeAgentCards(): void {
    this.agentCards = null;
  }

  private toggleLanguage(): void {
    this.language = this.language === "de" ? "en" : "de";
  }

  private cancelReset(): void {
    this.showResetDialog = false;
  }

  private confirmReset(): void {
    this.showResetDialog = false;
    this._fetchController?.abort();
    this.messages = [];
    this.inputValue = "";
    this.streaming = false;
    this.searching = false;
    this.searchStatusLabel = "";
    this.flowState = "idle";
    this.docViewerUrl = null;
    this.docContent = "";
    this.docViewerAnchors = [];
    this.agentCards = null;
    this.#processor.clearSurfaces();
    this.surfaceEntries = [];
    this.dashboardEmbed = null;
    this.docLinks = [];
    this.docLinksCurrentIdx = -1;
    this.sessionId = crypto.randomUUID();
    this.currentMsgId = null;
    // Stop active recording
    if (this.mediaRecorder && this.mediaRecorder.state !== "inactive") {
      this.mediaRecorder.stop();
    }
    this.mediaRecorder = null;
    this.audioChunks = [];
    this.isRecording = false;
    this._voiceSession = false;
    // Cancel flow animation timer
    if (this._flowTimer) clearTimeout(this._flowTimer);
    this._flowTimer = null;
    // Cancel any in-flight STT fetch
    this.sttGeneration++;
    // Cancel any pending TTS
    this.ttsGeneration++;
    this.audioQueue = Promise.resolve();
    if (this.currentAudio) {
      this.currentAudio.pause();
      this.currentAudio = null;
    }
  }

  private collectDocAnchors(basePath: string): string[] {
    const anchors: string[] = [];
    const seen = new Set<string>();
    const escapedPath = basePath.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const pattern = new RegExp(escapedPath + "#([\\w-]+)", "g");
    for (const msg of this.messages) {
      if (msg.role !== "assistant") continue;
      let match: RegExpExecArray | null;
      while ((match = pattern.exec(msg.text)) !== null) {
        if (!seen.has(match[1])) {
          seen.add(match[1]);
          anchors.push(match[1]);
        }
      }
    }
    return anchors;
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
