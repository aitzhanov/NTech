# 🚀 AI-Driven LPG Distribution System (GDM + Solana)

---

## 📌 Overview

This project introduces an **AI-powered Gas Distribution Management (GDM) system** integrated with the **Solana blockchain** to automate LPG allocation, improve transparency, and enable semi-autonomous decision-making.

The system replaces manual distribution processes with an intelligent workflow where **AI makes decisions and executes them on-chain**, ensuring trust and immutability.

---

## ❗ Problem

Current LPG distribution systems suffer from:

- Lack of transparency in allocation decisions  
- Manual and fragmented workflows  
- No immutable audit trail  
- Difficult tracking of supply and deliveries  
- Inefficient redistribution of unused volumes  

---

## 🎯 Solution

We propose a system where:

- AI analyzes demand and makes allocation decisions  
- Decisions are validated and executed automatically  
- All key actions are recorded on the Solana blockchain  
- Redistribution and monitoring are handled autonomously  

---

## 🌍 Real-World Impact

- Transparent LPG allocation  
- Reduced corruption risks  
- Automated decision-making  
- Efficient resource distribution  
- Real-time tracking and monitoring

---

## ⚙️ Key Features

### 🤖 AI Decision Engine
- Demand analysis  
- Allocation optimization  
- Contract validation  
- Anomaly detection  
- Redistribution decisions  

### 🔗 Solana Integration
- Stores allocation records  
- Records contracts and deliveries  
- Tracks redistribution events  
- Ensures immutable audit trail  

### 🏢 GDM Workflow (Odoo-based)
- Application collection  
- Allocation management  
- Approval process  
- Contract handling  
- Supply tracking  

---

## 🔄 System Flow

                ┌───────────────────────┐
                │     Applications      │
                └──────────┬────────────┘
                           │
                           ▼
                ┌───────────────────────┐
                │      AI Analysis      │
                └──────────┬────────────┘
                           │
                           ▼
                ┌───────────────────────┐
                │ AI Allocation Decision│
                └──────────┬────────────┘
                           │
                           ▼
                ┌───────────────────────┐
                │  Approval(Auto/Manual)│
                └──────────┬────────────┘
                           │
                           ▼
                ┌───────────────────────┐
                │   Write to Solana     │
                └──────────┬────────────┘
                           │
                           ▼
                ┌───────────────────────┐
                │       Contracts       │
                └──────────┬────────────┘
                           │
                           ▼
                ┌───────────────────────┐
                │   Supply Execution    │
                └──────────┬────────────┘
                           │
                           ▼
                ┌───────────────────────┐
                │    AI Monitoring      │
                └──────────┬────────────┘
                           │
                           ▼
                ┌───────────────────────┐
                │    AI Redistribution  │
                └──────────┬────────────┘
                           │
                           ▼
                ┌───────────────────────┐
                │    Update on Solana   │
                └──────────┬────────────┘
                           │
                           ▼
                ┌───────────────────────┐
                │        Exit           │
                └───────────────────────┘
---

## 🧠 AI + Blockchain Interaction

The system follows the required architecture:

AI → Decision → On-chain Transaction → Smart Contract State Change


- AI analyzes GDM events  
- Generates decisions  
- Triggers Solana transactions  
- Updates smart contract state  

---

## 🏗️ Architecture
                ┌───────────────────────┐
                │        Users          │
                │ (MinEnergy, Akimat,  │
                │  Suppliers, etc.)    │
                └──────────┬────────────┘
                           │
                           ▼
                ┌───────────────────────┐
                │   Odoo GDM System     │
                │  - Applications       │
                │  - Allocation         │
                │  - Contracts          │
                │  - Monitoring         │
                └──────────┬────────────┘
                           │ (events)
                           ▼
                ┌───────────────────────┐
                │  AI Decision Engine   │
                │  - Demand analysis    │
                │  - Allocation logic   │
                │  - Validation         │
                │  - Redistribution     │
                └──────────┬────────────┘
                           │ (decisions)
                           ▼
                ┌───────────────────────┐
                │  Solana Blockchain    │
                │  Smart Contracts      │
                │  - Allocation state   │
                │  - Contracts          │
                │  - Shipments          │
                └──────────┬────────────┘
                           │
                           ▼
                ┌───────────────────────┐
                │      Database         │
                │   (PostgreSQL)        │
                └───────────────────────┘

---

