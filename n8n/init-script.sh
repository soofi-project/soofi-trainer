#!/bin/sh
set -e
for file in /import-workflows/*.json; do
  # extract ID out of file
  ID=$(sed -n 's/.*"id":[[:space:]]*\("[^"\\]*\( \\.[^"\\]*\)*"\).*/\1/p' "$file" | tr -d '"' | grep -E '^.{16}$')
  echo "Importing and publishing ID: $ID"
  n8n import:workflow --input="$file"
  n8n publish:workflow --id="$ID"
done
touch /tmp/done