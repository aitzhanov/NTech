#!/usr/bin/env bash
set -eu

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
KEYS_DIR="${ROOT_DIR}/keys"

RPC_URL="http://gdm-solana-validator:8899"

solana config set --url "${RPC_URL}" >/dev/null

airdrop_if_needed() {
  keyfile="$1"
  pubkey="$(solana-keygen pubkey "${keyfile}")"

  balance="$(solana balance "${pubkey}" | awk '{print $1}')"

  if [ "$(echo "${balance} < 50" | bc 2>/dev/null || echo 1)" = "1" ]; then
    echo "[airdrop] ${pubkey}"
    solana airdrop 100 "${pubkey}" || true
  else
    echo "[ok] balance sufficient: ${pubkey} (${balance} SOL)"
  fi

  solana balance "${pubkey}"
}

airdrop_if_needed "${KEYS_DIR}/payer.json"
airdrop_if_needed "${KEYS_DIR}/authority.json"

echo "[ok] wallets funded"
