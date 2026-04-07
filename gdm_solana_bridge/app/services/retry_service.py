import asyncio
from app.domain.errors import BridgeError, ErrorType

class RetryService:
    def __init__(self, max_retries=3, backoff=None):
        self.max_retries = max_retries
        self.backoff = backoff or [1, 5, 15]

    async def execute(self, func, *args, **kwargs):
        attempt = 0
        while attempt <= self.max_retries:
            try:
                return await func(*args, **kwargs)
            except BridgeError as e:
                if e.type == ErrorType.NON_RETRIABLE or attempt == self.max_retries:
                    raise
                await asyncio.sleep(self.backoff[min(attempt, len(self.backoff) - 1)])
                attempt += 1
            except Exception:
                if attempt == self.max_retries:
                    raise
                await asyncio.sleep(self.backoff[min(attempt, len(self.backoff) - 1)])
                attempt += 1