## ⚡ Technologies Used

- **Odoo** – business workflow and UI  
- **AI (API / model)** – decision-making engine  
- **Solana** – blockchain layer  
- **Smart Contracts (Solana programs)** – state management   

---

# 🚀 NTech — Local Development Setup Guide

> ```bash
> Use main branch. It contains the latest working version.
> ```

---

## ✅ Current Status

| Component | Status |
|---|---|
| Odoo starts | ✅ |
| PostgreSQL starts | ✅ |
| Custom Odoo modules install | ✅ |
| Solana validator starts | ✅ |
| Solana programs build | ✅ |
| Solana programs deploy | ✅ |
| Smoke test passes | ✅ |
| Odoo calls Solana bridge | ✅ |
| Solana bridge returns 200 OK | ✅ |
| Odoo → Bridge → Solana flow works | ✅ |

---

## 📁 Project Structure

```
NTech-main/
├── arch_claude_client/
├── gdm_ai_orchestrator/
├── gdm_contract/
├── gdm_solana_bridge/
├── gdm_solana_programs/
└── infra/
    ├── config/
    │   └── odoo.conf
    ├── docker-compose.odoo.yml
    └── docker-compose.solana.yml
```

---

## Part 1 — Odoo + PostgreSQL Setup

### 2. Open Project Folder

Open the project root:

```
C:\Users\Alikhan\Documents\Python projects\NTech-main\NTech-main
```

The folder should contain:

```
arch_claude_client
gdm_ai_orchestrator
gdm_contract
gdm_solana_bridge
gdm_solana_programs
infra
```

---

### 3. Go to infra

In PowerShell:

```powershell
cd "C:\Users\Alikhan\Documents\Python projects\NTech-main\NTech-main\infra"
```

---

### 4. Create `docker-compose.odoo.yml`

Create file: `infra/docker-compose.odoo.yml`

```yaml
services:
  db:
    image: postgres:13
    container_name: project_pg
    restart: unless-stopped
    environment:
      POSTGRES_DB: odoo15
      POSTGRES_USER: odoo
      POSTGRES_PASSWORD: odoo
    volumes:
      - pg_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  odoo:
    image: odoo:15.0
    container_name: project_odoo
    restart: unless-stopped
    depends_on:
      - db
    ports:
      - "8069:8069"
    environment:
      HOST: db
      PORT: 5432
      USER: odoo
      PASSWORD: odoo
    volumes:
      - odoo_data:/var/lib/odoo
      - ../gdm_contract:/mnt/custom-addons/gdm_contract
      - ../gdm_ai_orchestrator:/mnt/custom-addons/gdm_ai_orchestrator
      - ../arch_claude_client:/mnt/custom-addons/arch_claude_client
      - ./config/odoo.conf:/etc/odoo/odoo.conf
    command: ["odoo", "-c", "/etc/odoo/odoo.conf"]

volumes:
  pg_data:
  odoo_data:
```

---

### 5. Create `config/odoo.conf`

In infra, create folder:

```powershell
mkdir config
```

Create file: `infra/config/odoo.conf`

```ini
[options]
admin_passwd = admin
db_host = db
db_port = 5432
db_user = odoo
db_password = odoo
addons_path = /usr/lib/python3/dist-packages/odoo/addons,/mnt/custom-addons
data_dir = /var/lib/odoo
xmlrpc_port = 8069
proxy_mode = False
limit_time_cpu = 600
limit_time_real = 1200
log_level = info
```

---

### 6. Start Odoo and PostgreSQL

From `infra`:

```powershell
docker compose -f docker-compose.odoo.yml up -d
```

Check containers:

```powershell
docker ps
```

Expected containers:

```
project_pg
project_odoo
```

Check logs:

```powershell
docker compose -f docker-compose.odoo.yml logs -f
```

---

### 7. Initialize Odoo Database If Needed

If `http://localhost:8069` gives an error, initialize the database manually:

```powershell
docker exec -it project_odoo odoo -c /etc/odoo/odoo.conf -d odoo15 -i base --stop-after-init
docker restart project_odoo
```

---

### 8. Open Odoo

