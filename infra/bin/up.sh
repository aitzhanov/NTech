#!/usr/bin/env bash
# up.sh — поднять всю Solana-сеть
# Путь: /opt/docker/chain-prod/bin/up.sh
set -eu

ROOT_DIR="/opt/docker/chain-prod"
COMPOSE_FILE="${ROOT_DIR}/docker-compose.solana.yml"
ENV_FILE="${ROOT_DIR}/.env"

echo "=== GDM Solana — UP ==="
echo "[*] root: ${ROOT_DIR}"

# Создаём нужные директории если нет
mkdir -p \
  "${ROOT_DIR}/ledger" \
  "${ROOT_DIR}/logs" \
  "${ROOT_DIR}/keys" \
  "${ROOT_DIR}/config" \
  "${ROOT_DIR}/state" \
  "${ROOT_DIR}/artifacts" \
  "${ROOT_DIR}/bin"

chmod 700 "${ROOT_DIR}/keys" 2>/dev/null || true

echo "[*] starting containers..."
docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" up -d --build

echo "[*] waiting for validator health..."
RETRIES=30
i=0
while [ $i -lt $RETRIES ]; do
  STATUS=$(curl -sf -X POST http://127.0.0.1:8899 \
    -H 'Content-Type: application/json' \
    -d '{"jsonrpc":"2.0","id":1,"method":"getHealth"}' 2>/dev/null | grep -c '"ok"' || true)
  if [ "${STATUS}" = "1" ]; then
    echo "[ok] validator is healthy"
    break
  fi
  i=$((i + 1))
  echo "[wait] ${i}/${RETRIES}..."
  sleep 3
done

if [ $i -eq $RETRIES ]; then
  echo "[error] validator did not become healthy in time"
  exit 1
fi

echo ""
echo "=== Validator is UP ==="
echo "  RPC:    http://127.0.0.1:8899"
echo "  WS:     ws://127.0.0.1:8900"
echo "  Faucet: http://127.0.0.1:9900"
echo ""
echo "Next steps:"
echo "  1. docker exec -it gdm-solana-tools sh -lc 'sh /solana/bin/bootstrap-keys.sh'"
echo "  2. docker exec -it gdm-solana-tools sh -lc 'sh /solana/bin/bootstrap-wallets.sh'"
echo "  3. [build .so] then: docker exec -it gdm-solana-tools sh -lc 'sh /solana/bin/deploy-programs.sh'"
