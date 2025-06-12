from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()

celery = Celery(
    "worker",
    broker=os.getenv("CELERY_BROKER_URL", "amqp://guest:guest@34.47.181.15:5672//"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "rpc://")
)

# Improved configuration
celery.conf.update(
    task_track_started=True,
    result_persistent=True,
    worker_send_task_events=True,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

# Explicit task routing
celery.conf.task_routes = {
    'app.tasks.compress_and_upload': {'queue': 'compression'},
}

# Ensure tasks from the app module are registered
celery.autodiscover_tasks(['app'])