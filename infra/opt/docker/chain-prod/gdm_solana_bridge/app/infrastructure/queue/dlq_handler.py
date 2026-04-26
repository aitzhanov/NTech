from app.infrastructure.queue.celery_app import celery_app
from app.infrastructure.db.pg_repository import AuditRepository


@celery_app.task(name="callback_dlq_handler")
def callback_dlq_handler(payload):
    # store failed callback in audit for manual intervention
    # assuming session is injected externally in real setup
    audit_repo = AuditRepository(None)

    audit_repo.log({
        "request_id": payload.get("request_id"),
        "transaction_lifecycle": "callback_failed",
        "result_status": "error",
        "error_code": "CALLBACK_DLQ"
    })

    return True
