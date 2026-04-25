from app.domain.errors import BridgeError, ErrorCode


class StateService:

    def __init__(self, repository):
        self.repository = repository

    async def get_onchain_state(self, request_id: str):
        record = await self.repository.get(request_id)

        if not record:
            raise BridgeError(ErrorCode.ENTITY_NOT_FOUND)

        return {
            "request_id": record.request_id,
            "status": record.status,
            "tx_hash": record.tx_hash
        }
