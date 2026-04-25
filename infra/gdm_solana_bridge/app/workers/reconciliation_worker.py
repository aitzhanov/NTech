import asyncio

from app.services.reconciliation_service import ReconciliationService


class ReconciliationWorker:

    def __init__(self, repository, solana_client, audit_repo=None, interval=10):
        self.service = ReconciliationService(repository, solana_client, audit_repo)
        self.interval = interval
        self.repository = repository

    async def run(self):
        while True:
            await self._process()
            await asyncio.sleep(self.interval)

    async def _process(self):
        # naive scan (to be optimized with DB query)
        for request_id, record in getattr(self.repository, "storage", {}).items():
            if record.get("status") in [
                "submitted",
                "timed_out",
                "resync_required"
            ]:
                await self.service.reconcile(request_id)
