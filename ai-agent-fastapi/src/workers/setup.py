import os
from celery import Celery
from src.core.telemetry import setup_telemetry
from src.core.config import settings

setup_telemetry()

RABBITMQ_URL = settings.RABBITMQ_URL

celery_app = Celery(
    "travel_buddy_ai",
    broker=RABBITMQ_URL,
    include=["src.workers.itinerary_tasks", "src.workers.memory_tasks"]
)

celery_app.conf.update(
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    # Task timeouts: soft limit raises SoftTimeLimitExceeded, hard limit kills the worker
    task_soft_time_limit=90,
    task_time_limit=120,
    # Broker connection retry on startup
    broker_connection_retry_on_startup=True,
)
