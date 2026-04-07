# gdm_contract

Standalone модуль управления контрактами с интеграцией Solana blockchain.

Работает **независимо от тяжёлого модуля `gdm`** — достаточно базового Odoo (`base`, `mail`, `uom`).
Совместим с `gdm_ai_orchestrator` и `gdm_solana_bridge`.

Путь: `/opt/docker/gdm-stage/addons/bundle/gdm_contract`

---

## Структура модуля

```
gdm_contract/
├── __init__.py
├── __manifest__.py              depends: [base, mail, uom]
├── models/
│   ├── __init__.py
│   ├── contract_stage.py        contract.stage
│   ├── contract_type.py         contract.type
│   └── contract.py              contract.contract
├── security/
│   ├── security.xml             group_gdm_contract_user / manager
│   └── ir.model.access.csv
├── data/
│   └── contract_sequence.xml    ir.sequence — prefix CTR, code contract.contract
├── views/
│   ├── contract_stage_views.xml
│   ├── contract_type_views.xml
│   ├── contract_views.xml
│   ├── blockchain_dashboard_views.xml
│   └── menu_views.xml           отдельное меню «Contracts»
└── static/description/index.html
```

---

## Модели

### `contract.stage`

Стадии контракта. Настраиваются через Configuration → Stages.

| Поле | Описание |
|------|----------|
| `name` | Название стадии |
| `code` | Технический код |
| `sequence` | Порядок (drag-and-drop) |
| `fold` | Свернуть в Kanban |
| `active` | Активна |

---

### `contract.type`

Типы контрактов. Настраиваются через Configuration → Contract Types.

| Поле | Описание |
|------|----------|
| `name` | Название |
| `code` | Уникальный код |
| `is_purchase` | Тип — закупка |
| `is_lease` | Тип — аренда |
| `is_supply` | Тип — поставка |

---

### `contract.contract`

Основная модель контракта.

| Поле | Описание |
|------|----------|
| `uuid` | UUID (генерируется автоматически, readonly) |
| `name` | Название контракта |
| `number` | Номер (авто-последовательность CTR00000001) |
| `stage_id` | Стадия → `contract.stage` |
| `contract_type_id` | Тип → `contract.type` |
| `operator_comp_id` | Компания-оператор |
| `operator_comp_ceo_id` | CEO оператора |
| `supplier_id` | Поставщик (res.partner) |
| `date` | Дата контракта |
| `date_start` | Дата начала |
| `date_end` | Дата окончания |
| `amount_total` | Сумма контракта |
| `volume_total` | Объём |
| `uom_id` | Единица измерения |
| `blockchain_tx` | Хэш транзакции Solana |
| `blockchain_status` | Статус регистрации on-chain |
| `onchain_version` | Версия записи в blockchain |

**UUID генерируется** из `number + operator_comp_id + supplier_id + date`.
При сохранении обновляется автоматически.

**Кнопки на форме:**
- **Approve via AI + Blockchain** — регистрирует контракт в Solana через bridge
- **Verify on-chain** — читает текущее состояние PDA из blockchain

---

## Blockchain интеграция

Метод `_contract_key()` возвращает UUID контракта без дефисов — ровно 32 байта,
что соответствует лимиту Solana PDA seed. Совпадает с `_normalize_contract_id()`
в `gdm_solana_bridge`.

```python
# uuid: '1ac276a4-76e1-5c39-8f84-9af80089cc25'
# key:  '1ac276a476e15c398f849af80089cc25'  (32 байта)
```

URL bridge берётся из `ir.config_parameter` → `gdm.solana_bridge_url`
(дефолт: `http://172.17.0.1:8181`).

Используемые endpoints:
- `POST /tx/register_and_track` — регистрация контракта
- `GET /contract/{id}` — чтение состояния PDA

---

## Меню

Отдельное корневое меню **Contracts** (не зависит от `gdm`):

```
Contracts
├── Contracts
│   └── All Contracts
├── Blockchain
│   └── Contracts on-chain
└── Configuration          (только manager)
    ├── Stages
    ├── Contract Types
    ├── AI Rules            ← появляется при установке gdm_ai_orchestrator
    └── AI Decisions        ← появляется при установке gdm_ai_orchestrator
```

---

## Группы доступа

| Группа | Права |
|--------|-------|
| `group_gdm_contract_user` | Читать и редактировать контракты |
| `group_gdm_contract_manager` | Полный доступ + настройки |

---

## Совместимость с gdm

`gdm_contract` использует имена моделей **`contract.*`**, а `gdm` использует **`gdm.contract.*`**.
Конфликта нет — оба модуля могут быть установлены на одном сервере одновременно.

`gdm_ai_orchestrator` поддерживает обе модели через `_CONTRACT_MODELS`:
```python
_CONTRACT_MODELS = {'contract.contract', 'gdm.contract'}
```

---

## Установка на новом сервере

Минимальный стек для работы без `gdm`:

```
gdm_contract  +  gdm_ai_orchestrator  +  chain-prod (gdm_solana_bridge + validator)
```

```bash
# Установить модули через Odoo
docker exec gdm-stage odoo -d <dbname> -i gdm_contract,gdm_ai_orchestrator --stop-after-init
docker restart gdm-stage
```

---

## Обновление после изменений кода

```bash
# Python или data файлы
docker exec gdm-stage odoo -d <dbname> -u gdm_contract --stop-after-init
docker restart gdm-stage

# Только XML views
docker restart gdm-stage
```
