#!/bin/sh
set -e

TEMPLATES_DIR="/slides-templates"
OUTPUT_DIR="/usr/share/nginx/html/slides"
POLL_INTERVAL=2

checksum() {
    find "$TEMPLATES_DIR" -name "*.md" | sort | xargs md5sum 2>/dev/null
}

render() {
    mkdir -p "$OUTPUT_DIR"
    for f in "$TEMPLATES_DIR"/*.md; do
        out="$OUTPUT_DIR/$(basename "$f")"
        envsubst < "$f" > "$out"
        echo "[landingpage] rendered: $(basename "$out")"
    done
}

render

if [ "${LANDING_PAGE_WATCH_SLIDES:-false}" = "true" ]; then
    echo "[landingpage] watching $TEMPLATES_DIR for changes (poll every ${POLL_INTERVAL}s)..."
    last="$(checksum)"
    (
        while true; do
            sleep "$POLL_INTERVAL"
            current="$(checksum)"
            if [ "$current" != "$last" ]; then
                render
                last="$current"
            fi
        done
    ) &
fi

exec "$@"
