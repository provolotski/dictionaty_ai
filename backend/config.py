"""
Конфигурация приложения с использованием pydantic-settings
"""

import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/belstat"
    
    # PostgreSQL specific settings
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_SCHEMA: str = "public"
    POSTGRES_DB: str = "belstat"
    
    # API settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Dictionary Management System API"
    API_HOST: str = "0.0.0.0"
    API_PORT: str = "8000"
    
    # Logging settings
    LOG_LEVEL: str = "DEBUG"
    LOG_FORMAT: str = "%(asctime)s %(levelname)s %(module)s %(funcName)s %(lineno)d %(message)s"
    LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S %Z"
    LOG_FILE: str = "logs/backend.log"
    
    # Timezone settings
    TIMEZONE: str = "Europe/Minsk"
    
    # CORS settings
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8080,http://127.0.0.1:8000"
    CORS_ALLOW_METHODS: str = "GET,POST,PUT,DELETE,OPTIONS"
    CORS_ALLOW_HEADERS: str = "Content-Type,Authorization"
    
    # Redis settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: str = "6379"
    REDIS_DB: str = "0"
    REDIS_PASSWORD: str = ""
    REDIS_USE_CACHE: str = "true"
    REDIS_CACHE_TTL: str = "3600"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"  # Разрешаем дополнительные поля

settings = Settings()

# Настройки логирования с учетом временной зоны
import logging
import logging.handlers
from datetime import datetime
import pytz

def setup_logging():
    """Настройка логирования с временной зоной Minsk"""
    # Создаем форматтер с временной зоной
    class TimezoneFormatter(logging.Formatter):
        def formatTime(self, record, datefmt=None):
            # Конвертируем время в временную зону Minsk
            dt = datetime.fromtimestamp(record.created, tz=pytz.UTC)
            minsk_tz = pytz.timezone('Europe/Minsk')
            dt_minsk = dt.astimezone(minsk_tz)
            return dt_minsk.strftime(datefmt or self.datefmt)
    
    # Настраиваем корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Создаем форматтер
    formatter = TimezoneFormatter(
        fmt=settings.LOG_FORMAT,
        datefmt=settings.LOG_DATE_FORMAT
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
    console_handler.setLevel(logging.DEBUG)
    
    # Добавляем хендлеры
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Настраиваем логгеры для конкретных модулей
    app_logger = logging.getLogger('app')
    app_logger.setLevel(logging.DEBUG)
    app_logger.addHandler(file_handler)
    
    return root_logger
