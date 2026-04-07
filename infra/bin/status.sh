#!/usr/bin/env bash
# status.sh — статус Solana-сети
# Путь: /opt/docker/chain-prod/bin/status.sh
set -eu

ROOT_DIR="/opt/docker/chain-prod"
RPC="http://127.0.0.1:8899"

echo "=== GDM Solana — STATUS ==="
echo ""

echo "[containers]"
docker ps --filter "name=gdm-solana" --format "  {{.Names}}\t{{.Status}}" 2>/dev/null || echo "  (docker not available)"

echo ""
echo "[rpc health]"
HEALTH=$(curl -sf -X POST "${RPC}" \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"getHealth"}' 2>/dev/null || echo '{"error":"no response"}')
echo "  ${HEALTH}"

echo ""
echo "[slot]"
SLOT=$(curl -sf -X POST "${RPC}" \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"getSlot"}' 2>/dev/null || echo '{"error":"no response"}')
echo "  ${SLOT}"

echo ""
echo "[version]"
VER=$(curl -sf -X POST "${RPC}" \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"getVersion"}' 2>/dev/null || echo '{"error":"no response"}')
echo "  ${VER}"

echo ""
echo "[deploy state]"
STATE_FILE="${ROOT_DIR}/state/deploy.json"
if [ -f "${STATE_FILE}" ]; then
  cat "${STATE_FILE}"
else
  echo "  (no deploy.json yet — programs not deployed)"
fi

echo ""
echo "[artifacts]"
ARTIFACTS_DIR="${ROOT_DIR}/artifacts"
if [ -f "${ARTIFACTS_DIR}/contract_state.so" ]; then
  echo "  contract_state.so    OK"
else
  echo "  contract_state.so    MISSING"
fi
if [ -f "${ARTIFACTS_DIR}/document_verification.so" ]; then
  echo "  document_verification.so    OK"
else
  echo "  document_verification.so    MISSING"
fi

echo ""
echo "[keys]"
KEYS_DIR="${ROOT_DIR}/keys"
for k in payer.json authority.json contract-program-keypair.json document-program-keypair.json; do
  if [ -f "${KEYS_DIR}/${k}" ]; then
    echo "  ${k}    OK"
  else
    echo "  ${k}    MISSING"
  fi
done
