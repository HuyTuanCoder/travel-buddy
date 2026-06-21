import os
from celery import Celery

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://enterprise_user:enterprise_password@rabbitmq:5672//")

celery_app = Celery(
    "travel_buddy_ai",
    broker=RABBITMQ_URL,
    include=["src.workers.itinerary_tasks", "src.workers.memory_tasks"]
)

celery_app.conf.update(
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)
