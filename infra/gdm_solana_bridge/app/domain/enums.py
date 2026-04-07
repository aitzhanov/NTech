from enum import Enum

class TransactionLifecycle(str, Enum):
    PREPARED = "prepared"
    SIGNED = "signed"
    SUBMITTED = "submitted"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    RESYNC_REQUIRED = "resync_required"


class EntityType(str, Enum):
    CONTRACT = "contract"
    DOCUMENT = "document"


class ErrorType(str, Enum):
    RETRIABLE = "retriable"
    NON_RETRIABLE = "non_retriable"
