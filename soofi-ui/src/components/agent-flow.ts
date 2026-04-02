import { LitElement, html, css, PropertyValues } from "lit";
import { customElement, property } from "lit/decorators.js";

export type FlowState =
  | "idle"
  | "asking-advisor"          // A2A fwd dots loop (IA → Advisor)
  | "searching"               // A2A fwd runs out, MCP fwd loops (Advisor → Weaviate)
  | "mcp-returning"           // MCP back runs out (Weaviate → Advisor)
  | "a2a-returning"           // A2A back runs out (Advisor → IA)
  | "asking-training-agent"   // A2A fwd dots loop (IA → Training Agent)
  | "training-searching"      // A2A fwd runs out, MCP fwd loops (TA → Gateway)
  | "training-mcp-returning"  // MCP back runs out (Gateway → TA)
  | "ta-returning"            // A2A back runs out (Training Agent → IA)
  | "asking-dataset-agent"    // A2A fwd dots loop (IA → Dataset Agent)
  | "dataset-searching"       // A2A fwd runs out, MCP fwd loops (DA → EDC)
  | "dataset-mcp-returning"   // MCP back runs out (EDC → DA)
  | "da-returning";           // A2A back runs out (Dataset Agent → IA)

const NT = 10;           // node top y
const NH = 44;           // node height
const CY = NT + NH / 2;  // center y = 32

const SVG_NS = "http://www.w3.org/2000/svg";
const _parser = new DOMParser();

function parseSvg(source: string): SVGSVGElement {
  const doc = _parser.parseFromString(source, "image/svg+xml");
  return doc.documentElement as unknown as SVGSVGElement;
}

/** Map MCP tool name from the dataset agent to a short display label. */
function mcpTargetLabel(tool: string): string {
  if (tool.startsWith("search_huggingface") || tool.startsWith("get_huggingface"))
    return "HuggingFace";
  if (tool.startsWith("query_federated") || tool.startsWith("get_federated")
    || tool.startsWith("list_assets") || tool.startsWith("find_assets")
    || tool.startsWith("get_asset") || tool.startsWith("get_catalog"))
    return "EDC";
  return tool ? "MCP" : "EDC";
}

