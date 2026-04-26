import hashlib


class CallbackIdempotencyService:

    def __init__(self, repository):
        self.repository = repository

    def generate_key(self, payload: dict):
        return hashlib.sha256(str(payload).encode()).hexdigest()

    def is_processed(self, key: str):
        record = self.repository.get(key)
        return record is not None

    def mark_processed(self, key: str, payload: dict):
        self.repository.save({
            "request_id": key,
            "payload": payload,
            "status": "callback_processed"
        })
