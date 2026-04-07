from __future__ import annotations
import logging, os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from app.infrastructure.solana.client import create_client_from_env, SolanaClient

logger = logging.getLogger(__name__)
_solana_client: SolanaClient | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _solana_client
    _solana_client = create_client_from_env()
    logger.info("solana client initialized: %s", _solana_client.rpc_url)
    yield
    if _solana_client:
        await _solana_client.close()

app = FastAPI(title="GDM Solana Bridge", version="0.1.0", lifespan=lifespan)

@app.get("/health")
async def health():
    ok = await _solana_client.health() if _solana_client else False
    return JSONResponse({"status": "ok" if ok else "degraded", "validator": ok})

@app.get("/slot")
async def get_slot():
    slot = await _solana_client.get_slot()
    return {"slot": slot}

@app.post("/tx/send")
async def send_tx(payload: dict):
    sig = await _solana_client.send_transaction(payload)
    return {"signature": sig}

@app.get("/tx/{signature}")
async def check_tx(signature: str):
    return await _solana_client.check_transaction(signature)

@app.get("/balance/{pubkey}")
async def get_balance(pubkey: str):
    lamports = await _solana_client.get_balance(pubkey)
    return {"pubkey": pubkey, "lamports": lamports, "sol": lamports / 1e9}
