from __future__ import annotations

from typing import Any, Dict, Optional
import asyncio
import base64
import hashlib
import struct

from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.instruction import AccountMeta, Instruction
from solders.signature import Signature
from solders.system_program import TransferParams, transfer, ID as SYSTEM_PROGRAM_ID
from solders.transaction import Transaction
from solders.message import Message
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from solana.rpc.types import TxOpts


CONTRACT_PROGRAM_ID = Pubkey.from_string("FhXXErPW17TR5sX1ZviQNP7BuZnV22hiixtf1Ww9tYQ5")

# Solana PDA seed max length is 32 bytes per seed.
_SEED_MAX_BYTES = 32


def _normalize_contract_id(contract_id: str) -> str:
    """
    Normalize contract_id to be safe as a Solana PDA seed (<= 32 bytes UTF-8).

    Strategy:
    - Strip dashes (UUID dashes are cosmetic, not semantic)
    - If still > 32 bytes, take first 32 hex chars (128 bits of entropy — sufficient)

    This must be applied BOTH to the PDA derivation seed AND to the contract_id
    stored in the instruction data, so that the Rust program derives the same PDA.
    """
    # Remove dashes — UUID without dashes is 32 hex chars = exactly 32 bytes
    normalized = contract_id.replace("-", "")
    raw = normalized.encode("utf-8")
    if len(raw) <= _SEED_MAX_BYTES:
        return normalized
    # Fallback: truncate to 32 bytes
    return raw[:_SEED_MAX_BYTES].decode("utf-8", errors="ignore")


