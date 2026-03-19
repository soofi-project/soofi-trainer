#!/bin/sh
set -e
for file in import-workflows/*.json; do
  # extract ID out of file
  ID=$(node -e "console.log(require('/home/node/$file').id)")
  echo "Importing and publishing ID: $ID"
  n8n import:workflow --input="$file"
  n8n publish:workflow --id="$ID"
done
touch /tmp/done