function buildSvgSource(s: FlowState, mcpTarget = ""): string {
  const isAdvisor  = s === "asking-advisor" || s === "searching"
                  || s === "mcp-returning"  || s === "a2a-returning";
  const isTraining = s === "asking-training-agent" || s === "training-searching"
                  || s === "training-mcp-returning" || s === "ta-returning";
  const isDataset  = s === "asking-dataset-agent" || s === "dataset-searching"
                  || s === "dataset-mcp-returning" || s === "da-returning";

  const aguiOn = s !== "idle";
  const a2aOn  = isAdvisor || isTraining || isDataset;
  const mcpOn  = s === "searching" || s === "mcp-returning";
  const ta2aOn = isTraining;
  const da2aOn = isDataset;

  // Node glow
  const iaCls  = (s === "asking-advisor" || s === "a2a-returning"
               || s === "asking-training-agent" || s === "ta-returning"
               || s === "asking-dataset-agent" || s === "da-returning") ? " node-rect--active" : "";
  const advCls = isAdvisor                                                ? " node-rect--active" : "";
  const weavCls = (s === "searching" || s === "mcp-returning")           ? " node-rect--active" : "";
  const taCls  = isTraining                                               ? " node-rect--active" : "";
  const tgCls  = (s === "training-searching" || s === "training-mcp-returning") ? " node-rect--active" : "";
  const daCls  = isDataset                                                ? " node-rect--active" : "";
  const edcCls = (s === "dataset-searching" || s === "dataset-mcp-returning") ? " node-rect--active" : "";

  const eC = (on: boolean) => "edge-line"  + (on ? " edge-line--active"  : "");
  const lC = (on: boolean) => "edge-label" + (on ? " edge-label--active" : "");

  const dots = (cls: string, x1: number, x2: number) => `
    <circle class="${cls}" r="4" style="offset-path:path('M ${x1} ${CY} L ${x2} ${CY}')"></circle>
    <circle class="${cls}" r="4" style="offset-path:path('M ${x1} ${CY} L ${x2} ${CY}');animation-delay:0.25s"></circle>
    <circle class="${cls}" r="4" style="offset-path:path('M ${x1} ${CY} L ${x2} ${CY}');animation-delay:0.5s"></circle>`;

  if (isTraining) {
    // Training Agent path: Browser → IA → Training Agent → Training Gateway
    return `<svg xmlns="${SVG_NS}" viewBox="0 0 760 60" preserveAspectRatio="xMidYMid meet">
      <line class="${eC(aguiOn)}" x1="90"  y1="${CY}" x2="185" y2="${CY}"/>
      <text class="${lC(aguiOn)}" x="137" y="${CY - 10}">AG-UI</text>

      <line class="${eC(ta2aOn)}" x1="345" y1="${CY}" x2="440" y2="${CY}"/>
      <text class="${lC(ta2aOn)}" x="397" y="${CY - 10}">A2A</text>
      ${s === "asking-training-agent" || s === "training-searching" ? dots("dot-ta-fwd",  345, 440) : ""}
      ${s === "ta-returning"          ? dots("dot-ta-back", 440, 345) : ""}

      <line class="${eC(isTraining)}" x1="575" y1="${CY}" x2="650" y2="${CY}"/>
      <text class="${lC(isTraining)}" x="612" y="${CY - 10}">MCP</text>
      ${s === "training-searching"      ? dots("dot-ta-mcp-fwd",  575, 650) : ""}
      ${s === "training-mcp-returning"  ? dots("dot-ta-mcp-back", 650, 575) : ""}

      <rect class="node-rect"          x="0"   y="${NT}" width="90"  height="${NH}" rx="8"/>
      <text class="node-label"         x="45"  y="${CY}">Browser</text>

      <rect class="node-rect${iaCls}"  x="185" y="${NT}" width="160" height="${NH}" rx="8"/>
      <text class="node-label"         x="265" y="${CY}">Interaction Agent</text>

      <rect class="node-rect${taCls}"  x="440" y="${NT}" width="135" height="${NH}" rx="8"/>
      <text class="node-label"         x="507" y="${CY}">Training Agent</text>

      <rect class="node-rect${tgCls}"  x="650" y="${NT}" width="110" height="${NH}" rx="8"/>
      <text class="node-label"         x="705" y="${CY}">Training Gateway</text>
    </svg>`;
  }

  if (isDataset) {
    const showMcp = !!mcpTarget;
    const targetLabel = mcpTargetLabel(mcpTarget);
    // Dataset Agent path: Browser → IA → Dataset Agent → (EDC/HuggingFace)
    return `<svg xmlns="${SVG_NS}" viewBox="0 0 760 60" preserveAspectRatio="xMidYMid meet">
      <line class="${eC(aguiOn)}" x1="90"  y1="${CY}" x2="185" y2="${CY}"/>
      <text class="${lC(aguiOn)}" x="137" y="${CY - 10}">AG-UI</text>

      <line class="${eC(da2aOn)}" x1="345" y1="${CY}" x2="440" y2="${CY}"/>
      <text class="${lC(da2aOn)}" x="397" y="${CY - 10}">A2A</text>
      ${s === "asking-dataset-agent" || s === "dataset-searching" ? dots("dot-da-fwd",  345, 440) : ""}
      ${s === "da-returning"         ? dots("dot-da-back", 440, 345) : ""}

      ${showMcp ? `
      <line class="${eC(isDataset)}" x1="575" y1="${CY}" x2="650" y2="${CY}"/>
      <text class="${lC(isDataset)}" x="612" y="${CY - 10}">MCP</text>
      ${s === "dataset-searching"      ? dots("dot-da-mcp-fwd",  575, 650) : ""}
      ${s === "dataset-mcp-returning"  ? dots("dot-da-mcp-back", 650, 575) : ""}
      ` : ""}

      <rect class="node-rect"          x="0"   y="${NT}" width="90"  height="${NH}" rx="8"/>
      <text class="node-label"         x="45"  y="${CY}">Browser</text>

      <rect class="node-rect${iaCls}"  x="185" y="${NT}" width="160" height="${NH}" rx="8"/>
      <text class="node-label"         x="265" y="${CY}">Interaction Agent</text>

      <rect class="node-rect${daCls}"  x="440" y="${NT}" width="135" height="${NH}" rx="8"/>
      <text class="node-label"         x="507" y="${CY}">Dataset Agent</text>

      ${showMcp ? `
      <rect class="node-rect${edcCls}" x="650" y="${NT}" width="110" height="${NH}" rx="8"/>
      <text class="node-label"         x="705" y="${CY}">${targetLabel}</text>
      ` : ""}
    </svg>`;
  }

  // Advisor path (default): Browser → IA → Advisor → Weaviate
  return `<svg xmlns="${SVG_NS}" viewBox="0 0 760 60" preserveAspectRatio="xMidYMid meet">
    <line class="${eC(aguiOn)}" x1="90"  y1="${CY}" x2="185" y2="${CY}"/>
    <text class="${lC(aguiOn)}" x="137" y="${CY - 10}">AG-UI</text>

    <line class="${eC(a2aOn)}" x1="345" y1="${CY}" x2="440" y2="${CY}"/>
    <text class="${lC(a2aOn)}" x="397" y="${CY - 10}">A2A</text>
    ${s === "asking-advisor" || s === "searching" ? dots("dot-a2a-fwd", 345, 440) : ""}
    ${s === "a2a-returning"                       ? dots("dot-a2a-back", 440, 345) : ""}

    <line class="${eC(mcpOn)}" x1="555" y1="${CY}" x2="650" y2="${CY}"/>
    <text class="${lC(mcpOn)}" x="602" y="${CY - 10}">MCP</text>
    ${s === "searching"     ? dots("dot-mcp-fwd",  555, 650) : ""}
    ${s === "mcp-returning" ? dots("dot-mcp-back", 650, 555) : ""}

    <rect class="node-rect"               x="0"   y="${NT}" width="90"  height="${NH}" rx="8"/>
    <text class="node-label"              x="45"  y="${CY}">Browser</text>

    <rect class="node-rect${iaCls}"       x="185" y="${NT}" width="160" height="${NH}" rx="8"/>
    <text class="node-label"              x="265" y="${CY}">Interaction Agent</text>

    <rect class="node-rect${advCls}"      x="440" y="${NT}" width="115" height="${NH}" rx="8"/>
    <text class="node-label"              x="497" y="${CY}">Advisor</text>

    <rect class="node-rect${weavCls}"     x="650" y="${NT}" width="110" height="${NH}" rx="8"/>
    <text class="node-label"              x="705" y="${CY}">Weaviate</text>
  </svg>`;
}

