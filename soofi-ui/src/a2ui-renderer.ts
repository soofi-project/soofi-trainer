/**
 * Lightweight A2UI renderer.
 *
 * Processes A2UI messages (surfaceUpdate, beginRendering, dataModelUpdate)
 * and renders them as native DOM elements.
 */

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface A2uiComponent {
  id: string;
  component: Record<string, unknown>;
}

interface SurfaceUpdate {
  surfaceId: string;
  components: A2uiComponent[];
}

interface BeginRendering {
  surfaceId: string;
  root: string;
  catalogId?: string;
}

interface DataModelUpdate {
  surfaceId: string;
  path?: string;
  contents: DataModelEntry[];
}

interface DataModelEntry {
  key: string;
  valueString?: string;
  valueNumber?: number;
  valueBoolean?: boolean;
  valueMap?: DataModelEntry[];
}

export interface A2uiMessage {
  surfaceUpdate?: SurfaceUpdate;
  beginRendering?: BeginRendering;
  dataModelUpdate?: DataModelUpdate;
  deleteSurface?: { surfaceId: string };
}

// Callback when a user clicks an A2UI Button action
export type ActionCallback = (actionName: string, args?: Record<string, unknown>) => void;

// ---------------------------------------------------------------------------
// Renderer
// ---------------------------------------------------------------------------

export class A2uiRenderer {
  private components = new Map<string, Record<string, unknown>>();
  private rootId: string | null = null;
  private container: HTMLElement;
  private onAction: ActionCallback;

  constructor(container: HTMLElement, onAction: ActionCallback) {
    this.container = container;
    this.onAction = onAction;
  }

  /** Process a single A2UI message. */
  process(msg: A2uiMessage): void {
    if (msg.surfaceUpdate) {
      for (const comp of msg.surfaceUpdate.components) {
        this.components.set(comp.id, comp.component);
      }
    }

    if (msg.beginRendering) {
      this.rootId = msg.beginRendering.root;
      this.render();
    }

    if (msg.deleteSurface) {
      this.components.clear();
      this.rootId = null;
      this.container.innerHTML = "";
    }
  }

  /** Clear all state and DOM. */
  clear(): void {
    this.components.clear();
    this.rootId = null;
    this.container.innerHTML = "";
  }

  // -----------------------------------------------------------------------
  // Rendering
  // -----------------------------------------------------------------------

  private render(): void {
    if (!this.rootId) return;
    this.container.innerHTML = "";
    const el = this.renderComponent(this.rootId);
    if (el) this.container.appendChild(el);
  }

  private renderComponent(id: string): HTMLElement | null {
    const def = this.components.get(id);
    if (!def) return null;

    // Each component def has exactly one key (the type)
    const type = Object.keys(def)[0];
    const props = def[type] as Record<string, unknown>;

    switch (type) {
      case "Text":
        return this.renderText(props);
      case "Card":
        return this.renderCard(props);
      case "Button":
        return this.renderButton(props);
      case "Column":
        return this.renderColumn(props);
      case "Row":
        return this.renderRow(props);
      case "TextField":
        return this.renderTextField(props);
      default:
        return this.renderFallback(type, id);
    }
  }

  private renderText(props: Record<string, unknown>): HTMLElement {
    const text = this.resolveText(props.text);
    const hint = (props.usageHint as string) || "body";
    const tagMap: Record<string, string> = {
      h1: "h1",
      h2: "h2",
      h3: "h3",
      h4: "h4",
      h5: "h5",
      caption: "small",
      body: "p",
    };
    const tag = tagMap[hint] || "p";
    const el = document.createElement(tag);
    el.textContent = text;
    el.className = "a2ui-text";
    return el;
  }

  private renderCard(props: Record<string, unknown>): HTMLElement {
    const el = document.createElement("div");
    el.className = "a2ui-card";
    const childId = props.child as string | undefined;
    if (childId) {
      const child = this.renderComponent(childId);
      if (child) el.appendChild(child);
    }
    return el;
  }

  private renderButton(props: Record<string, unknown>): HTMLElement {
    const el = document.createElement("button");
    el.className = "a2ui-button";
    if (props.primary) el.classList.add("a2ui-button--primary");

    // Render child (usually a Text component for the label)
    const childId = props.child as string | undefined;
    if (childId) {
      const child = this.renderComponent(childId);
      if (child) el.appendChild(child);
    }

    const action = props.action as { name: string; args?: Record<string, unknown> } | undefined;
    if (action) {
      el.addEventListener("click", () => {
        this.onAction(action.name, action.args);
      });
    }

    return el;
  }

  private renderColumn(props: Record<string, unknown>): HTMLElement {
    const el = document.createElement("div");
    el.className = "a2ui-column";
    const children = this.resolveChildren(props.children);
    for (const childId of children) {
      const child = this.renderComponent(childId);
      if (child) el.appendChild(child);
    }
    return el;
  }

  private renderRow(props: Record<string, unknown>): HTMLElement {
    const el = document.createElement("div");
    el.className = "a2ui-row";
    const children = this.resolveChildren(props.children);
    for (const childId of children) {
      const child = this.renderComponent(childId);
      if (child) el.appendChild(child);
    }
    return el;
  }

  private renderTextField(props: Record<string, unknown>): HTMLElement {
    const wrapper = document.createElement("div");
    wrapper.className = "a2ui-textfield";
    const label = this.resolveText(props.label);
    if (label) {
      const lbl = document.createElement("label");
      lbl.textContent = label;
      wrapper.appendChild(lbl);
    }
    const input = document.createElement("input");
    input.type = "text";
    wrapper.appendChild(input);
    return wrapper;
  }

  private renderFallback(type: string, id: string): HTMLElement {
    const el = document.createElement("div");
    el.className = "a2ui-unknown";
    el.textContent = `[${type}: ${id}]`;
    return el;
  }

  // -----------------------------------------------------------------------
  // Helpers
  // -----------------------------------------------------------------------

  private resolveText(textProp: unknown): string {
    if (!textProp || typeof textProp !== "object") return String(textProp ?? "");
    const obj = textProp as Record<string, unknown>;
    if (obj.literalString) return obj.literalString as string;
    if (obj.path) return `{{${obj.path}}}`;
    return "";
  }

  private resolveChildren(childrenProp: unknown): string[] {
    if (!childrenProp || typeof childrenProp !== "object") return [];
    const obj = childrenProp as Record<string, unknown>;
    if (obj.explicitList) return obj.explicitList as string[];
    return [];
  }
}
