# GDM Solana — chain-prod

Локальная Solana-сеть для GDM. Базовый путь: `/opt/docker/chain-prod`.

## Структура

```
/opt/docker/chain-prod/
├── docker-compose.solana.yml   # compose для validator + tools + bridge
├── Dockerfile.solana           # образ validator/tools
├── Dockerfile.builder          # образ для сборки Anchor программ
├── .env                        # переменные окружения
├── gdm_solana_programs/        # исходники Anchor программ
├── gdm_solana_bridge/          # исходники Python bridge
├── bin/
│   ├── up.sh                   # поднять сеть
│   ├── down.sh                 # остановить сеть
│   ├── status.sh               # статус (RPC, slot, keys, artifacts)
│   ├── reset.sh                # сброс ledger+state (ключи сохраняются)
│   ├── build-programs.sh       # сборка .so через Docker builder
│   ├── bootstrap-keys.sh       # генерация keypairs
│   ├── bootstrap-wallets.sh    # airdrop SOL на payer/authority
│   ├── deploy-programs.sh      # deploy .so на локальный validator
│   ├── validator-check.sh      # быстрая проверка RPC
│   └── smoke-test.sh           # E2E smoke test
├── config/
│   ├── solana.local.yml        # базовый конфиг
│   └── solana.local.generated.yml  # генерируется после deploy
├── keys/                       # keypairs (gitignored)
├── artifacts/                  # .so файлы (gitignored)
├── ledger/                     # данные validator (gitignored)
├── logs/                       # логи (gitignored)
└── state/
    ├── keypairs.json           # pubkeys всех ключей
    └── deploy.json             # program_ids после deploy
```

## Быстрый старт

### 1. Поднять сеть

```bash
cd /opt/docker/chain-prod
docker compose -f docker-compose.solana.yml up -d --build
```

### 2. Генерация ключей

```bash
docker exec -it gdm-solana-tools sh -lc 'sh /solana/bin/bootstrap-keys.sh'
```

### 3. Пополнить кошельки

```bash
docker exec -it gdm-solana-tools sh -lc 'sh /solana/bin/bootstrap-wallets.sh'
```

### 4. Собрать программы (на хосте)

```bash
sh /opt/docker/chain-prod/bin/build-programs.sh
```

Скрипт автоматически найдёт исходники в `/opt/docker/chain-prod/gdm_solana_programs/`.

Результат:
```
/opt/docker/chain-prod/artifacts/contract_state.so
/opt/docker/chain-prod/artifacts/document_verification.so
```

### 5. Задеплоить программы

```bash
docker exec -it gdm-solana-tools sh -lc 'sh /solana/bin/deploy-programs.sh'
```

После deploy:
- `state/deploy.json` — реальные program_id
- `config/solana.local.generated.yml` — полный конфиг для bridge

### 6. Проверить статус

```bash
sh /opt/docker/chain-prod/bin/status.sh
sh /opt/docker/chain-prod/bin/smoke-test.sh
```

---

## Контейнеры

| Контейнер | Назначение | Порты |
|-----------|-----------|-------|
| `gdm-solana-validator` | Solana localnet validator | 8899 (RPC), 8900 (WS), 9900 (faucet) |
| `gdm-solana-tools` | CLI + deploy + keygen | — |
| `gdm-solana-bridge` | Python HTTP bridge | 8181 |

Сеть: `sactek-prod` (external)

---

## Bridge API

```bash
# Health
curl http://127.0.0.1:8181/health

# Текущий слот
curl http://127.0.0.1:8181/slot

# Баланс
curl http://127.0.0.1:8181/balance/<pubkey>

# Отправить транзакцию
curl -X POST http://127.0.0.1:8181/tx/send \
  -H 'Content-Type: application/json' \
  -d '{"type":"transfer","to":"<pubkey>","lamports":1000000}'

# Проверить транзакцию
curl http://127.0.0.1:8181/tx/<signature>
```

---

## Переменные окружения (.env)

