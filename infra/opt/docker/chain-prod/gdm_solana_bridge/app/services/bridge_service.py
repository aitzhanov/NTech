from datetime import datetime
import uuid

from app.services.idempotency_service import IdempotencyService


idempotency = IdempotencyService()


class BridgeService:

    @staticmethod
    async def handle(request):
        record = await idempotency.check(request.request_id, request.data)

        if record.get("tx_hash"):
            return {
                "request_id": request.request_id,
                "status": "accepted",
                "message": "duplicate",
                "tx_hash": record["tx_hash"],
                "submitted_at": record["created_at"],
                "expected_finalization": None
            }

        tx_hash = f"MOCK-{uuid.uuid4()}"

        record["tx_hash"] = tx_hash
        record["status"] = "submitted"

        return {
            "request_id": request.request_id,
            "status": "accepted",
            "message": "submitted",
            "tx_hash": tx_hash,
            "submitted_at": datetime.utcnow().isoformat(),
            "expected_finalization": None
        }

    @staticmethod
    async def get_state(request_id: str):
        record = idempotency.storage.get(request_id)
        return record or {"error": "not_found"}
