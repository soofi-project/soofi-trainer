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
  agent_field_version: { de: "Version", en: "Version" },
  agent_field_protocol: { de: "Protokoll", en: "Protocol" },
  agent_field_transport: { de: "Transport", en: "Transport" },
  agent_field_streaming: { de: "Streaming", en: "Streaming" },
  agent_field_input: { de: "Input", en: "Input" },
  agent_field_output: { de: "Output", en: "Output" },
  agent_field_skills: { de: "Skills", en: "Skills" },

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
