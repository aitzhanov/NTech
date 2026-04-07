import asyncio

from app.infrastructure.solana.client_mock import SolanaClientMock
from app.services.transaction_service import TransactionService
from app.services.retry_service import RetryService
from app.domain.enums import TransactionLifecycle
from app.domain.errors import BridgeError, ErrorCode


solana = SolanaClientMock()
transaction_service = TransactionService(None)
retry_service = RetryService()


async def process_transaction(request_id: str, payload: dict):
    try:
        await transaction_service.transition(request_id, TransactionLifecycle.SIGNED)

        tx_hash = await retry_service.execute(solana.send_transaction, payload)

        await transaction_service.transition(request_id, TransactionLifecycle.SUBMITTED)

        for _ in range(3):
            result = await retry_service.execute(solana.check_transaction, tx_hash)

            if result.get("status") == "confirmed":
                await transaction_service.transition(request_id, TransactionLifecycle.CONFIRMED)
                return {
                    "tx_hash": tx_hash,
                    "status": "confirmed"
                }

            await asyncio.sleep(1)

        raise BridgeError(ErrorCode.SYNC_TIMEOUT)

    except BridgeError as e:
        if e.type.value == "retriable":
            await transaction_service.transition(request_id, TransactionLifecycle.TIMED_OUT)
        else:
            await transaction_service.transition(request_id, TransactionLifecycle.FAILED)

        return {
            "status": "error",
            "error": e.to_dict()
        }

    except Exception as e:
        await transaction_service.transition(request_id, TransactionLifecycle.FAILED)
        return {
            "status": "error",
            "error": str(e)
        }
