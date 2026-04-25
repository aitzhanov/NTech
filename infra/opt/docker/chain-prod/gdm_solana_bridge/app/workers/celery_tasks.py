from app.infrastructure.queue.celery_app import celery_app
from app.workers.transaction_worker import process_transaction


@celery_app.task(name="app.workers.process_transaction")
def process_transaction_task(request_id, payload):
    import asyncio
    return asyncio.run(process_transaction(request_id, payload))
