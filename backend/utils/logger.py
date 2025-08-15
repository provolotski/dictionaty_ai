"""
Централизованное логирование для приложения
"""

import logging
import logging.handlers
import sys
from typing import Optional, Dict, Any
from datetime import datetime
from config import settings


def setup_logger(name: str = __name__, level: Optional[str] = None) -> logging.Logger:
    """
    Настройка логгера с централизованной конфигурацией
    
    Args:
        name: Имя логгера
        level: Уровень логирования (если не указан, берется из настроек)
        
    Returns:
        logging.Logger: Настроенный логгер
    """
    logger = logging.getLogger(name)
    
    # Если логгер уже настроен, возвращаем его
    if logger.handlers:
        return logger
    
    # Устанавливаем уровень логирования
    log_level = level or settings.log_level
    logger.setLevel(getattr(logging, log_level))
    
    # Создаем форматтер с расширенной информацией
    formatter = logging.Formatter(
        settings.log_format,
        datefmt=settings.log_date
    )
    
    # Хендлер для файла с ротацией
    file_handler = logging.handlers.RotatingFileHandler(
        settings.log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Хендлер для консоли
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Хендлер для ошибок (отдельный файл)
    error_handler = logging.handlers.RotatingFileHandler(
        settings.log_file.replace('.log', '_errors.log'),
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)
    
    return logger


def log_api_request(logger: logging.Logger, method: str, url: str, status_code: int, 
                   response_time: float, user_info: Optional[Dict] = None, 
                   ip_address: Optional[str] = None):
    """
    Логирует API запросы с автоматическим добавлением даты и времени
    
    Args:
        logger: Логгер для записи
        method: HTTP метод
        url: URL запроса
        status_code: HTTP статус код
        response_time: Время ответа в секундах
        user_info: Информация о пользователе
        ip_address: IP адрес
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    log_data = {
        'timestamp': timestamp,
        'method': method,
        'url': url,
        'status_code': status_code,
        'response_time': f"{response_time:.3f}s"
    }
    
    if user_info:
        log_data['user'] = user_info
    if ip_address:
        log_data['ip_address'] = ip_address
    
    if 200 <= status_code < 400:
        logger.info(f"API_REQUEST: {method} {url} - {status_code} ({response_time:.3f}s)")
    else:
        logger.warning(f"API_REQUEST_ERROR: {method} {url} - {status_code} ({response_time:.3f}s)")
    
    return log_data


def log_database_operation(logger: logging.Logger, operation: str, table: str, 
                          record_id: Optional[int] = None, success: bool = True, 
                          error_message: Optional[str] = None, execution_time: Optional[float] = None):
    """
    Логирует операции с базой данных с автоматическим добавлением даты и времени
    
    Args:
        logger: Логгер для записи
        operation: Тип операции (SELECT, INSERT, UPDATE, DELETE)
        table: Имя таблицы
        record_id: ID записи
        success: Успешность операции
        error_message: Сообщение об ошибке
        execution_time: Время выполнения в секундах
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    log_data = {
        'timestamp': timestamp,
        'operation': operation,
        'table': table,
        'success': success
    }
    
    if record_id:
        log_data['record_id'] = record_id
    if execution_time:
        log_data['execution_time'] = f"{execution_time:.3f}s"
    if error_message:
        log_data['error'] = error_message
    
    if success:
        logger.info(f"DB_OPERATION: {operation} on {table} - Success")
    else:
        logger.error(f"DB_OPERATION_FAILED: {operation} on {table} - Error: {error_message}")
    
    return log_data


def log_user_action(logger: logging.Logger, action: str, details: Dict[str, Any], 
                   user_info: Optional[Dict] = None, ip_address: Optional[str] = None, 
                   success: bool = True):
    """
    Логирует действия пользователя с автоматическим добавлением даты и времени
    
    Args:
        logger: Логгер для записи
        action: Описание действия
        details: Детали действия
        user_info: Информация о пользователе
        ip_address: IP адрес пользователя
        success: Успешность действия
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    log_data = {
        'timestamp': timestamp,
        'action': action,
        'success': success,
        'details': details
    }
    
    if user_info:
        log_data['user'] = user_info
    if ip_address:
        log_data['ip_address'] = ip_address
    
    if success:
        logger.info(f"USER_ACTION: {action} - {details}")
    else:
        logger.warning(f"USER_ACTION_FAILED: {action} - {details}")
    
    return log_data


# Создаем основной логгер приложения
app_logger = setup_logger("dictionary_api") 