from app.infrastructure.queue.celery_app import celery_app
from app.services.callback_service import CallbackService


callback_service = CallbackService("http://orchestrator/callback")


@celery_app.task(bind=True, max_retries=5, default_retry_delay=2)
def send_callback_task(self, payload):
    try:
        success = callback_service.send(payload)

        if not success:
            raise Exception("CALLBACK_FAILED")

        return True

    except Exception as exc:
        raise self.retry(exc=exc)
