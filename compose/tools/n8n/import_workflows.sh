#!/bin/bash

docker compose exec n8n sh init_script.sh
docker compose restart n8n
