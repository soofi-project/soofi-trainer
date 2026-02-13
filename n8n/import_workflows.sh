#!/bin/bash
set -e
set -a 
source $(pwd)/.env
set +a

docker run --rm \
  --network soofi-network \
  -e DB_TYPE=postgresdb \
  -e DB_POSTGRESDB_HOST=postgres \
  -e DB_POSTGRESDB_DATABASE="$POSTGRES_DB" \
  -e DB_POSTGRESDB_USER="$POSTGRES_USER" \
  -e DB_POSTGRESDB_PASSWORD="$POSTGRES_PASSWORD" \
  -v "$(pwd)/n8n/workflows:/import-workflows:ro" \
  -v "$(pwd)/n8n/init_script.sh:/init_script.sh:ro" \
  --entrypoint sh \
  n8nio/n8n:2.7.3 \
  -c "sh /init_script.sh"

echo "Import complete, restarting n8n..."
docker restart n8n

echo "Done! n8n restarted with imported workflows."
