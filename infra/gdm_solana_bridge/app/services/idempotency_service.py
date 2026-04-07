import hashlib
from datetime import datetime


class IdempotencyService:

    def __init__(self):
        self.storage = {}

    def _hash_payload(self, payload: dict) -> str:
        return hashlib.sha256(str(payload).encode()).hexdigest()

    async def check(self, request_id: str, payload: dict):
        payload_hash = self._hash_payload(payload)

        if request_id in self.storage:
            record = self.storage[request_id]

            if record["payload_hash"] != payload_hash:
                raise Exception("IDEMPOTENCY_PAYLOAD_MISMATCH")

            return record

        self.storage[request_id] = {
            "payload_hash": payload_hash,
            "created_at": datetime.utcnow().isoformat(),
            "tx_hash": None,
            "status": "prepared"
        }

        return self.storage[request_id]
