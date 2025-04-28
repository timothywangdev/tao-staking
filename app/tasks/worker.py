import os
from celery import Celery
import logging
from app.config import settings

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# Get Redis connection URL from environment variable
logger.info(f"Redis connection URL: {settings.REDIS_URL}")

# create celery application
celery_app = Celery(
    "celery",
    backend=settings.REDIS_URL,
    broker=settings.REDIS_URL,
)
