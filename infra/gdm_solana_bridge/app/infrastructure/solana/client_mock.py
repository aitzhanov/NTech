import uuid
import random


class SolanaClientMock:

    async def send_transaction(self, payload: dict):
        return f"SOL-{uuid.uuid4()}"

    async def check_transaction(self, tx_hash: str):
        # simulate random confirmation
        if random.choice([True, False]):
            return {
                "status": "confirmed"
            }
        return {
            "status": "pending"
        }