Open: [http://localhost:8069](http://localhost:8069)

```
Login:    admin
Password: admin
```

---

### 9. Install Odoo Modules

Open Odoo in debug mode:

```
http://localhost:8069/web?debug=1
```

Go to **Apps**, click **Update Apps List**.

Install modules in this order:

1. `gdm_contract`
2. `arch_claude_client`
3. `gdm_ai_orchestrator`

Restart Odoo after installing modules:

```powershell
docker restart project_odoo
```

---

## Part 2 — Solana Local Infrastructure Setup

> All commands in this section run inside **WSL (Ubuntu)**.

### 10. Open WSL

Open Ubuntu / WSL.

Go to project infra folder:

```bash
cd /mnt/c/Users/Alikhan/Documents/"Python projects"/NTech-main/NTech-main/infra
```

---

### 11. Prepare Solana Runtime Folder

Create runtime folder:

```bash
sudo mkdir -p /opt/docker/chain-prod
```

Copy infra files:

```bash
sudo cp -r ./* /opt/docker/chain-prod/
sudo cp .env.solana.local /opt/docker/chain-prod/.env
```

Copy Solana programs:

```bash
sudo cp -r /mnt/c/Users/Alikhan/Documents/"Python projects"/NTech-main/NTech-main/gdm_solana_programs /opt/docker/chain-prod/
```

Go to runtime folder:

```bash
cd /opt/docker/chain-prod
```

---

### 12. Create Docker Network

```bash
sudo docker network create solana-prod
```

> If it already exists, continue.

---

### 13. Start Solana Infrastructure

```bash
sudo bash ./bin/up.sh
```

Check validator:

```bash
sudo bash ./bin/validator-check.sh
sudo bash ./bin/status.sh
```

Expected:

```
rpc health = ok
validator healthy
```

---

### 14. Check `docker-compose.solana.yml`

Open:

```bash
sudo nano /opt/docker/chain-prod/docker-compose.solana.yml
```

Make sure `solana-tools` has this volume:

```yaml
- /opt/docker/chain-prod/gdm_solana_programs:/solana/gdm_solana_programs
```

Full expected `solana-tools` volumes:

```yaml
volumes:
  - /opt/docker/chain-prod/ledger:/solana/ledger
  - /opt/docker/chain-prod/logs:/solana/logs
  - /opt/docker/chain-prod/keys:/solana/keys
  - /opt/docker/chain-prod/config:/solana/config
  - /opt/docker/chain-prod/state:/solana/state
  - /opt/docker/chain-prod/bin:/solana/bin
  - /opt/docker/chain-prod/artifacts:/solana/artifacts
  - /opt/docker/chain-prod/gdm_solana_programs:/solana/gdm_solana_programs
```

Recreate solana-tools:

```bash
sudo docker compose -f docker-compose.solana.yml up -d --force-recreate solana-tools
```

Check mount:

```bash
sudo docker exec -it gdm-solana-tools bash -lc 'ls /solana/gdm_solana_programs'
```

---

### 15. Bootstrap Keys

Run inside `gdm-solana-tools`:

```bash
sudo docker exec -it gdm-solana-tools bash -lc 'bash /solana/bin/bootstrap-keys.sh'
```

---

### 16. Bootstrap Wallets

Run inside `gdm-solana-tools`:

```bash
sudo docker exec -it gdm-solana-tools bash -lc 'bash /solana/bin/bootstrap-wallets.sh'
```

Check:

```bash
sudo bash ./bin/status.sh
```

Expected keys:

```
payer.json                     OK
authority.json                 OK
contract-program-keypair.json  OK
document-program-keypair.json  OK
```

---

### 17. Build Solana Programs

From `/opt/docker/chain-prod`:

```bash
sudo bash ./bin/build-programs.sh
```

Expected result:

```
contract_state.so        OK
document_verification.so OK
BUILD SUCCESS
```

---

### 18. Deploy Solana Programs

Run inside `gdm-solana-tools`:

```bash
sudo docker exec -it gdm-solana-tools bash -lc 'bash /solana/bin/deploy-programs.sh'
```

Expected output includes program IDs.

**Current working local program IDs:**

```
contract_program_id:  GqZAqQQEE6uq9ftdk78xA51ZnBEW4tF6bfE5pJF5H8tT
document_program_id:  7DUQyBbeEYMud89Ekc3NpvxKQ9PYpDLvGpVex1wYWzXc
```

---

### 19. Run Smoke Test

```bash
sudo bash ./bin/smoke-test.sh
```

Expected:

```
=== RESULT: 6 passed, 0 failed ===
```

---

### 20. Final Solana Status Check

```bash
sudo bash ./bin/status.sh
```

Expected:

```
gdm-solana-validator   Up  healthy
gdm-solana-tools       Up
gdm-solana-bridge      Up
rpc health             ok
artifacts              OK
keys                   OK
deploy state           exists
```

---

## Part 3 — Odoo ↔ Solana Integration Check

### 21. Check Bridge Logs

In WSL:

```bash
sudo docker logs --tail 120 gdm-solana-bridge
```

Successful integration should show:

```
POST /tx/register_and_track HTTP/1.1" 200 OK
```

---

### 22. Check Odoo Logs

In PowerShell from `infra`:

```powershell
docker compose -f docker-compose.odoo.yml logs --tail=200 odoo
```

Successful flow should show Odoo calling the Solana bridge and receiving a blockchain response.

---

### 23. Test Contract Flow

Open Odoo: [http://localhost:8069/web?debug=1](http://localhost:8069/web?debug=1)

Create or update a contract.

Expected backend flow:

```
Odoo contract write/create
        ↓
AI Orchestrator decision
        ↓
Solana Bridge request
        ↓
Solana transaction submission
        ↓
Odoo blockchain fields update
```

---

## 🛠 Useful Commands

### Restart Odoo

```powershell
docker restart project_odoo
```

### Restart Solana Stack

```bash
cd /opt/docker/chain-prod
sudo bash ./bin/down.sh
sudo bash ./bin/up.sh
```

### Open Odoo Shell

```powershell
docker exec -it project_odoo odoo shell -d odoo15 -c /etc/odoo/odoo.conf
```

### Check Latest Contracts (Odoo Shell)

```python
env['contract.contract'].search([], order='id desc', limit=5).read([
    'id',
    'name',
    'number',
    'blockchain_status',
    'blockchain_tx',
    'onchain_version'
])
```

### Check AI Decisions (Odoo Shell)

```python
env['gdm.ai.decision'].search([], order='id desc', limit=5).read([
    'id',
    'entity_model',
    'entity_res_id',
    'decision',
    'risk_level',
    'final_status',
    'blockchain_sync_status'
])
```

---

## 🔧 Troubleshooting

<details>
<summary><strong>Odoo does not open</strong></summary>

Check containers:

```powershell
docker ps
```

Check logs:

```powershell
docker compose -f docker-compose.odoo.yml logs --tail=200 odoo
```

Initialize database if needed:

```powershell
docker exec -it project_odoo odoo -c /etc/odoo/odoo.conf -d odoo15 -i base --stop-after-init
docker restart project_odoo
```

</details>

<details>
<summary><strong>Odoo modules are not visible</strong></summary>

Open debug mode:

```
http://localhost:8069/web?debug=1
```

Then: **Apps → Update Apps List**

</details>

<details>
<summary><strong>Solana network does not start</strong></summary>

Create Docker network:

```bash
sudo docker network create solana-prod
```

Then:

```bash
cd /opt/docker/chain-prod
sudo bash ./bin/up.sh
```

</details>

<details>
<summary><strong>solana command not found</strong></summary>

Run Solana commands inside `gdm-solana-tools`:

```bash
sudo docker exec -it gdm-solana-tools bash
```

</details>

<details>
<summary><strong>Bridge cannot reach validator</strong></summary>

Check `.env`:

```bash
cat /opt/docker/chain-prod/.env
```

Expected:

```env
SOLANA_RPC_URL=http://gdm-solana-validator:8899
SOLANA_WS_URL=ws://gdm-solana-validator:8900
```

Restart bridge:

```bash
sudo docker compose -f docker-compose.solana.yml up -d --force-recreate solana-bridge
```

</details>

<details>
<summary><strong>Program ID mismatch</strong></summary>

Make sure the Solana program `declare_id!()` values match the deployed program IDs.

Check deployed state:

```bash
cat /opt/docker/chain-prod/state/deploy.json
```

Check bridge client:

```bash
grep -n 'CONTRACT_PROGRAM_ID' /opt/docker/chain-prod/gdm_solana_bridge/app/infrastructure/solana/client.py
```

</details>

<details>
<summary><strong>Repeated blockchain submits</strong></summary>

This can happen if contract writes trigger the orchestrator repeatedly.

The working setup uses a context guard:

```python
skip_ai_trigger=True
```

Blockchain field updates should use:

```python
contract.with_context(skip_ai_trigger=True).write(write_vals)
```

</details>
