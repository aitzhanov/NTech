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

## 🌍 Real-World Impact

- Transparent LPG allocation  
- Reduced corruption risks  
- Automated decision-making  
- Efficient resource distribution  
- Real-time tracking and monitoring  

---

## Setup

This project includes three main runtime layers:

- **Odoo 15 Community Edition**
- **PostgreSQL**
- **Solana local infrastructure**

### 1. Start PostgreSQL and Odoo 15 CE

Run from:

```bash
cd project/infra
docker compose -f docker-compose.odoo.yml up -d
````

Check logs:

```bash
docker compose -f docker-compose.odoo.yml logs -f
```

Open Odoo in the browser:

```text
http://localhost:8069
```

### 2. Configure the Odoo database

Create or select the database for the project.

The custom addons are mounted from:

```text
project/odoo/addons/
```

Required Odoo modules:

* `gdm_contract`
* `gdm_ai_orchestrator`
* `gdm_claude_agent`

### 3. Install Odoo modules

After Odoo starts:

1. Open **Apps**
2. Update the Apps List
3. Install:

   * `gdm_contract`
   * `gdm_ai_orchestrator`
   * `gdm_claude_agent`

### 4. Start Solana infrastructure

Run all Solana infrastructure scripts from:

```bash
cd project/infra
```

Start the local environment and validate it:

```bash
./bin/up.sh
./bin/validator-check.sh
./bin/status.sh
```

Initialize keys and wallets:

```bash
./bin/bootstrap-keys.sh
./bin/bootstrap-wallets.sh
```

Build and deploy Solana programs:

```bash
./bin/build-programs.sh
./bin/deploy-programs.sh
```

Run the smoke test:

```bash
./bin/smoke-test.sh
```

### 5. Stop or reset the Solana environment

```bash
./bin/reset.sh
./bin/down.sh
```

### 6. Docker Compose for Odoo 15 CE and PostgreSQL

Create the file:

```text
project/infra/docker-compose.odoo.yml
```

with the following content:

```yaml
version: "3.9"

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
      - ../odoo/addons:/mnt/custom-addons
      - ./config/odoo.conf:/etc/odoo/odoo.conf
    command: ["odoo", "-c", "/etc/odoo/odoo.conf"]

volumes:
  pg_data:
  odoo_data:
```

### 7. Odoo configuration

Create the file:

```text
project/infra/config/odoo.conf
```

with the following content:

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

```
4. Start Solana infrastructure

Run all Solana infrastructure scripts from:

cd project/infra

Available commands:

./bin/up.sh
./bin/validator-check.sh
./bin/status.sh
./bin/bootstrap-keys.sh
./bin/bootstrap-wallets.sh
./bin/build-programs.sh
./bin/deploy-programs.sh
./bin/smoke-test.sh

Stop or reset the local Solana environment:

./bin/reset.sh
./bin/down.sh
Responsibility Split
odoo/addons/ — Odoo modules
bridge/gdm_solana_bridge/ — Solana bridge service
solana/gdm_solana_programs/ — Solana on-chain programs
infra/ — Docker, scripts, keys, validator state, logs, and deployment/runtime files

```
