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
                │  (Distributors send)  │
                └──────────┬────────────┘
                           │
                           ▼
                ┌───────────────────────┐
                │      AI Analysis      │
                │  - Demand evaluation  │
                │  - Data validation    │
                └──────────┬────────────┘
                           │
                           ▼
                ┌───────────────────────┐
                │ AI Allocation Decision│
                │  - Volume calculation │
                │  - Optimization       │
                └──────────┬────────────┘
                           │
                           ▼
                ┌───────────────────────┐
                │ Approval Process      │
                │ (Auto / Manual)       │
                └──────────┬────────────┘
                           │
                           ▼
                ┌───────────────────────┐
                │  Solana Blockchain    │
                │  - Store allocation   │
                │  - Immutable record   │
                └──────────┬────────────┘
                           │
                           ▼
                ┌───────────────────────┐
                │       Contracts       │
                │  (Sign & Payment)     │
                └──────────┬────────────┘
                           │
                           ▼
                ┌───────────────────────┐
                │   Supply Execution    │
                │  (Delivery process)   │
                └──────────┬────────────┘
                           │
                           ▼
                ┌───────────────────────┐
                │    AI Monitoring      │
                │  - Delivery tracking  │
                │  - Anomaly detection  │
                └──────────┬────────────┘
                           │
          ┌────────────────┴────────────────┐
          ▼                                 ▼
┌───────────────────────┐         ┌───────────────────────┐
│   No Issues Detected  │         │  Issues Detected       │
│        → End          │         │  AI Redistribution     │
└───────────────────────┘         │  - Reallocate volumes  │
                                  │  - Optimize supply     │
                                  └──────────┬────────────┘
                                             │
                                             ▼
                                  ┌───────────────────────┐
                                  │  Update on Solana     │
                                  │  (State change)       │
                                  └──────────┬────────────┘
                                             │
                                             ▼
                                            End

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

## 🔮 Future Improvements

- Advanced AI models for demand forecasting  
- Integration with real-time supply chain data  
- DAO-based governance  
- Predictive anomaly detection  

---

## 📊 Demo Scenario

1. Distributor submits application  
2. AI analyzes demand and allocates volume  
3. Allocation is approved and recorded on Solana  
4. Contract is created and signed  
5. Supply is executed and tracked  
6. AI detects unused volume  
7. Redistribution is triggered automatically  
