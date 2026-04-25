from enum import Enum

class ErrorType(str, Enum):
    RETRIABLE = "retriable"
    NON_RETRIABLE = "non_retriable"

class ErrorCode(str, Enum):
    NETWORK_ERROR = "NETWORK_ERROR"
    RPC_TIMEOUT = "RPC_TIMEOUT"
    RPC_UNAVAILABLE = "RPC_UNAVAILABLE"
    TEMPORARY_NODE_FAILURE = "TEMPORARY_NODE_FAILURE"
    SUBMISSION_TIMEOUT = "SUBMISSION_TIMEOUT"
    SYNC_TIMEOUT = "SYNC_TIMEOUT"
    RATE_LIMIT_TEMPORARY = "RATE_LIMIT_TEMPORARY"
    INVALID_PAYLOAD = "INVALID_PAYLOAD"
    SCHEMA_VALIDATION_FAILED = "SCHEMA_VALIDATION_FAILED"
    INVALID_STATE_TRANSITION = "INVALID_STATE_TRANSITION"
    IDEMPOTENCY_PAYLOAD_MISMATCH = "IDEMPOTENCY_PAYLOAD_MISMATCH"
    SIGNATURE_INVALID = "SIGNATURE_INVALID"
    UNAUTHORIZED_ACTION = "UNAUTHORIZED_ACTION"
    SMART_CONTRACT_REJECTED = "SMART_CONTRACT_REJECTED"
    ENTITY_NOT_FOUND = "ENTITY_NOT_FOUND"
    UNSUPPORTED_ACTION = "UNSUPPORTED_ACTION"
    INVALID_HASH_FORMAT = "INVALID_HASH_FORMAT"

RETRIABLE_ERRORS = {
    ErrorCode.NETWORK_ERROR, ErrorCode.RPC_TIMEOUT, ErrorCode.RPC_UNAVAILABLE,
    ErrorCode.TEMPORARY_NODE_FAILURE, ErrorCode.SUBMISSION_TIMEOUT,
    ErrorCode.SYNC_TIMEOUT, ErrorCode.RATE_LIMIT_TEMPORARY,
}

class BridgeError(Exception):
    def __init__(self, code: ErrorCode, message: str = "", details: dict = None):
        self.code = code
        self.type = ErrorType.RETRIABLE if code in RETRIABLE_ERRORS else ErrorType.NON_RETRIABLE
        self.message = message or code.value
        self.details = details or {}

    def to_dict(self):
        return {"code": self.code.value, "type": self.type.value, "message": self.message, "details": self.details}
