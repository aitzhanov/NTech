from __future__ import annotations
import json, os, logging
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from solana.rpc.types import TxOpts
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.system_program import TransferParams, transfer
from solders.transaction import Transaction
from solders.message import Message

logger = logging.getLogger(__name__)

class SolanaClient:
    def __init__(self, rpc_url: str, payer_keypair_path: str, commitment: str = "confirmed"):
        self.rpc_url = rpc_url
        self.commitment = Confirmed
        self._payer_path = payer_keypair_path
        self._payer: Keypair | None = None
        self._client: AsyncClient | None = None

    def _load_payer(self) -> Keypair:
        if self._payer is None:
            with open(self._payer_path, "r") as f:
                self._payer = Keypair.from_bytes(bytes(json.load(f)))
        return self._payer

    def _get_client(self) -> AsyncClient:
        if self._client is None:
            self._client = AsyncClient(self.rpc_url, commitment=self.commitment)
        return self._client

    async def health(self) -> bool:
        try:
            resp = await self._get_client().get_health()
            return resp.value == "ok"
        except Exception as e:
            logger.error("health check failed: %s", e)
            return False

    async def get_slot(self) -> int:
        return (await self._get_client().get_slot(commitment=self.commitment)).value

    async def get_balance(self, pubkey_str: str) -> int:
        pubkey = Pubkey.from_string(pubkey_str)
        return (await self._get_client().get_balance(pubkey, commitment=self.commitment)).value

    async def request_airdrop(self, pubkey_str: str, lamports: int = 100_000_000_000) -> str:
        pubkey = Pubkey.from_string(pubkey_str)
        resp = await self._get_client().request_airdrop(pubkey, lamports)
        return str(resp.value)

    async def send_transaction(self, payload: dict) -> str:
        client = self._get_client()
        payer = self._load_payer()
        tx_type = payload.get("type", "transfer")
        if tx_type == "transfer":
            to_pubkey = Pubkey.from_string(payload["to"])
            lamports = int(payload.get("lamports", 1000))
            latest_bh = await client.get_latest_blockhash(commitment=self.commitment)
            blockhash = latest_bh.value.blockhash
            ix = transfer(TransferParams(from_pubkey=payer.pubkey(), to_pubkey=to_pubkey, lamports=lamports))
            msg = Message.new_with_blockhash([ix], payer.pubkey(), blockhash)
            tx = Transaction([payer], msg, blockhash)
            resp = await client.send_transaction(tx, opts=TxOpts(skip_preflight=False, preflight_commitment=self.commitment))
            return str(resp.value)
        raise ValueError(f"unsupported tx type: {tx_type}")

    async def check_transaction(self, tx_hash: str) -> dict:
        try:
            from solders.signature import Signature
            sig = Signature.from_string(tx_hash)
            resp = await self._get_client().get_signature_statuses([sig])
            status_val = resp.value[0]
            if status_val is None:
                return {"status": "pending"}
            if status_val.err:
                return {"status": "failed", "error": str(status_val.err)}
            conf = status_val.confirmation_status
            return {"status": str(conf).lower() if conf else "pending"}
        except Exception as e:
            return {"status": "error", "detail": str(e)}

    async def close(self):
        if self._client:
            await self._client.close()
            self._client = None

def create_client_from_env() -> SolanaClient:
    return SolanaClient(
        rpc_url=os.environ.get("SOLANA_RPC_URL", "http://gdm-solana-validator:8899"),
        payer_keypair_path=os.environ.get("SOLANA_PAYER_KEYPAIR", "/app/keys/payer.json"),
        commitment=os.environ.get("SOLANA_COMMITMENT", "confirmed"),
    )

def create_client_from_config(config_path: str) -> SolanaClient:
    import yaml
    with open(config_path) as f:
        cfg = yaml.safe_load(f)
    sol = cfg.get("solana", {})
    return SolanaClient(
        rpc_url=sol.get("rpc_url", "http://gdm-solana-validator:8899"),
        payer_keypair_path=sol.get("keypairs", {}).get("payer", "/app/keys/payer.json"),
        commitment=sol.get("commitment", "confirmed"),
    )
