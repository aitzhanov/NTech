#!/usr/bin/env bash
set -euo pipefail

RPC_URL="http://127.0.0.1:8899"

echo "[check] RPC health"
curl -s -X POST ${RPC_URL} \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"getHealth"}'

echo

echo "[check] slot"
curl -s -X POST ${RPC_URL} \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"getSlot"}'

echo

echo "[ok] validator responding"
