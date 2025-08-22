import os

from django.core.management.base import BaseCommand
import logging


class Command(BaseCommand):
    help = 'Ручное тестирование системы логирования'

    def handle(self, *args, **options):
        # Тестирование разных логгеров и уровней
        loggers = {
            'django': logging.getLogger('django'),
            'django.request': logging.getLogger('django.request'),
            'django.security': logging.getLogger('django.security'),
            'django.db.backends': logging.getLogger('django.db.backends'),
            'django.template': logging.getLogger('django.template'),
            'django.server': logging.getLogger('django.server'),
        }

        # Тестирование разных уровней логирования
        for name, logger in loggers.items():
            self.stdout.write(f"\nТестирование логгера: {name}")

            logger.debug(f"DEBUG сообщение от {name}")
            logger.info(f"INFO сообщение от {name}")
            logger.warning(f"WARNING сообщение от {name}")

            try:
                raise ValueError("Тестовая ошибка")
            except ValueError:
                logger.error(f"ERROR сообщение от {name}", exc_info=True)

        self.stdout.write(self.style.SUCCESS(
            "Тестирование завершено. Проверьте логи и консоль для проверки результатов."
        ))
        log_files = ['general.log', 'errors.log', 'security.log']
        for log_file in log_files:
            if os.path.exists(log_file):
                self.stdout.write(f"Файл {log_file} создан")
                with open(log_file, 'r') as f:
                    content = f.read()
                    self.stdout.write(f"Содержимое {log_file}:\n{content}")
            else:
                self.stdout.write(f"Файл {log_file} не создан")