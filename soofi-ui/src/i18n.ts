/**
 * Minimal i18n for the Soofi UI — DE/EN runtime toggle.
 * All keys used in main.ts are defined here.
 */

export type Language = "de" | "en";

const strings: Record<string, Record<Language, string>> = {
  // Header / input
  placeholder: { de: "Nachricht eingeben\u2026", en: "Type a message\u2026" },
  send: { de: "Senden", en: "Send" },
  ptt_hold: { de: "Gedrückt halten zum Sprechen", en: "Hold to speak" },
  ptt_toggle: { de: "Klicken zum Starten/Stoppen", en: "Click to start/stop" },

  // Status / search bar
  thinking: { de: "Überlege", en: "Thinking" },
  recording: { de: "Aufnahme läuft\u2026", en: "Recording\u2026" },

  // Dashboard card
  open_dashboard: { de: "öffnen", en: "open" },

  // Doc viewer
  doc_load_error: { de: "Fehler beim Laden", en: "Error loading" },
  doc_load_error_generic: { de: "Fehler beim Laden des Dokuments.", en: "Error loading document." },

  // Agent cards
  agent_cards: { de: "Agentenkarten", en: "Agent Cards" },
  agent_offline: { de: "Nicht erreichbar", en: "Unreachable" },
  agent_offline_msg: {
    de: "Dieser Agent ist derzeit nicht verfügbar.",
    en: "This agent is currently unavailable.",
  },
  streaming_yes: { de: "Ja", en: "Yes" },
  streaming_no: { de: "Nein", en: "No" },

  // Reset dialog
  reset_title: { de: "Gespräch zurücksetzen?", en: "Reset conversation?" },
  reset_body: {
    de: "Das aktuelle Gespräch wird gelöscht und eine neue Session gestartet.",
    en: "The current conversation will be cleared and a new session started.",
  },
  reset_confirm: { de: "Zurücksetzen", en: "Reset" },
  reset_cancel: { de: "Abbrechen", en: "Cancel" },

  // Training progress
  training_jobs: { de: "Trainingsaufträge", en: "Training Jobs" },
  training_dataset: { de: "Datensatz", en: "Dataset" },
  training_no_jobs: { de: "Keine Trainingsaufträge", en: "No training jobs" },
  // Training status labels
  status_running: { de: "Läuft", en: "Running" },
  status_completed: { de: "Abgeschlossen", en: "Completed" },
  status_failed: { de: "Fehlgeschlagen", en: "Failed" },
  status_cancelled: { de: "Abgebrochen", en: "Cancelled" },
  status_queued: { de: "Wartend", en: "Queued" },
  // Training phase names
  phase_data_preparation: { de: "Datenvorbereitung", en: "Data Preparation" },
  phase_training: { de: "Training", en: "Training" },
  phase_model_upload: { de: "Modell-Upload", en: "Model Upload" },
  // Training metric labels
  metric_epoch: { de: "Epoche", en: "Epoch" },
  metric_loss: { de: "Verlust", en: "Loss" },
  metric_eta: { de: "Verbleibend", en: "ETA" },
  metric_duration: { de: "Dauer", en: "Duration" },

  // Errors
  error_prefix: { de: "Fehler", en: "Error" },
  error_unknown: { de: "Unbekannter Fehler", en: "Unknown error" },
  error_processing: { de: "Fehler bei der Verarbeitung", en: "Error during processing" },
};

/**
 * Translate a key to the given language.
 * Falls back to DE if the key is unknown.
 */
export function tr(key: string, lang: Language): string {
  return strings[key]?.[lang] ?? strings[key]?.de ?? key;
}
