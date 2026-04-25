#!/usr/bin/env bash
# down.sh — остановить всю Solana-сеть
# Путь: /opt/docker/chain-prod/bin/down.sh
set -eu

ROOT_DIR="/opt/docker/chain-prod"
COMPOSE_FILE="${ROOT_DIR}/docker-compose.solana.yml"
ENV_FILE="${ROOT_DIR}/.env"

echo "=== GDM Solana — DOWN ==="
docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" down
echo "[ok] all containers stopped"
