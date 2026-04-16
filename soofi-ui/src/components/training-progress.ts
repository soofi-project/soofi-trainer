import { LitElement, html, css, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { tr, type Language } from "../i18n.js";

interface JobPhase {
  name: string;
  status: string;
  progress: number;
  started_at: string | null;
  completed_at: string | null;
}

interface Job {
  id: string;
  method: string;
  dataset_ref: string;
  base_model: string;
  config: Record<string, unknown>;
  status: string;
  current_phase: string | null;
  phases: JobPhase[];
  created_at: string;
  updated_at: string;
  error: string | null;
  result: { model_ref?: string; metrics?: Record<string, unknown> } | null;
  container_id: string | null;
}

const TERMINAL_STATUSES = new Set(["completed", "failed", "cancelled"]);
const RECENT_THRESHOLD_MS = 5 * 60 * 1000; // 5 minutes

@customElement("soofi-training-progress")
export class TrainingProgress extends LitElement {
  @property({ type: String }) language: Language = "de";
  @property({ type: Boolean }) visible = false;

  @state() private jobs: Job[] = [];
  @state() private polling = false;

  private _pollTimer: ReturnType<typeof setInterval> | null = null;
  // Consecutive fetches with all jobs terminal. Polling only auto-stops after
  // a grace period so a newly-submitted job has time to appear in the gateway.
  private _allTerminalStreak = 0;
  private static readonly ALL_TERMINAL_STOP_AFTER = 8; // ~24s at 3s interval

  static styles = css`
    :host {
      display: block;
    }
    .jobs-list {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .job-card {
      border: 1px solid var(--color-border, #dadce0);
      border-radius: 8px;
      background: var(--color-surface, #fff);
      overflow: hidden;
    }
    .job-header {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 10px 12px;
      font-size: 13px;
    }
    .job-id {
      font-family: monospace;
      font-size: 12px;
      color: var(--color-text-secondary, #5f6368);
    }
    .job-method {
      font-weight: 600;
      text-transform: uppercase;
      font-size: 12px;
    }
    .job-model {
      color: var(--color-text-secondary, #5f6368);
      font-size: 12px;
    }
    .badge {
      margin-left: auto;
      padding: 2px 8px;
      border-radius: 10px;
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      white-space: nowrap;
    }
    .badge--running { background: #dbeafe; color: #1d4ed8; animation: pulse 2s ease-in-out infinite; }
    .badge--completed { background: #dcfce7; color: #166534; }
    .badge--failed { background: #fee2e2; color: #991b1b; }
    .badge--cancelled { background: #f3f4f6; color: #6b7280; }
    .badge--queued { background: #fef9c3; color: #854d0e; }

    .job-detail {
      padding: 2px 12px 6px;
      font-size: 12px;
      color: var(--color-text-secondary, #5f6368);
    }
    .phases {
      padding: 0 12px 10px;
    }
    .phase-row {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 4px 0;
      font-size: 12px;
    }
    .phase-num {
      width: 18px;
      height: 18px;
      border-radius: 50%;
      background: #e5e7eb;
      color: #6b7280;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 10px;
      font-weight: 600;
      flex-shrink: 0;
    }
    .phase-num--running { background: #dbeafe; color: #1d4ed8; }
    .phase-num--completed { background: #dcfce7; color: #166534; }
    .phase-num--failed { background: #fee2e2; color: #991b1b; }
    .phase-name {
      width: 110px;
      flex-shrink: 0;
    }
    .progress-bar {
      flex: 1;
      height: 6px;
      background: #e5e7eb;
      border-radius: 3px;
      overflow: hidden;
    }
    .progress-bar__fill {
      height: 100%;
      border-radius: 3px;
      transition: width 0.3s ease;
    }
    .progress-bar__fill--pending { width: 0; }
    .progress-bar__fill--running { background: #3b82f6; }
    .progress-bar__fill--completed { background: #22c55e; width: 100% !important; }
    .progress-bar__fill--failed { background: #ef4444; }
    .phase-icon {
      width: 16px;
      text-align: center;
      flex-shrink: 0;
    }
    .metrics-row {
      padding: 2px 0 2px 30px;
      font-size: 11px;
      color: var(--color-text-secondary, #5f6368);
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
    }

    .error-text {
      padding: 4px 12px 10px;
      font-size: 12px;
      color: #991b1b;
    }

    .empty {
      text-align: center;
      color: var(--color-text-secondary, #5f6368);
      font-size: 13px;
      padding: 24px 12px;
    }

    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.5; }
    }
  `;

  disconnectedCallback(): void {
    super.disconnectedCallback();
    this._stopPolling();
  }

  updated(changed: Map<string, unknown>): void {
    if (changed.has("visible")) {
      if (this.visible && !this.polling) {
        this._startPolling();
      } else if (!this.visible) {
        this._stopPolling();
      }
    }
  }

  /** Force an immediate re-poll — call when a new job may have just started
   *  while the panel is already visible (polling may have stopped after all
   *  prior jobs reached a terminal state). */
  public refresh(): void {
    if (!this.visible) return;
    // Reset grace period — a user/agent action just opened or refreshed the
    // panel, so a new job may be imminent. Give it time to materialize.
    this._allTerminalStreak = 0;
    if (this._pollTimer) {
      this._fetchJobs();
    } else {
      this._startPolling();
    }
  }

  private _startPolling(): void {
    if (this._pollTimer) return;
    this.polling = true;
    this._allTerminalStreak = 0;
    this._fetchJobs();
    this._pollTimer = setInterval(() => this._fetchJobs(), 3000);
  }

  private _stopPolling(): void {
    if (this._pollTimer) {
      clearInterval(this._pollTimer);
      this._pollTimer = null;
    }
    this.polling = false;
  }

  private async _fetchJobs(): Promise<void> {
    try {
      const resp = await fetch("/api/training/jobs");
      if (!resp.ok) return;
      const allJobs: Job[] = await resp.json();

      // Only show active jobs + recently finished ones (< 5 min)
      const now = Date.now();
      this.jobs = allJobs.filter((j) => {
        if (!TERMINAL_STATUSES.has(j.status)) return true;
        const updatedAt = new Date(j.updated_at).getTime();
        return now - updatedAt < RECENT_THRESHOLD_MS;
      });

      // Stop polling only after several consecutive all-terminal fetches —
      // otherwise a freshly-submitted job (not yet in the DB at first poll)
      // would be missed because polling stopped on the first empty/terminal
      // fetch before the gateway created the record.
      const anyActive = allJobs.some((j) => !TERMINAL_STATUSES.has(j.status));
      if (anyActive) {
        this._allTerminalStreak = 0;
      } else {
        this._allTerminalStreak += 1;
        if (this._allTerminalStreak >= TrainingProgress.ALL_TERMINAL_STOP_AFTER) {
          this._stopPolling();
        }
      }
    } catch {
      // Silently ignore fetch errors — gateway may be down
    }
  }

  private _shortId(id: string): string {
    return id.slice(0, 8);
  }

  private _phaseIcon(status: string): string {
    switch (status) {
      case "completed": return "\u2713";
      case "failed": return "\u2717";
      case "running": return "\u25CB";
      default: return "\u00B7";
    }
  }

  private _phaseName(name: string): string {
    return tr(`phase_${name}`, this.language);
  }

  private _formatDuration(start: string | null, end: string | null): string {
    if (!start) return "";
    const s = new Date(start).getTime();
    const e = end ? new Date(end).getTime() : Date.now();
    const secs = Math.round((e - s) / 1000);
    if (secs < 60) return `${secs}s`;
    const mins = Math.floor(secs / 60);
    const rem = secs % 60;
    return `${mins}m ${rem}s`;
  }

  render() {
    if (!this.visible) return nothing;

    if (this.jobs.length === 0) {
      return html`<div class="empty">${tr("training_no_jobs", this.language)}</div>`;
    }

    return html`
      <div class="jobs-list">
        ${this.jobs.map((job) => this._renderJob(job))}
      </div>
    `;
  }

  private _renderJob(job: Job) {
    if (TERMINAL_STATUSES.has(job.status)) {
      return html`
        <details class="job-card">
          <summary class="job-header" style="cursor:pointer;list-style:none">
            <span class="job-id">${this._shortId(job.id)}</span>
            <span class="job-method">${job.method}</span>
            <span class="job-model">${job.base_model}</span>
            <span class="badge badge--${job.status}">${tr(`status_${job.status}`, this.language)}</span>
          </summary>
          <div class="job-detail">${tr("training_dataset", this.language)}: ${job.dataset_ref}</div>
          <div class="phases">
            ${job.phases.map((phase, i) => this._renderPhase(phase, i, job))}
          </div>
          ${job.error ? html`<div class="error-text">${job.error}</div>` : nothing}
        </details>
      `;
    }

    return html`
      <div class="job-card">
        <div class="job-header">
          <span class="job-id">${this._shortId(job.id)}</span>
          <span class="job-method">${job.method}</span>
          <span class="job-model">${job.base_model}</span>
          <span class="badge badge--${job.status}">${tr(`status_${job.status}`, this.language)}</span>
        </div>
        <div class="job-detail">${tr("training_dataset", this.language)}: ${job.dataset_ref}</div>
        <div class="phases">
          ${job.phases.map((phase, i) => this._renderPhase(phase, i, job))}
        </div>
        ${job.error ? html`<div class="error-text">${job.error}</div>` : nothing}
      </div>
    `;
  }

  private _renderPhase(phase: JobPhase, index: number, job: Job) {
    const metrics = (job.config as Record<string, unknown>)?.phase_metrics as
      | Record<string, Record<string, unknown>>
      | undefined;
    const phaseMetrics = metrics?.[phase.name];

    return html`
      <div class="phase-row">
        <span class="phase-num phase-num--${phase.status}">${index + 1}</span>
        <span class="phase-name">${this._phaseName(phase.name)}</span>
        <div class="progress-bar">
          <div
            class="progress-bar__fill progress-bar__fill--${phase.status}"
            style="width:${phase.status === "completed" ? 100 : phase.progress}%"
          ></div>
        </div>
        <span class="phase-icon">${this._phaseIcon(phase.status)}</span>
      </div>
      ${phase.status === "running" && phaseMetrics
        ? html`<div class="metrics-row">
            ${phaseMetrics.epoch != null
              ? html`<span>${tr("metric_epoch", this.language)}: ${phaseMetrics.epoch}</span>`
              : nothing}
            ${phaseMetrics.loss != null
              ? html`<span>${tr("metric_loss", this.language)}: ${Number(phaseMetrics.loss).toFixed(4)}</span>`
              : nothing}
            ${phaseMetrics.eta
              ? html`<span>${tr("metric_eta", this.language)}: ${phaseMetrics.eta}</span>`
              : nothing}
            ${phase.started_at
              ? html`<span>${tr("metric_duration", this.language)}: ${this._formatDuration(phase.started_at, null)}</span>`
              : nothing}
          </div>`
        : nothing}
    `;
  }
}
