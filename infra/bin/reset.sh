#!/usr/bin/env bash
# reset.sh — полный сброс Solana-сети (ledger, logs, state)
# Путь: /opt/docker/chain-prod/bin/reset.sh
# ВНИМАНИЕ: удаляет ledger и state, но сохраняет ключи
set -eu

ROOT_DIR="/opt/docker/chain-prod"
COMPOSE_FILE="${ROOT_DIR}/docker-compose.solana.yml"
ENV_FILE="${ROOT_DIR}/.env"

echo "=== GDM Solana — RESET ==="
echo "[!] This will stop containers and wipe ledger + state (keys preserved)"
printf "Continue? [y/N] "
read -r CONFIRM
if [ "${CONFIRM}" != "y" ] && [ "${CONFIRM}" != "Y" ]; then
  echo "[abort] reset cancelled"
  exit 0
fi

echo "[*] stopping containers..."
docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" down 2>/dev/null || true

echo "[*] removing containers by name (if orphaned)..."
docker rm -f gdm-solana-validator gdm-solana-tools gdm-solana-bridge 2>/dev/null || true

echo "[*] wiping ledger..."
rm -rf "${ROOT_DIR}/ledger"/*

echo "[*] wiping logs..."
rm -rf "${ROOT_DIR}/logs"/*

echo "[*] wiping state/deploy.json..."
rm -f "${ROOT_DIR}/state/deploy.json"
rm -f "${ROOT_DIR}/config/solana.local.generated.yml"

echo "[ok] reset complete. Keys preserved in ${ROOT_DIR}/keys/"
echo ""
echo "Run 'sh /opt/docker/chain-prod/bin/up.sh' to start fresh"
