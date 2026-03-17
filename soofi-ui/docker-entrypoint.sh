#!/bin/sh
# Generate runtime config from environment variables.
# This allows changing VITE_* settings without rebuilding the image.
cat > /usr/share/nginx/html/env.js <<EOF
window.__ENV = {
  VITE_VOICE_CONTROLS_VISIBLE: "${VITE_VOICE_CONTROLS_VISIBLE:-true}",
  VITE_VOICE_ACTIVATION: "${VITE_VOICE_ACTIVATION:-push-to-talk}",
  VITE_TTS_VOICE_DE: "${VITE_TTS_VOICE_DE:-alloy}",
  VITE_TTS_VOICE_EN: "${VITE_TTS_VOICE_EN:-onyx}",
};
EOF

exec nginx -g 'daemon off;'