class SolanaClient:
    def __init__(
        self,
        rpc_url: str,
        payer_keypair_path: str,
        commitment: str = "confirmed",
    ) -> None:
        self.rpc_url = rpc_url
        self.payer_keypair_path = payer_keypair_path
        self.commitment = commitment

    def _load_payer(self) -> Keypair:
        with open(self.payer_keypair_path, "r", encoding="utf-8") as f:
            return Keypair.from_json(f.read())

    async def health(self) -> Dict[str, Any]:
        try:
            async with AsyncClient(self.rpc_url, commitment=Confirmed) as client:
                slot_resp = await client.get_slot()
                blockhash_resp = await client.get_latest_blockhash()
                return {
                    "ok": True,
                    "validator": True,
                    "slot": getattr(slot_resp, "value", None),
                    "latest_blockhash": str(blockhash_resp.value.blockhash),
                }
        except Exception as exc:
            return {"ok": False, "validator": False, "error": str(exc)}

    async def get_slot(self) -> int:
        async with AsyncClient(self.rpc_url, commitment=Confirmed) as client:
            resp = await client.get_slot()
            return int(resp.value)

    async def get_balance(self, pubkey: str) -> Dict[str, Any]:
        async with AsyncClient(self.rpc_url, commitment=Confirmed) as client:
            target = Pubkey.from_string(pubkey)
            resp = await client.get_balance(target)
            lamports = int(resp.value)
            return {"pubkey": pubkey, "lamports": lamports, "sol": lamports / 1_000_000_000}

    def _map_confirmation_status(self, value: Optional[str]) -> str:
        if value is None:
            return "unknown"
        normalized = str(value).lower().split(".")[-1]
        if normalized in {"processed", "confirmed", "finalized"}:
            return normalized
        return "unknown"

    async def get_tx_status(self, signature: str) -> Dict[str, Any]:
        async with AsyncClient(self.rpc_url, commitment=Confirmed) as client:
            sig_obj = Signature.from_string(signature)
            resp = await client.get_signature_statuses([sig_obj], search_transaction_history=True)
            values = getattr(resp, "value", None) or []
            status = values[0] if values else None

            if status is None:
                return {
                    "found": False,
                    "signature": signature,
                    "status": "not_found",
                    "confirmation_status": None,
                    "slot": None,
                    "confirmations": None,
                    "err": None,
                }

            confirmation_status = self._map_confirmation_status(getattr(status, "confirmation_status", None))
            confirmations = getattr(status, "confirmations", None)
            err = getattr(status, "err", None)

            return {
                "found": True,
                "signature": signature,
                "status": confirmation_status,
                "confirmation_status": confirmation_status,
                "slot": getattr(status, "slot", None),
                "confirmations": confirmations,
                "err": err,
                "error": err,
            }

    async def wait_for_confirmation(
        self,
        signature: str,
        target_status: str = "finalized",
        timeout_seconds: float = 30.0,
        poll_interval_seconds: float = 0.75,
        rebroadcast_payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        allowed = {"processed": 1, "confirmed": 2, "finalized": 3}
        target_rank = allowed.get(target_status, 3)
        deadline = asyncio.get_running_loop().time() + timeout_seconds
        history = []
        rebroadcasted = False
        rebroadcast_result = None

        while True:
            status = await self.get_tx_status(signature)
            history.append(
                {
                    "status": status.get("status"),
                    "slot": status.get("slot"),
                    "confirmations": status.get("confirmations"),
                    "error": status.get("error"),
                }
            )

            current_status = status.get("status")
            current_rank = allowed.get(current_status, 0)
            if status.get("error") is not None:
                return {
                    "signature": signature,
                    "target_status": target_status,
                    "reached": False,
                    "timed_out": False,
                    "rebroadcasted": rebroadcasted,
                    "rebroadcast_result": rebroadcast_result,
                    "history": history,
                    "final_status": status,
                }

            if current_rank >= target_rank:
                return {
                    "signature": signature,
                    "target_status": target_status,
                    "reached": True,
                    "timed_out": False,
                    "rebroadcasted": rebroadcasted,
                    "rebroadcast_result": rebroadcast_result,
                    "history": history,
                    "final_status": status,
                }

            now = asyncio.get_running_loop().time()
            if (
                not rebroadcasted
                and rebroadcast_payload is not None
                and current_status == "not_found"
                and now + poll_interval_seconds >= deadline
            ):
                rebroadcasted = True
                try:
                    rebroadcast_result = await self.send_transaction(rebroadcast_payload)
                    new_signature = rebroadcast_result.get("signature")
                    if new_signature:
                        signature = new_signature
                except Exception as exc:
                    rebroadcast_result = {"error": str(exc)}

            if now >= deadline:
                return {
                    "signature": signature,
                    "target_status": target_status,
                    "reached": False,
                    "timed_out": True,
                    "rebroadcasted": rebroadcasted,
                    "rebroadcast_result": rebroadcast_result,
                    "history": history,
                    "final_status": status,
                }

            await asyncio.sleep(poll_interval_seconds)

    def _validate_transfer_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(payload, dict):
            raise ValueError("payload must be an object")
        if payload.get("type") != "transfer":
            raise ValueError("only payload.type='transfer' is currently supported")
        to_value = payload.get("to")
        if not to_value:
            raise ValueError("missing required field: to")
        lamports_value = payload.get("lamports")
        if lamports_value is None:
            raise ValueError("missing required field: lamports")
        lamports = int(lamports_value)
        if lamports <= 0:
            raise ValueError("lamports must be > 0")
        return {"type": "transfer", "to": str(to_value), "lamports": lamports}

    def _anchor_discriminator(self, name: str) -> bytes:
        return hashlib.sha256(f"global:{name}".encode("utf-8")).digest()[:8]

    def _account_discriminator(self, name: str) -> bytes:
        return hashlib.sha256(f"account:{name}".encode("utf-8")).digest()[:8]

    def _encode_anchor_string(self, value: str) -> bytes:
        raw = value.encode("utf-8")
        return len(raw).to_bytes(4, "little") + raw

    def _encode_u64(self, value: int) -> bytes:
        return int(value).to_bytes(8, "little")

    def derive_contract_pda(self, contract_id: str) -> Dict[str, Any]:
        safe_id = _normalize_contract_id(contract_id)
        contract_pda, bump = Pubkey.find_program_address(
            [b"contract", safe_id.encode("utf-8")],
            CONTRACT_PROGRAM_ID,
        )
        return {
            "contract_id": contract_id,
            "safe_contract_id": safe_id,
            "contract_pda": str(contract_pda),
            "bump": bump,
            "program_id": str(CONTRACT_PROGRAM_ID),
        }

    def _register_contract_ix(self, authority: Pubkey, contract_id: str, version: int):
        # IMPORTANT: safe_id must be used BOTH as seed AND as the contract_id in instruction data
        # so the Rust program derives the same PDA address.
        safe_id = _normalize_contract_id(contract_id)
        contract_pda, bump = Pubkey.find_program_address(
            [b"contract", safe_id.encode("utf-8")],
            CONTRACT_PROGRAM_ID,
        )

        data = (
            self._anchor_discriminator("register_contract")
            + self._encode_anchor_string(safe_id)   # <-- safe_id, not contract_id
            + self._encode_u64(version)
        )

        ix = Instruction(
            CONTRACT_PROGRAM_ID,
            data,
            [
                AccountMeta(contract_pda, False, True),
                AccountMeta(authority, True, True),
                AccountMeta(SYSTEM_PROGRAM_ID, False, False),
            ],
        )
        return ix, contract_pda, bump

    def _decode_contract_state(self, raw: bytes) -> Dict[str, Any]:
        offset = 0
        discriminator = raw[offset:offset + 8]
        offset += 8

        contract_state_disc = self._account_discriminator("ContractState")
        if discriminator != contract_state_disc:
            raise ValueError("unexpected account discriminator")

        str_len = struct.unpack_from("<I", raw, offset)[0]
        offset += 4
        contract_id = raw[offset:offset + str_len].decode("utf-8")
        offset += str_len

        status_tag = raw[offset] if offset < len(raw) else None
        offset += 1

        version = struct.unpack_from("<Q", raw, offset)[0]
        offset += 8

        authority = str(Pubkey.from_bytes(raw[offset:offset + 32]))
        offset += 32

        is_initialized = bool(raw[offset]) if offset < len(raw) else None
        offset += 1

        bump = raw[offset] if offset < len(raw) else None
        offset += 1

        created_at = struct.unpack_from("<q", raw, offset)[0]
        offset += 8

        updated_at = struct.unpack_from("<q", raw, offset)[0]
        offset += 8

        return {
            "contract_id": contract_id,
            "status_tag": status_tag,
            "version": int(version),
            "authority": authority,
            "is_initialized": is_initialized,
            "bump": bump,
            "created_at": int(created_at),
            "updated_at": int(updated_at),
        }

    async def get_contract_state(self, contract_id: str) -> Dict[str, Any]:
        pda_info = self.derive_contract_pda(contract_id)
        pda = Pubkey.from_string(pda_info["contract_pda"])

        async with AsyncClient(self.rpc_url, commitment=Confirmed) as client:
            resp = await client.get_account_info(pda, encoding="base64")
            account = getattr(resp, "value", None)

            if account is None:
                return {
                    "found": False,
                    "contract_id": contract_id,
                    "contract_pda": str(pda),
                    "program_id": str(CONTRACT_PROGRAM_ID),
                }

            data_field = getattr(account, "data", None)
            if isinstance(data_field, bytes):
                raw = data_field
            elif isinstance(data_field, (list, tuple)) and data_field:
                encoded = data_field[0]
                raw = base64.b64decode(encoded)
            elif isinstance(data_field, str):
                raw = base64.b64decode(data_field)
            elif hasattr(data_field, "data"):
                inner = data_field.data
                if isinstance(inner, bytes):
                    raw = inner
                elif isinstance(inner, (list, tuple)) and inner:
                    raw = base64.b64decode(inner[0])
                else:
                    raise ValueError(f"unsupported nested account data format: {type(inner)}")
            else:
                raise ValueError(f"unsupported account data format: {type(data_field)}")

            decoded = self._decode_contract_state(raw)

            return {
                "found": True,
                "contract_id": decoded["contract_id"],
                "version": decoded["version"],
                "status_tag": decoded.get("status_tag"),
                "contract_pda": str(pda),
                "program_id": str(CONTRACT_PROGRAM_ID),
                "lamports": getattr(account, "lamports", None),
                "owner": str(getattr(account, "owner", CONTRACT_PROGRAM_ID)),
                "space": len(raw),
            }

    async def _send_transfer(self, client: AsyncClient, payer: Keypair, payer_pubkey: Pubkey, payload: Dict[str, Any]) -> Dict[str, Any]:
        normalized = self._validate_transfer_payload(payload)
        to_pubkey = Pubkey.from_string(normalized["to"])
        lamports = normalized["lamports"]

        latest_blockhash_resp = await client.get_latest_blockhash()
        recent_blockhash = latest_blockhash_resp.value.blockhash

        ix = transfer(
            TransferParams(
                from_pubkey=payer_pubkey,
                to_pubkey=to_pubkey,
                lamports=lamports,
            )
        )

        tx = Transaction.new_signed_with_payer(
            [ix], payer_pubkey, [payer], recent_blockhash
        )

        opts = TxOpts(skip_preflight=False, preflight_commitment=Confirmed)
        resp = await client.send_transaction(tx, opts=opts)
        signature = str(resp.value) if hasattr(resp, "value") else str(resp)

        return {
            "signature": signature,
            "signer": str(payer_pubkey),
            "rpc_url": self.rpc_url,
            "recent_blockhash": str(recent_blockhash),
            "transaction": {
                "type": "transfer",
                "from": str(payer_pubkey),
                "to": str(to_pubkey),
                "lamports": lamports,
            },
        }

    async def _send_register_contract(self, client: AsyncClient, payer: Keypair, payer_pubkey: Pubkey, payload: Dict[str, Any]) -> Dict[str, Any]:
        contract_id = payload.get("contract_id")
        version = int(payload.get("version", 1))
        if not contract_id:
            raise ValueError("missing required field: contract_id")

        # Normalize before any PDA derivation or on-chain lookup
        safe_id = _normalize_contract_id(contract_id)

        existing_state = await self.get_contract_state(safe_id)
        if existing_state.get("found"):
            return {
                "signature": None,
                "signer": str(payer_pubkey),
                "rpc_url": self.rpc_url,
                "recent_blockhash": None,
                "retry_attempts": 0,
                "skipped": True,
                "skip_reason": "contract_already_exists",
                "transaction": {
                    "type": "register_contract",
                    "authority": str(payer_pubkey),
                    "contract_id": safe_id,
                    "version": version,
                    "contract_pda": existing_state.get("contract_pda"),
                    "program_id": str(CONTRACT_PROGRAM_ID),
                },
                "onchain_state": existing_state,
            }

        attempts = 0
        last_error = None
        blockhash_history = []

        while attempts < 2:
            try:
                latest_blockhash_resp = await client.get_latest_blockhash()
                recent_blockhash = latest_blockhash_resp.value.blockhash
                blockhash_history.append(str(recent_blockhash))

                ix, contract_pda, bump = self._register_contract_ix(
                    payer_pubkey, safe_id, version
                )

                msg = Message.new_with_blockhash([ix], payer_pubkey, recent_blockhash)
                tx = Transaction([payer], msg, recent_blockhash)

                opts = TxOpts(skip_preflight=False, preflight_commitment=Confirmed)
                resp = await client.send_transaction(tx, opts=opts)
                signature = str(resp.value) if hasattr(resp, "value") else str(resp)

                return {
                    "signature": signature,
                    "signer": str(payer_pubkey),
                    "rpc_url": self.rpc_url,
                    "recent_blockhash": str(recent_blockhash),
                    "retry_attempts": attempts,
                    "blockhash_history": blockhash_history,
                    "transaction": {
                        "type": "register_contract",
                        "authority": str(payer_pubkey),
                        "contract_id": safe_id,
                        "version": version,
                        "contract_pda": str(contract_pda),
                        "bump": bump,
                        "program_id": str(CONTRACT_PROGRAM_ID),
                    },
                }
            except Exception as exc:
                last_error = exc
                message = str(exc).lower()
                if "already in use" in message or "custom program error: 0x0" in message:
                    existing_state = await self.get_contract_state(safe_id)
                    if existing_state.get("found"):
                        return {
                            "signature": None,
                            "signer": str(payer_pubkey),
                            "rpc_url": self.rpc_url,
                            "recent_blockhash": None,
                            "retry_attempts": attempts,
                            "blockhash_history": blockhash_history,
                            "skipped": True,
                            "skip_reason": "contract_already_exists",
                            "transaction": {
                                "type": "register_contract",
                                "authority": str(payer_pubkey),
                                "contract_id": safe_id,
                                "version": version,
                                "contract_pda": existing_state.get("contract_pda"),
                                "program_id": str(CONTRACT_PROGRAM_ID),
                            },
                            "onchain_state": existing_state,
                        }
                if "blockhash" in message:
                    attempts += 1
                    continue
                raise

        raise last_error

    async def send_and_track_contract(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        result = await self.send_transaction(payload)

        if payload.get("type") != "register_contract":
            signature = result.get("signature")
            tx_status = await self.get_tx_status(signature) if signature else None
            if tx_status is None:
                tx_status = {
                    "found": False,
                    "signature": None,
                    "status": "not_sent",
                    "confirmation_status": None,
                    "slot": None,
                    "confirmations": None,
                    "err": None,
                    "error": None,
                }
            return {
                "tx": result,
                "tx_status": tx_status,
                "onchain_state": None,
            }

        if result.get("skipped"):
            tx_result = dict(result)
            tx_result.pop("onchain_state", None)
            return {
                "tx": tx_result,
                "tx_status": {
                    "found": True,
                    "signature": None,
                    "status": "skipped",
                    "confirmation_status": "skipped",
                    "slot": None,
                    "confirmations": None,
                    "err": None,
                    "error": None,
                },
                "onchain_state": result.get("onchain_state"),
            }

        signature = result.get("signature")
        safe_id = _normalize_contract_id(payload["contract_id"])
        confirmation = await self.wait_for_confirmation(
            signature,
            target_status=payload.get("wait_for", "confirmed"),
            timeout_seconds=float(payload.get("timeout_seconds", 30)),
            rebroadcast_payload=payload,
        )

        state = await self.get_contract_state(safe_id)

        return {
            "tx": result,
            "tx_status": confirmation,
            "onchain_state": state,
        }

    async def send_transaction(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(payload, dict):
            raise ValueError("payload must be an object")

        tx_type = payload.get("type", "transfer")
        payer = self._load_payer()
        payer_pubkey = payer.pubkey()

        async with AsyncClient(self.rpc_url, commitment=Confirmed) as client:
            if tx_type == "transfer":
                return await self._send_transfer(client, payer, payer_pubkey, payload)

            if tx_type == "register_contract":
                return await self._send_register_contract(client, payer, payer_pubkey, payload)

            raise ValueError(f"unsupported tx type: {tx_type}")
