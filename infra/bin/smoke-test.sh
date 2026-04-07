#!/usr/bin/env bash
# smoke-test.sh — E2E проверка: validator + programs + bridge
# Путь: /opt/docker/chain-prod/bin/smoke-test.sh
set -eu

ROOT_DIR="/opt/docker/chain-prod"
RPC="http://127.0.0.1:8899"
BRIDGE="http://127.0.0.1:8080"
STATE_FILE="${ROOT_DIR}/state/deploy.json"

echo "=== GDM Solana — SMOKE TEST ==="
echo ""

PASS=0
FAIL=0

check() {
  LABEL="$1"
  RESULT="$2"
  EXPECT="$3"
  if echo "${RESULT}" | grep -q "${EXPECT}"; then
    echo "  [PASS] ${LABEL}"
    PASS=$((PASS + 1))
  else
    echo "  [FAIL] ${LABEL}"
    echo "         got: ${RESULT}"
    FAIL=$((FAIL + 1))
  fi
}

# 1. Validator health
echo "[1] Validator RPC..."
R=$(curl -sf -X POST "${RPC}" \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"getHealth"}' 2>/dev/null || echo 'error')
check "getHealth" "${R}" "ok"

# 2. Slot advancing
echo "[2] Slot..."
R=$(curl -sf -X POST "${RPC}" \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"getSlot"}' 2>/dev/null || echo 'error')
check "getSlot" "${R}" "result"

# 3. Programs deployed
echo "[3] Deploy state..."
if [ -f "${STATE_FILE}" ]; then
  CONTRACT_ID=$(python3 -c "import json,sys; d=json.load(open('${STATE_FILE}')); print(d.get('contract_program_id',''))" 2>/dev/null || echo "")
  DOCUMENT_ID=$(python3 -c "import json,sys; d=json.load(open('${STATE_FILE}')); print(d.get('document_program_id',''))" 2>/dev/null || echo "")

  if [ -n "${CONTRACT_ID}" ] && [ "${CONTRACT_ID}" != "null" ]; then
    echo "  [PASS] contract_program_id: ${CONTRACT_ID}"
    PASS=$((PASS + 1))
  else
    echo "  [FAIL] contract_program_id missing"
    FAIL=$((FAIL + 1))
  fi

  if [ -n "${DOCUMENT_ID}" ] && [ "${DOCUMENT_ID}" != "null" ]; then
    echo "  [PASS] document_program_id: ${DOCUMENT_ID}"
    PASS=$((PASS + 1))
  else
    echo "  [FAIL] document_program_id missing"
    FAIL=$((FAIL + 1))
  fi

  # 4. Verify programs exist on chain
  echo "[4] Programs on-chain..."
  for PID in "${CONTRACT_ID}" "${DOCUMENT_ID}"; do
    if [ -z "${PID}" ] || [ "${PID}" = "null" ]; then continue; fi
    R=$(curl -sf -X POST "${RPC}" \
      -H 'Content-Type: application/json' \
      -d "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"getAccountInfo\",\"params\":[\"${PID}\",{\"encoding\":\"base64\"}]}" \
      2>/dev/null || echo 'error')
    check "program ${PID:0:8}..." "${R}" "result"
  done
else
  echo "  [SKIP] deploy.json not found — programs not deployed yet"
fi

# 5. Bridge health (optional)
echo "[5] Bridge..."
B=$(curl -sf "${BRIDGE}/health" 2>/dev/null || echo 'not running')
if echo "${B}" | grep -q "ok\|healthy\|200"; then
  echo "  [PASS] bridge responding"
  PASS=$((PASS + 1))
else
  echo "  [INFO] bridge not responding (may not be started)"
fi

echo ""
echo "=== RESULT: ${PASS} passed, ${FAIL} failed ==="
if [ "${FAIL}" -gt 0 ]; then
  exit 1
fi
