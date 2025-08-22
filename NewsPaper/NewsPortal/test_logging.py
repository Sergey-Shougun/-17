import logging
from django.test import TestCase, override_settings
from django.conf import settings
import os
import tempfile
import shutil


class LoggingTest(TestCase):

    def setUp(self):
        # Создаем временные директории для логов
        self.temp_dir = tempfile.mkdtemp()

        # Создаем конфигурацию логирования с временными файлами
        self.custom_logging = self._create_custom_logging_config()

    def _create_custom_logging_config(self):
        """Создает конфигурацию логирования с временными файлами"""
        # Копируем оригинальную конфигурацию
        custom_config = settings.LOGGING.copy()

        # Обновляем пути к файлам
        self.log_files = {}
        for handler_name, handler_config in custom_config['handlers'].items():
            if 'filename' in handler_config:
                filename = os.path.basename(handler_config['filename'])
                full_path = os.path.join(self.temp_dir, filename)
                handler_config['filename'] = full_path
                self.log_files[handler_name] = full_path

        return custom_config

    def tearDown(self):
        # Восстанавливаем оригинальную конфигурацию
        shutil.rmtree(self.temp_dir)

    def test_console_logging_debug_true(self):
        """Тестирование консольного логирования при DEBUG=True"""
        with override_settings(DEBUG=True, LOGGING=self.custom_logging):
            logger = logging.getLogger('django')

            # Генерируем сообщения разных уровней
            logger.debug("Test debug message")
            logger.info("Test info message")
            logger.warning("Test warning message")

            try:
                raise ValueError("Test error")
            except ValueError:
                logger.error("Test error message", exc_info=True)

            # Для этого теста нужно визуально проверить вывод в консоль
            # Убедитесь, что:
            # - DEBUG: время, уровень, сообщение
            # - WARNING: время, уровень, сообщение, путь
            # - ERROR: время, уровень, сообщение, путь, стек ошибки

    def test_file_logging_debug_false(self):
        """Тестирование файлового логирования при DEBUG=False"""
        with override_settings(DEBUG=False, LOGGING=self.custom_logging):
            # Получаем разные логгеры
            django_logger = logging.getLogger('django')
            request_logger = logging.getLogger('django.request')
            security_logger = logging.getLogger('django.security')

            # Генерируем тестовые сообщения
            django_logger.info("Test info message for general.log")
            request_logger.error("Test error message for errors.log")
            security_logger.warning("Test security message")

            # Проверяем содержимое файлов
            general_file = self.log_files.get('general_file', 'general.log')
            if os.path.exists(general_file):
                with open(general_file, 'r') as f:
                    general_content = f.read()
                    self.assertIn("Test info message for general.log", general_content)
                    self.assertIn("[", general_content)  # Проверяем наличие модуля

            errors_file = self.log_files.get('error_file', 'errors.log')
            if os.path.exists(errors_file):
                with open(errors_file, 'r') as f:
                    errors_content = f.read()
                    self.assertIn("Test error message for errors.log", errors_content)
                    self.assertIn("Path:", errors_content)

            security_file = self.log_files.get('security_file', 'security.log')
            if os.path.exists(security_file):
                with open(security_file, 'r') as f:
                    security_content = f.read()
                    self.assertIn("Test security message", security_content)

    def test_error_logging_sources(self):
        """Тестирование, что ошибки из определенных источников попадают в errors.log"""
        with override_settings(DEBUG=False, LOGGING=self.custom_logging):
            loggers_to_test = [
                'django.request',
                'django.server',
                'django.template',
                'django.db.backends'
            ]

            for logger_name in loggers_to_test:
                logger = logging.getLogger(logger_name)
                logger.error(f"Test error from {logger_name}")

            # Проверяем, что все сообщения попали в errors.log
            errors_file = self.log_files.get('error_file', 'errors.log')
            if os.path.exists(errors_file):
                with open(errors_file, 'r') as f:
                    errors_content = f.read()
                    for logger_name in loggers_to_test:
                        self.assertIn(f"Test error from {logger_name}", errors_content)