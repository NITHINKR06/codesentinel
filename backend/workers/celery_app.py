from celery import Celery
from config import settings

celery_app = Celery(
    "codesentinel",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["workers.scan_worker"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_soft_time_limit=300,
    task_time_limit=360,
    worker_prefetch_multiplier=1,
)
