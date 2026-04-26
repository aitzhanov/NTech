from app.domain.enums import TransactionLifecycle
from app.domain.errors import BridgeError, ErrorCode


class ReconciliationService:

    def __init__(self, repository, solana_client, audit_repo=None):
        self.repository = repository
        self.solana = solana_client
        self.audit_repo = audit_repo

    async def reconcile(self, request_id: str):
        record = await self.repository.get(request_id)

        if not record:
            raise BridgeError(ErrorCode.ENTITY_NOT_FOUND)

        if record.status not in [
            TransactionLifecycle.SUBMITTED,
            TransactionLifecycle.TIMED_OUT,
            TransactionLifecycle.RESYNC_REQUIRED,
        ]:
            return record

        tx_hash = record.tx_hash

        if not tx_hash:
            raise BridgeError(ErrorCode.ENTITY_NOT_FOUND)

        result = await self.solana.check_transaction(tx_hash)

        # strict comparison
        onchain_status = result.get("status")
        onchain_version = result.get("business_version")

        local_version = getattr(record, "business_version", None)
        local_status = record.status

        if onchain_status == "confirmed" and (onchain_version is None or onchain_version == local_version):
            await self.repository.update(request_id, {
                "status": TransactionLifecycle.CONFIRMED
            })

            if self.audit_repo:
                await self.audit_repo.log({
                    "request_id": request_id,
                    "transaction_lifecycle": "confirmed",
                    "blockchain_tx_hash": tx_hash,
                    "result_status": "success"
                })

            return await self.repository.get(request_id)

        # mismatch cases
        if onchain_status == "confirmed" and onchain_version != local_version:
            await self.repository.update(request_id, {
                "status": TransactionLifecycle.RESYNC_REQUIRED
            })

            if self.audit_repo:
                await self.audit_repo.log({
                    "request_id": request_id,
                    "transaction_lifecycle": "resync_required",
                    "blockchain_tx_hash": tx_hash,
                    "result_status": "error",
                    "error_code": "VERSION_MISMATCH"
                })

            return await self.repository.get(request_id)

        # mismatch or unknown state
        await self.repository.update(request_id, {
            "status": TransactionLifecycle.RESYNC_REQUIRED
        })

        if self.audit_repo:
            await self.audit_repo.log({
                "request_id": request_id,
                "transaction_lifecycle": "resync_required",
                "blockchain_tx_hash": tx_hash,
                "result_status": "error"
            })

        return await self.repository.get(request_id)
