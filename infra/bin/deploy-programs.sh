#!/usr/bin/env bash
set -eu

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
KEYS_DIR="${ROOT_DIR}/keys"
STATE_DIR="${ROOT_DIR}/state"
CONFIG_DIR="${ROOT_DIR}/config"

RPC_URL="${RPC_URL:-http://gdm-solana-validator:8899}"
WS_URL="${WS_URL:-ws://gdm-solana-validator:8900}"
FAUCET_URL="${FAUCET_URL:-http://gdm-solana-validator:9900}"
PAYER_KEYPAIR="${KEYS_DIR}/payer.json"
CONTRACT_KP="${KEYS_DIR}/contract-program-keypair.json"
DOCUMENT_KP="${KEYS_DIR}/document-program-keypair.json"
CONTRACT_SO="${ROOT_DIR}/artifacts/contract_state.so"
DOCUMENT_SO="${ROOT_DIR}/artifacts/document_verification.so"

mkdir -p "${STATE_DIR}" "${CONFIG_DIR}"

solana config set --url "${RPC_URL}" >/dev/null

if [ ! -f "${PAYER_KEYPAIR}" ]; then
  echo "[error] missing payer keypair: ${PAYER_KEYPAIR}"
  exit 1
fi

if [ ! -f "${CONTRACT_KP}" ]; then
  echo "[error] missing contract program keypair: ${CONTRACT_KP}"
  exit 1
fi

if [ ! -f "${DOCUMENT_KP}" ]; then
  echo "[error] missing document program keypair: ${DOCUMENT_KP}"
  exit 1
fi

if [ ! -f "${CONTRACT_SO}" ]; then
  echo "[error] missing contract artifact: ${CONTRACT_SO}"
  echo "[hint] run build-programs.sh first"
  exit 1
fi

if [ ! -f "${DOCUMENT_SO}" ]; then
  echo "[error] missing document artifact: ${DOCUMENT_SO}"
  echo "[hint] run build-programs.sh first"
  exit 1
fi

echo "[deploy] contract_state.so"
solana program deploy \
  --url "${RPC_URL}" \
  --keypair "${PAYER_KEYPAIR}" \
  --program-id "${CONTRACT_KP}" \
  "${CONTRACT_SO}"

echo

echo "[deploy] document_verification.so"
solana program deploy \
  --url "${RPC_URL}" \
  --keypair "${PAYER_KEYPAIR}" \
  --program-id "${DOCUMENT_KP}" \
  "${DOCUMENT_SO}"

CONTRACT_ID="$(solana-keygen pubkey "${CONTRACT_KP}")"
DOCUMENT_ID="$(solana-keygen pubkey "${DOCUMENT_KP}")"

cat > "${STATE_DIR}/deploy.json" <<EOF
{
  "rpc_url": "${RPC_URL}",
  "contract_program_id": "${CONTRACT_ID}",
  "document_program_id": "${DOCUMENT_ID}"
}
EOF

cat > "${CONFIG_DIR}/solana.local.generated.yml" <<EOF
solana:
  network: local
  rpc_url: ${RPC_URL}
  ws_url: ${WS_URL}
  faucet_url: ${FAUCET_URL}
  commitment: confirmed

  ledger_path: ./ledger
  logs_path: ./logs
  keys_path: ./keys
  state_path: ./state

  keypairs:
    payer: ./keys/payer.json
    authority: ./keys/authority.json

  program_keypairs:
    contract: ./keys/contract-program-keypair.json
    document: ./keys/document-program-keypair.json

  program_artifacts:
    contract: ./artifacts/contract_state.so
    document: ./artifacts/document_verification.so

  program_ids:
    contract: ${CONTRACT_ID}
    document: ${DOCUMENT_ID}
EOF

echo "[ok] deploy complete"
cat "${STATE_DIR}/deploy.json"
