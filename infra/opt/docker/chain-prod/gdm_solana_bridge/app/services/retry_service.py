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
                if e.type == ErrorType.NON_RETRIABLE:
                    raise

                if attempt == self.max_retries:
                    raise

                delay = self.backoff[min(attempt, len(self.backoff) - 1)]
                await asyncio.sleep(delay)
                attempt += 1

            except Exception as e:
                # fallback unknown errors treated as retriable
                if attempt == self.max_retries:
                    raise

                delay = self.backoff[min(attempt, len(self.backoff) - 1)]
                await asyncio.sleep(delay)
                attempt += 1
