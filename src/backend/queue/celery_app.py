from celery import Celery
from config.backend_settings import get_backend_settings

settings = get_backend_settings()

celery_app = Celery(
    "telegram_backend",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    beat_scheduler="redbeat.RedBeatScheduler",
    redbeat_redis_url=settings.redis_url,
    beat_schedule={
        "drain-buffer-periodic": {
            "task": "backend.queue.tasks.drain_buffer_task",
            "schedule": settings.buffer_drain_interval_seconds,
        },
        "merge-topics-periodic": {
            "task": "backend.queue.tasks.merge_topics_task",
            "schedule": settings.merge_topics_interval_minutes * 60,
        },
        "split-topics-periodic": {
            "task": "backend.queue.tasks.split_topics_task",
            "schedule": settings.split_topics_interval_minutes * 60,
        },
    },
)

celery_app.autodiscover_tasks(["backend.queue"])