@customElement("soofi-agent-flow")
export class SoofiAgentFlow extends LitElement {
  static styles = css`
    :host { display: block; }

    .flow-wrap {
      max-height: 0;
      overflow: hidden;
      transition: max-height 0.3s ease;
      background: var(--color-surface, #fff);
      border-top: 1px solid var(--color-border, #dadce0);
    }
    .flow-wrap.visible { max-height: 110px; }

    svg {
      display: block;
      width: 100%;
      padding: 8px 24px;
      box-sizing: border-box;
      overflow: visible;
    }

    /* ── Nodes ──────────────────────────────────────────────────────────── */
    .node-rect {
      fill: var(--color-surface, #fff);
      stroke: var(--color-border, #dadce0);
      stroke-width: 1.5;
    }
    .node-rect--active {
      fill: #e8f0fe;
      filter: drop-shadow(0 0 6px var(--color-primary, #1a73e8));
    }
    .node-label {
      fill: var(--color-text, #202124);
      font-family: inherit;
      font-size: 11px;
      text-anchor: middle;
      dominant-baseline: middle;
    }

    /* ── Edges ──────────────────────────────────────────────────────────── */
    .edge-line  { stroke: var(--color-border, #dadce0); stroke-width: 1.5; }
    .edge-line--active { stroke: var(--color-primary, #1a73e8); }
    .edge-label { fill: var(--color-text-secondary, #5f6368); font-family: inherit; font-size: 9px; text-anchor: middle; }
    .edge-label--active { fill: var(--color-primary, #1a73e8); }

    /* ── Dot base (invisible until a state rule gives them an animation) ── */
    .dot-a2a-fwd, .dot-a2a-back,
    .dot-mcp-fwd, .dot-mcp-back,
    .dot-ta-fwd,  .dot-ta-back,
    .dot-ta-mcp-fwd, .dot-ta-mcp-back,
    .dot-da-fwd,  .dot-da-back,
    .dot-da-mcp-fwd, .dot-da-mcp-back {
      fill: var(--color-primary, #1a73e8);
      opacity: 0;
    }

    /* ── Looping dots: outgoing journey, active phase ───────────────────── */
    .state-asking-advisor       .dot-a2a-fwd,
    .state-searching            .dot-mcp-fwd,
    .state-asking-training-agent .dot-ta-fwd,
    .state-training-searching   .dot-ta-mcp-fwd,
    .state-asking-dataset-agent .dot-da-fwd,
    .state-dataset-searching    .dot-da-mcp-fwd {
      animation: flow 0.75s linear infinite;
    }

    /* ── One-shot run-out: completing the final trip ────────────────────── */
    .state-searching            .dot-a2a-fwd,
    .state-mcp-returning        .dot-mcp-back,
    .state-a2a-returning        .dot-a2a-back,
    .state-training-searching   .dot-ta-fwd,
    .state-training-mcp-returning .dot-ta-mcp-back,
    .state-ta-returning         .dot-ta-back,
    .state-dataset-searching    .dot-da-fwd,
    .state-dataset-mcp-returning .dot-da-mcp-back,
    .state-da-returning         .dot-da-back {
      animation: flow-out 0.8s linear forwards;
    }

    @keyframes flow {
      0%   { offset-distance: 0%;   opacity: 1; }
      85%  { opacity: 1; }
      100% { offset-distance: 100%; opacity: 0; }
    }

    @keyframes flow-out {
      0%   { offset-distance: 0%;   opacity: 1; }
      70%  { opacity: 0.7; }
      100% { offset-distance: 100%; opacity: 0; }
    }
  `;

  @property() flowState: FlowState = "idle";
  @property() mcpTarget = "";

  private _prevFlowState: FlowState = "idle";
  private _prevMcpTarget = "";

  render() {
    const visible = this.flowState !== "idle";
    const cls = ["flow-wrap", visible ? "visible" : "", `state-${this.flowState}`]
      .filter(Boolean).join(" ");
    return html`<div class="${cls}"><div id="svg-host"></div></div>`;
  }

  protected updated(changed: PropertyValues): void {
    if (!changed.has("flowState") && !changed.has("mcpTarget")) return;
    if (this.flowState === this._prevFlowState && this.mcpTarget === this._prevMcpTarget) return;
    this._prevFlowState = this.flowState;
    this._prevMcpTarget = this.mcpTarget;

    const host = this.shadowRoot?.getElementById("svg-host");
    if (!host) return;
    const imported = document.importNode(parseSvg(buildSvgSource(this.flowState, this.mcpTarget)), true);
    host.replaceChildren(imported);
  }
}

declare global {
  interface HTMLElementTagNameMap {
    "soofi-agent-flow": SoofiAgentFlow;
  }
}
