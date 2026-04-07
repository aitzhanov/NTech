class InMemoryRepository:
    def __init__(self):
        self.storage = {}

    async def get(self, request_id):
        return self.storage.get(request_id)

    async def save(self, record):
        self.storage[record["request_id"]] = record
        return record

    async def update(self, request_id, values: dict):
        record = self.storage.get(request_id)
        if not record:
            return None
        record.update(values)
        self.storage[request_id] = record
        return record
