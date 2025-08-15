#!/usr/bin/env python3
"""
Скрипт для применения миграции базы данных
Добавляет поля created_at и updated_at в таблицу dictionary
"""

import asyncio
import logging
from pathlib import Path

from database import database
from config import settings

# Настройка логирования
logging.basicConfig(
    level=settings.log_level,
    format=settings.log_format,
    datefmt=settings.log_date,
    handlers=[logging.FileHandler(settings.log_file), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


async def apply_migration():
    """Применяет миграцию для добавления полей created_at и updated_at"""
    
    migration_sql = """
    -- Добавляем поля created_at и updated_at
    ALTER TABLE dictionary 
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

    -- Обновляем существующие записи, устанавливая created_at и updated_at равными change_date
    -- Если change_date NULL, используем текущую дату
    UPDATE dictionary 
    SET 
        created_at = COALESCE(change_date::timestamp, CURRENT_TIMESTAMP),
        updated_at = COALESCE(change_date::timestamp, CURRENT_TIMESTAMP)
    WHERE created_at IS NULL OR updated_at IS NULL;

    -- Создаем функцию для автоматического обновления updated_at
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = CURRENT_TIMESTAMP;
        RETURN NEW;
    END;
    $$ language 'plpgsql';

    -- Создаем триггер для автоматического обновления updated_at
    DROP TRIGGER IF EXISTS update_dictionary_updated_at ON dictionary;
    CREATE TRIGGER update_dictionary_updated_at 
        BEFORE UPDATE ON dictionary 
        FOR EACH ROW 
        EXECUTE FUNCTION update_updated_at_column();
    """
    
    try:
        logger.info("Начинаем применение миграции...")
        
        # Выполняем миграцию
        await database.execute(migration_sql)
        
        logger.info("Миграция успешно применена!")
        
        # Проверяем, что поля добавлены
        check_sql = """
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'dictionary' 
        AND column_name IN ('created_at', 'updated_at')
        ORDER BY column_name;
        """
        
        result = await database.fetch_all(check_sql)
        logger.info(f"Проверка полей: {result}")
        
    except Exception as e:
        logger.error(f"Ошибка при применении миграции: {e}")
        raise
    finally:
        await database.disconnect()


if __name__ == "__main__":
    asyncio.run(apply_migration())
