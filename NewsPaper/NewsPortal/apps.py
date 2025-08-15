from django.apps import AppConfig
import os
import logging
import threading
import time
import sys
from django.db import connection
from django.db.utils import OperationalError

logger = logging.getLogger(__name__)


class NewsPortalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'NewsPortal'

    def ready(self):
        from . import signals

        if not os.environ.get('WERKZEUG_RUN_MAIN') and not os.environ.get('RUN_MAIN'):
            logger.info("Main process detected - starting scheduler")
            thread = threading.Thread(target=self.delayed_scheduler_start)
            thread.daemon = True
            thread.start()

    def delayed_scheduler_start(self):

        logger.info("Waiting for database to be ready...")

        max_retries = 10
        retry_delay = 5

        for i in range(max_retries):
            try:
                connection.ensure_connection()
                logger.info("Database connection established")
                break
            except OperationalError:
                if i == max_retries - 1:
                    logger.error("Database not available after retries")
                    return
                logger.warning(f"Database not ready. Retrying in {retry_delay} sec...")
                time.sleep(retry_delay)

        time.sleep(10)

        try:
            from .tasks import start_scheduler
            start_scheduler()
        except Exception as e:
            logger.error(f"Failed to start scheduler: {str(e)}")
