import requests
import time


class CallbackService:

    def __init__(self, callback_url: str, retries=3):
        self.callback_url = callback_url
        self.retries = retries

    def send(self, payload: dict):
        for attempt in range(self.retries):
            try:
                requests.post(self.callback_url, json=payload, timeout=5)
                return True
            except Exception:
                time.sleep(2 ** attempt)
        return False
