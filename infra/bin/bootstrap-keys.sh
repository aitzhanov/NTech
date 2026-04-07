#!/usr/bin/env bash
set -eu

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
KEYS_DIR="${ROOT_DIR}/keys"
STATE_DIR="${ROOT_DIR}/state"

mkdir -p "${KEYS_DIR}" "${STATE_DIR}"
chmod 700 "${KEYS_DIR}" 2>/dev/null || true

create_key_if_missing() {
  target="$1"
  if [ -f "${target}" ]; then
    echo "[skip] exists: ${target}"
    return 0
  fi
  solana-keygen new --no-bip39-passphrase -o "${target}" >/dev/null
  chmod 600 "${target}" 2>/dev/null || true
  echo "[ok] created: ${target}"
}

create_key_if_missing "${KEYS_DIR}/payer.json"
create_key_if_missing "${KEYS_DIR}/authority.json"
create_key_if_missing "${KEYS_DIR}/contract-program-keypair.json"
create_key_if_missing "${KEYS_DIR}/document-program-keypair.json"

cat > "${STATE_DIR}/keypairs.json" <<EOF
{
  "payer": "$(solana-keygen pubkey "${KEYS_DIR}/payer.json")",
  "authority": "$(solana-keygen pubkey "${KEYS_DIR}/authority.json")",
  "contract_program": "$(solana-keygen pubkey "${KEYS_DIR}/contract-program-keypair.json")",
  "document_program": "$(solana-keygen pubkey "${KEYS_DIR}/document-program-keypair.json")"
}
EOF

echo "[ok] keypairs ready"
cat "${STATE_DIR}/keypairs.json"
