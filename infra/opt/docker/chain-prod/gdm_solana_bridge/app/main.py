from __future__ import annotations

import logging
import os
import traceback

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.infrastructure.solana.client import SolanaClient

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI(title="GDM Solana Bridge", version="0.2.0")

_solana_client = SolanaClient(
    rpc_url=os.getenv("SOLANA_RPC_URL", "http://gdm-solana-validator:8899"),
    payer_keypair_path=os.getenv("SOLANA_PAYER_KEYPAIR", "/app/keys/payer.json"),
    commitment=os.getenv("SOLANA_COMMITMENT", "confirmed"),
)


@app.get("/health")
async def health():
    info = await _solana_client.health()
    if info.get("validator"):
        return {
            "status": "ok",
            "validator": True,
            "slot": info.get("slot"),
            "latest_blockhash": info.get("latest_blockhash"),
        }

    return JSONResponse(
        status_code=200,
        content={
            "status": "degraded",
            "validator": False,
            "error": info.get("error"),
        },
    )


@app.get("/slot")
async def get_slot():
    try:
        slot = await _solana_client.get_slot()
        return {"slot": slot}
    except Exception as exc:
        logger.exception("GET /slot failed")
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/tx/send")
async def send_tx(payload: dict):
    try:
        result = await _solana_client.send_transaction(payload)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception("POST /tx/send failed")
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/tx/{signature}")
async def check_tx(signature: str):
    try:
        result = await _solana_client.get_tx_status(signature)
        return result
    except Exception as exc:
        logger.exception("GET /tx/%s failed", signature)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/contract/{contract_id}")
async def get_contract(contract_id: str):
    try:
        result = await _solana_client.get_contract_state(contract_id)
        return result
    except Exception as exc:
        logger.exception("GET /contract/%s failed", contract_id)
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/tx/register_and_track")
async def register_and_track(request: Request):
    payload = None
    try:
        payload = await request.json()
        logger.debug("POST /tx/register_and_track payload: %s", payload)
        result = await _solana_client.send_and_track_contract(payload)
        return result
    except ValueError as exc:
        logger.exception("POST /tx/register_and_track ValueError, payload=%s", payload)
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception("POST /tx/register_and_track FAILED, payload=%s", payload)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/balance/{pubkey}")
async def get_balance(pubkey: str):
    try:
        result = await _solana_client.get_balance(pubkey)
        return result
    except Exception as exc:
        logger.exception("GET /balance/%s failed", pubkey)
        raise HTTPException(status_code=500, detail=str(exc))
