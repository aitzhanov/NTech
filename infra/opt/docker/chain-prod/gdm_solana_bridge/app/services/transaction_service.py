from datetime import datetime
from app.domain.enums import TransactionLifecycle
from app.domain.errors import BridgeError, ErrorCode


class TransactionService:

    def __init__(self, repository):
        self.repository = repository

    def transition(self, request_id: str, new_state: TransactionLifecycle, payload: dict = None):
        record = self.repository.get(request_id)

        if not record:
            raise BridgeError(ErrorCode.ENTITY_NOT_FOUND)

        current = record.status

        allowed = {
            "prepared": ["signed"],
            "signed": ["submitted"],
            "submitted": ["confirmed", "failed", "timed_out", "resync_required"],
        }

        if current in allowed and new_state.value not in allowed[current]:
            raise BridgeError(ErrorCode.INVALID_STATE_TRANSITION)

        # business version enforcement
        if payload and "business_version" in payload:
            incoming_version = payload.get("business_version")
            current_version = getattr(record, "business_version", None)

            if current_version is not None and incoming_version <= current_version:
                raise BridgeError(ErrorCode.INVALID_STATE_TRANSITION, "BUSINESS_VERSION_CONFLICT")

            # update business version
            record.business_version = incoming_version

        record.status = new_state.value
        record.updated_at = datetime.utcnow()

        return record
