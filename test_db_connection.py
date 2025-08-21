#!/usr/bin/env python3
"""
Тестовый скрипт для проверки подключения к базе данных
"""

import asyncio
import sys
import os

# Добавляем путь к backend в sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

async def test_database_connection():
    """Тестирование подключения к базе данных"""
    try:
        from database import database, check_database_connection
        
        print("=== Тестирование подключения к базе данных ===\n")
        
        # Проверяем подключение
        print("1. Проверка подключения к базе данных...")
        is_connected = await check_database_connection()
        print(f"Результат: {is_connected}")
        
        if is_connected:
            print("2. Подключение к базе данных...")
            await database.connect()
            print("Подключение успешно")
            
            # Проверяем таблицу users
            print("3. Проверка таблицы users...")
            query = "SELECT COUNT(*) FROM users"
            result = await database.fetch_val(query=query)
            print(f"Количество пользователей в таблице: {result}")
            
            # Проверяем структуру таблицы
            print("4. Проверка структуры таблицы users...")
            query = """
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'users' 
                ORDER BY ordinal_position
            """
            columns = await database.fetch_all(query=query)
            print("Структура таблицы users:")
            for col in columns:
                print(f"  - {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']})")
            
            # Отключаемся от базы данных
            await database.disconnect()
            print("Отключение от базы данных успешно")
            
        else:
            print("Не удалось подключиться к базе данных")
            
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_database_connection())
