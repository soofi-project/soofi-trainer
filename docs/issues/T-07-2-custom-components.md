# Task

- user story: #US-07
- depends on: #T-07-1

/label ~UserStory_US-07
/label ~Task
/label ~ToDo

# Description

**Custom Components & Theming**

Register custom Soofi components via A2UI's `componentRegistry.register()` and apply branding/theming to the frontend.

## Custom Component Catalog

### `soofi-logo`
- SVG logo with animation states:
  - **idle**: static logo display
  - **processing**: pulsating animation (triggered when agent is thinking/generating)
  - **error**: visual error indication (e.g. red tint, shake)
- Interaction Agent (T-07-6) controls the state via A2UI messages

### `voice-controls`
- Audio level indicator (visualizes input volume while recording)
- Playback controls (play/pause/stop for TTS audio output)
- Integrates with voice pipeline from T-07-3
- **Visibility configurable** via env var `VOICE_CONTROLS_VISIBLE=true|false` — in demo setups (Hannover Messe) the mic is always on with a physical mute button on the hardware mic, so on-screen controls are unnecessary and awkward without a touchscreen. For development with a laptop, the on-screen controls are useful.

### `dashboard-embed`
- iframe wrapper for embedding external dashboards
- Configurable URL, dimensions, and loading state
- Used by T-07-5 for Grafana, Langfuse, and other dashboard embedding
- Interaction Agent (T-07-6) decides when and what dashboard to show based on conversation context

## Theming & Branding

- Soofi color palette, typography, and layout
- Consistent branding across all components
- Responsive layout for demo screens (large display) and development (laptop)

## Prototyping

- Use A2UI Composer for rapid prototyping of component layouts
- Validate rendering of custom components with sample A2UI payloads

## Acceptance Criteria

- [ ] `soofi-logo` component registered and renders with idle/processing/error states
- [ ] `voice-controls` component registered with audio level indicator and playback controls
- [ ] `voice-controls` visibility configurable via `VOICE_CONTROLS_VISIBLE` env var
- [ ] `dashboard-embed` component registered and can embed external URLs via iframe
- [ ] All custom components are registered via `componentRegistry.register()`
- [ ] Soofi theming applied (colors, fonts, layout)
- [ ] Components respond to A2UI messages from the Interaction Agent
- [ ] Layout works on large demo screens and laptop displays

# Branches

- feature/T-07-2-custom-components