| Переменная | Описание |
|-----------|---------|
| `SOLANA_RPC_URL` | RPC endpoint (inter-container) |
| `SOLANA_WS_URL` | WebSocket endpoint |
| `SOLANA_COMMITMENT` | confirmed / finalized |
| `CHAIN_ROOT` | `/opt/docker/chain-prod` |
| `SOLANA_PAYER_KEYPAIR` | путь к payer.json |
| `BRIDGE_PORT` | порт bridge на хосте (8181) |

---

## Важные правила

- **Все пути от `/opt/docker/chain-prod`** — не менять базу
- `keys/` — никогда не коммитить в git
- `artifacts/` — пересобирать через `build-programs.sh`
- `deploy-programs.sh` — запускать только после появления `.so`
- После deploy — сразу зафиксировать `state/deploy.json`

---

## Идентификация контрактов в blockchain (contract_id / PDA seed)

### Проблема

Solana накладывает жёсткое ограничение: каждый seed при деривации PDA-адреса
не может превышать **32 байта**. UUID в стандартном формате
(`xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`) занимает **36 байт** — на 4 байта
больше допустимого. При превышении Rust runtime паникует:

```
PanicException: Unable to find a viable program address bump seed
```

или, если seed доходит до on-chain программы:

```
Program failed: Could not create program address with signer seeds:
Length of the seed is too long for address generation
```

### Решение

UUID без дефисов (`xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`) — ровно **32 байта**,
что точно вписывается в лимит Solana.

**Правило:** везде где UUID используется как `contract_id` для blockchain —
дефисы удаляются.

#### gdm_solana_bridge — `_normalize_contract_id()`

Файл: `gdm_solana_bridge/app/infrastructure/solana/client.py`

```python
def _normalize_contract_id(contract_id: str) -> str:
    """
    Normalize contract_id to be safe as a Solana PDA seed (<= 32 bytes UTF-8).
    UUID without dashes = 32 hex chars = exactly 32 bytes.
    """
    normalized = contract_id.replace("-", "")
    raw = normalized.encode("utf-8")
    if len(raw) <= 32:
        return normalized
    # Fallback for non-UUID ids longer than 32 bytes: truncate
    return raw[:32].decode("utf-8", errors="ignore")
```

Функция вызывается в трёх местах:
- `derive_contract_pda()` — деривация адреса PDA
- `_register_contract_ix()` — формирование instruction (seed + данные)
- `_send_register_contract()` — idempotency-проверка перед отправкой

> **Важно:** `safe_id` (без дефисов) используется и как seed PDA, и как
> `contract_id` в instruction data. Это обязательно — Rust-программа
> дерайвит PDA изнутри используя тот же `contract_id` из аргументов.
> Если они расходятся — программа не найдёт аккаунт.

#### gdm (Odoo) — `_contract_key()`

Файл: `gdm/models/contract/contract.py`

```python
def _contract_key(self):
    self.ensure_one()
    # UUID without dashes = 32 hex chars = exactly 32 bytes
    # Must match _normalize_contract_id() in gdm_solana_bridge
    raw = (self.uuid or self.number or '').strip()
    return raw.replace('-', '')
```

Метод используется в:
- `action_ai_blockchain_approve()` — кнопка "Approve via AI + Blockchain"
- `action_verify_onchain()` — кнопка "Verify on-chain"

### Итоговый маппинг

```
gdm.contract.uuid (Odoo)
    → _contract_key() → uuid без дефисов (32 байта)
        → Bridge POST /tx/register_and_track { contract_id: "1ac276a476e1..." }
            → _normalize_contract_id() → safe_id (уже без дефисов, <= 32 байта)
                → PDA seed: [b"contract", safe_id.encode()]
                → instruction data: contract_id = safe_id
                    → Rust program: find_program_address([b"contract", contract_id.as_bytes()])
```

### Пересборка bridge после изменений

```bash
docker compose -f /opt/docker/chain-prod/docker-compose.solana.yml \
  build --no-cache solana-bridge && \
docker compose -f /opt/docker/chain-prod/docker-compose.solana.yml \
  up -d --force-recreate solana-bridge
```
