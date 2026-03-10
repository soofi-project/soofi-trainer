# Task

- user story: [US-07](US-07-voice-agent-ui.md)
- depends on: [T-07-6](T-07-6-interaction-agent.md)

/label ~UserStory_US-07
/label ~Task
/label ~Done

# Description

**Session Reset Button for Trade Show Use**

In kiosk/fullscreen mode (e.g. Hannover Messe), there is no browser chrome to
refresh the page between demo sessions. A reset button in the UI header allows
the presenter to clear the conversation and start fresh for the next visitor.

## Implementation

- Reset button (circular refresh icon) in the header, next to the language toggle
- Confirmation dialog with overlay to prevent accidental resets
- On confirm: clears messages, generates new `session_id`, closes doc viewer /
  agent cards / dashboards, stops active recordings, cancels pending TTS,
  resets flow animation state
- New session ID means advisor and training agent start with fresh conversation
  history (memory is keyed by `thread_id` = `session_id`)

## Files Changed

- `soofi-ui/src/main.ts`: Reset button, confirmation dialog, `confirmReset()` method
- `soofi-ui/src/i18n.ts`: 4 new keys (`reset_title`, `reset_body`, `reset_confirm`, `reset_cancel`)

## Acceptance Criteria

1. Reset button visible in header next to language toggle
2. Click opens confirmation dialog with translated text (DE/EN)
3. Confirm clears all UI state and generates new session ID
4. Cancel (button or overlay click) closes dialog without side effects
5. Next message after reset starts a fresh agent conversation
