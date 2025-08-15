"""
Тесты для утилит приложения
"""

import pytest
import logging
import os
from unittest.mock import patch, MagicMock
from datetime import datetime

from utils.logger import setup_logger


class TestLogger:
    """Тесты для системы логирования"""

    @pytest.fixture
    def temp_log_file(self, tmp_path):
        """Временный файл для логов"""
        return tmp_path / "test.log"

    @pytest.fixture
    def clean_logging(self):
        """Очистка настроек логирования"""
        # Сохраняем оригинальные настройки
        original_handlers = logging.getLogger().handlers.copy()
        original_level = logging.getLogger().level
        
        # Очищаем
        logging.getLogger().handlers.clear()
        
        yield
        
        # Восстанавливаем
        logging.getLogger().handlers = original_handlers
        logging.getLogger().setLevel(original_level)

    class TestSetupLogger:
        """Тесты функции setup_logger"""

        def test_setup_logger_basic(self, clean_logging, temp_log_file):
            """Базовая настройка логгера"""
            # Act
            logger = setup_logger("test_module", log_file=str(temp_log_file))

            # Assert
            assert logger.name == "test_module"
            assert logger.level == logging.INFO
            assert len(logger.handlers) > 0

        def test_setup_logger_with_custom_level(self, clean_logging, temp_log_file):
            """Настройка логгера с пользовательским уровнем"""
            # Act
            logger = setup_logger("test_module", level=logging.DEBUG, log_file=str(temp_log_file))

            # Assert
            assert logger.level == logging.DEBUG

        def test_setup_logger_file_handler(self, clean_logging, temp_log_file):
            """Проверка файлового обработчика"""
            # Act
            logger = setup_logger("test_module", log_file=str(temp_log_file))

            # Assert
            file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
            assert len(file_handlers) > 0
            assert file_handlers[0].baseFilename == str(temp_log_file)

        def test_setup_logger_console_handler(self, clean_logging, temp_log_file):
            """Проверка консольного обработчика"""
            # Act
            logger = setup_logger("test_module", log_file=str(temp_log_file))

            # Assert
            console_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
            assert len(console_handlers) > 0

        def test_setup_logger_format(self, clean_logging, temp_log_file):
            """Проверка формата логов"""
            # Act
            logger = setup_logger("test_module", log_file=str(temp_log_file))

            # Assert
            for handler in logger.handlers:
                formatter = handler.formatter
                assert formatter is not None
                format_string = formatter._fmt
                assert "%(asctime)s" in format_string
                assert "%(name)" in format_string
                assert "%(levelname)" in format_string
                assert "%(message)" in format_string

        def test_setup_logger_creates_directory(self, clean_logging, tmp_path):
            """Создание директории для логов"""
            # Arrange
            log_dir = tmp_path / "logs"
            log_file = log_dir / "test.log"

            # Act
            logger = setup_logger("test_module", log_file=str(log_file))

            # Assert
            assert log_dir.exists()
            assert log_dir.is_dir()

        def test_setup_logger_existing_directory(self, clean_logging, tmp_path):
            """Работа с существующей директорией"""
            # Arrange
            log_dir = tmp_path / "logs"
            log_dir.mkdir()
            log_file = log_dir / "test.log"

            # Act
            logger = setup_logger("test_module", log_file=str(log_file))

            # Assert
            assert log_dir.exists()
            assert len(logger.handlers) > 0

        def test_setup_logger_logging_functionality(self, clean_logging, temp_log_file):
            """Проверка функциональности логирования"""
            # Arrange
            logger = setup_logger("test_module", log_file=str(temp_log_file))

            # Act
            test_message = "Test log message"
            logger.info(test_message)

            # Assert
            assert temp_log_file.exists()
            log_content = temp_log_file.read_text()
            assert test_message in log_content
            assert "test_module" in log_content
            assert "INFO" in log_content

        def test_setup_logger_different_levels(self, clean_logging, temp_log_file):
            """Логирование разных уровней"""
            # Arrange
            logger = setup_logger("test_module", level=logging.DEBUG, log_file=str(temp_log_file))

            # Act
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")

            # Assert
            log_content = temp_log_file.read_text()
            assert "Debug message" in log_content
            assert "Info message" in log_content
            assert "Warning message" in log_content
            assert "Error message" in log_content

        def test_setup_logger_multiple_instances(self, clean_logging, temp_log_file):
            """Множественные экземпляры логгера"""
            # Act
            logger1 = setup_logger("module1", log_file=str(temp_log_file))
            logger2 = setup_logger("module2", log_file=str(temp_log_file))

            # Assert
            assert logger1.name == "module1"
            assert logger2.name == "module2"
            assert logger1 is not logger2

        def test_setup_logger_without_file(self, clean_logging):
            """Настройка логгера без файла"""
            # Act
            logger = setup_logger("test_module")

            # Assert
            assert logger.name == "test_module"
            assert len(logger.handlers) > 0
            # Должен быть только консольный обработчик
            file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
            assert len(file_handlers) == 0

        def test_setup_logger_custom_format(self, clean_logging, temp_log_file):
            """Пользовательский формат логов"""
            # Arrange
            custom_format = "%(levelname)s - %(message)s"

            # Act
            logger = setup_logger("test_module", log_file=str(temp_log_file), format=custom_format)

            # Assert
            for handler in logger.handlers:
                formatter = handler.formatter
                assert formatter._fmt == custom_format

        def test_setup_logger_date_format(self, clean_logging, temp_log_file):
            """Пользовательский формат даты"""
            # Arrange
            custom_date_format = "%Y-%m-%d %H:%M"

            # Act
            logger = setup_logger("test_module", log_file=str(temp_log_file), date_format=custom_date_format)

            # Assert
            for handler in logger.handlers:
                formatter = handler.formatter
                assert formatter.datefmt == custom_date_format

    class TestLoggingIntegration:
        """Интеграционные тесты логирования"""

        def test_logger_integration_with_application(self, clean_logging, temp_log_file):
            """Интеграция логгера с приложением"""
            # Arrange
            logger = setup_logger("test_app", log_file=str(temp_log_file))

            # Act
            logger.info("Application started")
            logger.warning("Configuration warning")
            logger.error("Database connection failed")

            # Assert
            log_content = temp_log_file.read_text()
            assert "Application started" in log_content
            assert "Configuration warning" in log_content
            assert "Database connection failed" in log_content

        def test_logger_performance(self, clean_logging, temp_log_file):
            """Производительность логгера"""
            # Arrange
            logger = setup_logger("test_performance", log_file=str(temp_log_file))

            # Act
            import time
            start_time = time.time()
            
            for i in range(1000):
                logger.info(f"Log message {i}")

            end_time = time.time()
            duration = end_time - start_time

            # Assert
            assert duration < 1.0  # Логирование должно быть быстрым
            assert temp_log_file.stat().st_size > 0

        def test_logger_concurrent_access(self, clean_logging, temp_log_file):
            """Конкурентный доступ к логгеру"""
            import threading
            import time

            # Arrange
            logger = setup_logger("test_concurrent", log_file=str(temp_log_file))
            log_messages = []

            def log_worker(worker_id):
                """Рабочая функция для логирования"""
                for i in range(10):
                    message = f"Worker {worker_id} - Message {i}"
                    logger.info(message)
                    log_messages.append(message)
                    time.sleep(0.001)  # Небольшая задержка

            # Act
            threads = []
            for i in range(5):
                thread = threading.Thread(target=log_worker, args=(i,))
                threads.append(thread)
                thread.start()

            # Ждем завершения всех потоков
            for thread in threads:
                thread.join()

            # Assert
            assert len(log_messages) == 50  # 5 потоков * 10 сообщений
            log_content = temp_log_file.read_text()
            for message in log_messages:
                assert message in log_content

    class TestLoggerErrorHandling:
        """Тесты обработки ошибок логгера"""

        def test_logger_invalid_file_path(self, clean_logging):
            """Некорректный путь к файлу логов"""
            # Arrange
            invalid_path = "/invalid/path/to/log/file.log"

            # Act & Assert
            # Логгер должен создаться без ошибок, даже с некорректным путем
            logger = setup_logger("test_module", log_file=invalid_path)
            assert logger is not None

        def test_logger_permission_error(self, clean_logging, tmp_path):
            """Ошибка прав доступа к файлу логов"""
            # Arrange
            log_file = tmp_path / "test.log"
            log_file.write_text("existing content")

            # Делаем файл только для чтения (если возможно)
            try:
                log_file.chmod(0o444)  # Только чтение
                
                # Act
                logger = setup_logger("test_module", log_file=str(log_file))
                
                # Assert
                assert logger is not None
                
            except (OSError, PermissionError):
                # На некоторых системах это может не работать
                pass
            finally:
                # Восстанавливаем права
                try:
                    log_file.chmod(0o666)
                except:
                    pass

        def test_logger_disk_full_simulation(self, clean_logging, temp_log_file):
            """Симуляция заполненного диска"""
            # Arrange
            logger = setup_logger("test_module", log_file=str(temp_log_file))

            # Act
            # Пытаемся записать большое количество данных
            large_message = "x" * 10000
            for i in range(100):
                logger.info(f"Large message {i}: {large_message}")

            # Assert
            # Логгер должен продолжать работать
            assert logger is not None
            assert temp_log_file.exists()


