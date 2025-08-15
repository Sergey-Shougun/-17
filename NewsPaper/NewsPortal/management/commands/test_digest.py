from django.core.management.base import BaseCommand
from ...tasks import send_weekly_digest
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Manually trigger weekly digest for testing'

    def handle(self, *args, **options):
        logger.info("=== Starting manual digest test ===")
        result = send_weekly_digest()
        logger.info(result)
        self.stdout.write(self.style.SUCCESS("Test digest completed"))