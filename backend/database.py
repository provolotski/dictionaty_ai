"""
Модуль для работы с базой данных
"""

import logging
import databases
from config import settings

# Настройка логирования для базы данных
logging.getLogger("databases").setLevel(logging.WARNING)
logging.getLogger("asyncpg").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Формируем URL для подключения к базе данных
DATABASE_URL = (
    f"postgresql://{settings.POSTGRES_USER}:"
    f"{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:"
    f"{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
)

# Создаем экземпляр базы данных
database = databases.Database(DATABASE_URL)


async def get_database() -> databases.Database:
    """
    Получение экземпляра базы данных для dependency injection
    
    Returns:
        databases.Database: Экземпляр базы данных
    """
    return database


async def check_database_connection() -> bool:
    """
    Проверка подключения к базе данных
    
    Returns:
        bool: True если подключение успешно, False в противном случае
    """
    try:
        await database.connect()
        await database.disconnect()
        logger.info("Подключение к базе данных успешно")
        return True
    except Exception as e:
        logger.error(f"Ошибка подключения к базе данных: {e}")
        return False