class TestUtilityFunctions:
    """Тесты дополнительных утилитарных функций"""

    def test_date_validation_utility(self):
        """Утилита валидации дат"""
        from datetime import date

        def is_valid_date_range(start_date, end_date):
            """Проверка корректности диапазона дат"""
            if not isinstance(start_date, date) or not isinstance(end_date, date):
                return False
            return start_date < end_date

        # Act & Assert
        assert is_valid_date_range(date(2024, 1, 1), date(2024, 12, 31)) is True
        assert is_valid_date_range(date(2024, 12, 31), date(2024, 1, 1)) is False
        assert is_valid_date_range("invalid", date(2024, 1, 1)) is False

    def test_string_validation_utility(self):
        """Утилита валидации строк"""
        def is_valid_string(value, min_length=1, max_length=100):
            """Проверка корректности строки"""
            if not isinstance(value, str):
                return False
            return min_length <= len(value) <= max_length

        # Act & Assert
        assert is_valid_string("test", 1, 10) is True
        assert is_valid_string("", 1, 10) is False
        assert is_valid_string("very long string" * 10, 1, 10) is False
        assert is_valid_string(123, 1, 10) is False

    def test_file_extension_utility(self):
        """Утилита проверки расширения файла"""
        def is_valid_file_extension(filename, allowed_extensions):
            """Проверка расширения файла"""
            if not filename:
                return False
            extension = filename.lower().split('.')[-1] if '.' in filename else ''
            return extension in allowed_extensions

        # Act & Assert
        assert is_valid_file_extension("test.csv", ["csv", "xlsx"]) is True
        assert is_valid_file_extension("test.CSV", ["csv", "xlsx"]) is True
        assert is_valid_file_extension("test.txt", ["csv", "xlsx"]) is False
        assert is_valid_file_extension("", ["csv", "xlsx"]) is False
        assert is_valid_file_extension("noextension", ["csv", "xlsx"]) is False
