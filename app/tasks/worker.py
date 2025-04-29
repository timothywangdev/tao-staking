from celery import Celery
from app.config import settings
from app.utils import setting_celery_logging

# Set up Loki logging for Celery
setting_celery_logging(settings.LOKI_URL)

# create celery application
celery_app = Celery(
    "tao_dividends",
    backend=settings.REDIS_URL,
    broker=settings.REDIS_URL,
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=900,  # 15 minutes
    task_soft_time_limit=600,  # 10 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    # Add logging configuration
    worker_hijack_root_logger=False,  # Don't hijack root logger
    worker_log_format="%(asctime)s %(levelname)s [%(processName)s] [%(name)s] %(message)s",
    worker_task_log_format="%(asctime)s %(levelname)s [%(processName)s] [%(name)s] [%(task_name)s(%(task_id)s)] %(message)s",
)
