import { LitElement, html, css, PropertyValues } from "lit";
import { customElement, property } from "lit/decorators.js";

export type FlowState =
  | "idle"
  | "asking-advisor"  // A2A fwd dots loop
  | "searching"       // A2A fwd runs out, MCP fwd loops
  | "mcp-returning"   // MCP back runs out (Weaviate → Advisor)
  | "a2a-returning";  // A2A back runs out (Advisor → IA)

const NT = 10;           // node top y
const NH = 44;           // node height
const CY = NT + NH / 2;  // center y = 32

const SVG_NS = "http://www.w3.org/2000/svg";
const _parser = new DOMParser();

function parseSvg(source: string): SVGSVGElement {
  const doc = _parser.parseFromString(source, "image/svg+xml");
  return doc.documentElement as unknown as SVGSVGElement;
}

function buildSvgSource(s: FlowState): string {
  const aguiOn      = s !== "idle";
  const a2aOn       = s === "asking-advisor" || s === "searching"
                   || s === "mcp-returning"   || s === "a2a-returning";
  const mcpOn       = s === "searching" || s === "mcp-returning";

  // Which nodes glow
  const iaCls       = s === "asking-advisor" || s === "a2a-returning"   ? " node-rect--active" : "";
  const advisorCls  = s === "asking-advisor" || s === "searching"
                   || s === "mcp-returning"   || s === "a2a-returning"   ? " node-rect--active" : "";
  const weaviateCls = s === "searching" || s === "mcp-returning"         ? " node-rect--active" : "";

  const eC = (on: boolean) => "edge-line" + (on ? " edge-line--active" : "");
  const lC = (on: boolean) => "edge-label" + (on ? " edge-label--active" : "");

  // Each dot group gets a unique class so CSS can target it per-state
  const dots = (cls: string, x1: number, x2: number) => `
    <circle class="${cls}" r="4" style="offset-path:path('M ${x1} ${CY} L ${x2} ${CY}')"></circle>
    <circle class="${cls}" r="4" style="offset-path:path('M ${x1} ${CY} L ${x2} ${CY}');animation-delay:0.25s"></circle>
    <circle class="${cls}" r="4" style="offset-path:path('M ${x1} ${CY} L ${x2} ${CY}');animation-delay:0.5s"></circle>`;

  return `<svg xmlns="${SVG_NS}" viewBox="0 0 760 60" preserveAspectRatio="xMidYMid meet">
    <line class="${eC(aguiOn)}" x1="90"  y1="${CY}" x2="185" y2="${CY}"/>
    <text class="${lC(aguiOn)}" x="137" y="${CY - 10}">AG-UI</text>

    <line class="${eC(a2aOn)}" x1="345" y1="${CY}" x2="440" y2="${CY}"/>
    <text class="${lC(a2aOn)}" x="397" y="${CY - 10}">A2A</text>
    ${s === "asking-advisor" || s === "searching" ? dots("dot-a2a-fwd", 345, 440) : ""}
    ${s === "a2a-returning"                       ? dots("dot-a2a-back", 440, 345) : ""}

    <line class="${eC(mcpOn)}" x1="555" y1="${CY}" x2="650" y2="${CY}"/>
    <text class="${lC(mcpOn)}" x="602" y="${CY - 10}">MCP</text>
    ${s === "searching"      ? dots("dot-mcp-fwd", 555, 650) : ""}
    ${s === "mcp-returning"  ? dots("dot-mcp-back", 650, 555) : ""}

    <rect class="node-rect"               x="0"   y="${NT}" width="90"  height="${NH}" rx="8"/>
    <text class="node-label"              x="45"  y="${CY}">Browser</text>

    <rect class="node-rect${iaCls}"       x="185" y="${NT}" width="160" height="${NH}" rx="8"/>
    <text class="node-label"              x="265" y="${CY}">Interaction Agent</text>

    <rect class="node-rect${advisorCls}"  x="440" y="${NT}" width="115" height="${NH}" rx="8"/>
    <text class="node-label"              x="497" y="${CY}">Advisor</text>

    <rect class="node-rect${weaviateCls}" x="650" y="${NT}" width="110" height="${NH}" rx="8"/>
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
    .dot-mcp-fwd, .dot-mcp-back {
      fill: var(--color-primary, #1a73e8);
      opacity: 0;
    }

    /* ── Looping dots: outgoing journey, active phase ───────────────────── */
    .state-asking-advisor .dot-a2a-fwd,
    .state-searching      .dot-mcp-fwd {
      animation: flow 0.75s linear infinite;
    }

    /* ── One-shot run-out: completing the final trip ────────────────────── */
    .state-searching      .dot-a2a-fwd,
    .state-mcp-returning  .dot-mcp-back,
    .state-a2a-returning  .dot-a2a-back {
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

  private _prevFlowState: FlowState = "idle";

  render() {
    const visible = this.flowState !== "idle";
    const cls = ["flow-wrap", visible ? "visible" : "", `state-${this.flowState}`]
      .filter(Boolean).join(" ");
    return html`<div class="${cls}"><div id="svg-host"></div></div>`;
  }

  protected updated(changed: PropertyValues): void {
    if (!changed.has("flowState")) return;
    if (this.flowState === this._prevFlowState) return;
    this._prevFlowState = this.flowState;

    const host = this.shadowRoot?.getElementById("svg-host");
    if (!host) return;
    const imported = document.importNode(parseSvg(buildSvgSource(this.flowState)), true);
    host.replaceChildren(imported);
  }
}

declare global {
  interface HTMLElementTagNameMap {
    "soofi-agent-flow": SoofiAgentFlow;
  }
}
