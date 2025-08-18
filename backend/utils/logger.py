"""
Централизованное логирование для приложения
"""

import logging
import logging.handlers
import os
from datetime import datetime
import pytz

def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    """
    Настройка логгера с временной зоной Minsk
    """
    # Создаем директорию для логов если её нет
    os.makedirs('logs', exist_ok=True)
    
    # Создаем форматтер с временной зоной
    class TimezoneFormatter(logging.Formatter):
        def formatTime(self, record, datefmt=None):
            # Конвертируем время в временную зону Minsk
            dt = datetime.fromtimestamp(record.created, tz=pytz.UTC)
            minsk_tz = pytz.timezone('Europe/Minsk')
            dt_minsk = dt.astimezone(minsk_tz)
            return dt_minsk.strftime(datefmt or self.datefmt)
    
    # Создаем логгер
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Проверяем, не добавлены ли уже хендлеры
    if logger.handlers:
        return logger
    
    # Создаем форматтер
    formatter = TimezoneFormatter(
        fmt='%(asctime)s %(levelname)s %(module)s %(funcName)s %(lineno)d %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S %Z'
    )
    
    # Хендлер для файла
    file_handler = logging.handlers.RotatingFileHandler(
        'logs/backend.log',
        maxBytes=10*1024*1024,  # 10 MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    
    # Хендлер для консоли
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    
    # Добавляем хендлеры
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def log_api_request(logger: logging.Logger, method: str, url: str, status_code: int = None, response_time: float = None):
    """Логирование API запросов"""
    if status_code:
        if response_time:
            logger.info(f"API_REQUEST → {method} {url} → {status_code} ({response_time:.3f}s)")
        else:
            logger.info(f"API_REQUEST → {method} {url} → {status_code}")
    else:
        logger.info(f"API_REQUEST → {method} {url}")

def log_database_operation(logger: logging.Logger, operation: str, table: str, details: str = None):
    """Логирование операций с базой данных"""
    if details:
        logger.info(f"DB_OPERATION → {operation} {table} → {details}")
    else:
        logger.info(f"DB_OPERATION → {operation} {table}")

def log_user_action(logger: logging.Logger, user_id: str, action: str, details: str = None):
    """Логирование действий пользователя"""
    if details:
        logger.info(f"USER_ACTION → {user_id} {action} → {details}")
    else:
        logger.info(f"USER_ACTION → {user_id} {action}")

def error_handler(logger: logging.Logger, error: Exception, context: str = None):
    """Обработчик ошибок с логированием"""
    if context:
        logger.error(f"ERROR in {context}: {error}")
    else:
        logger.error(f"ERROR: {error}") 