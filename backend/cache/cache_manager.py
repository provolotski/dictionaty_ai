"""
Универсальный кэш-менеджер
"""

import hashlib
import json
from typing import Any, Optional, Callable, Dict
from functools import wraps
import time

# from cache.redis_cache import redis_cache  # Временно отключаем Redis
from cache.memory_cache import memory_cache
from config import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)


class CacheManager:
    """Универсальный кэш-менеджер"""
    
    def __init__(self):
        self.redis_available = False
        self.memory_available = True
    
    async def initialize(self):
        """Инициализация кэш-менеджера"""
        # Попытка подключения к Redis (пропускаем для упрощения)
        self.redis_available = False
        
        logger.info("Кэш-менеджер: используется только локальный кэш")
    
    async def cleanup(self):
        """Очистка ресурсов"""
        if self.redis_available:
            await redis_cache.disconnect()
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Генерация ключа кэша"""
        # Создаем строку из аргументов
        key_parts = [prefix]
        
        # Добавляем позиционные аргументы
        for arg in args:
            key_parts.append(str(arg))
        
        # Добавляем именованные аргументы (отсортированные)
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            for key, value in sorted_kwargs:
                key_parts.append(f"{key}:{value}")
        
        # Создаем хеш от строки
        key_string = ":".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    async def get(self, key: str, cache_type: str = "auto") -> Optional[Any]:
        """Получение значения из кэша"""
        # Проверяем локальный кэш
        if self.memory_available:
            value = memory_cache.get(key, "ttl")
            if value is not None:
                logger.debug(f"Кэш-менеджер: значение найдено в локальном кэше: {key}")
                return value
        
        logger.debug(f"Кэш-менеджер: значение не найдено в кэше: {key}")
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None, cache_type: str = "auto") -> bool:
        """Установка значения в кэш"""
        success = True
        
        # Сохраняем в локальный кэш
        if self.memory_available:
            memory_cache.set(key, value, "ttl")
        
        if success:
            logger.debug(f"Кэш-менеджер: значение сохранено: {key}")
        
        return success
    
    async def delete(self, key: str, cache_type: str = "all") -> bool:
        """Удаление значения из кэша"""
        success = True
        
        # Удаляем из локального кэша
        if self.memory_available:
            memory_cache.delete(key, "all")
        
        if success:
            logger.debug(f"Кэш-менеджер: значение удалено: {key}")
        
        return success
    
    async def clear_pattern(self, pattern: str, cache_type: str = "all") -> bool:
        """Очистка кэша по паттерну"""
        success = True
        
        # Очищаем локальный кэш (полная очистка, так как нет паттернов)
        if self.memory_available and cache_type in ["all", "memory"]:
            memory_cache.clear("all")
        
        if success:
            logger.info(f"Кэш-менеджер: кэш очищен по паттерну: {pattern}")
        
        return success
    
    async def get_stats(self) -> Dict[str, Any]:
        """Получение статистики кэша"""
        stats = {
            "redis_available": self.redis_available,
            "memory_available": self.memory_available,
            "memory_stats": memory_cache.get_stats()
        }
        
        return stats


# Глобальный экземпляр кэш-менеджера
cache_manager = CacheManager()


def cached(prefix: str, ttl: Optional[int] = None, cache_type: str = "auto"):
    """
    Декоратор для кэширования результатов функций
    
    Args:
        prefix: Префикс для ключа кэша
        ttl: Время жизни кэша в секундах
        cache_type: Тип кэша ("auto", "memory", "redis")
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Генерируем ключ кэша
            cache_key = cache_manager._generate_key(prefix, *args, **kwargs)
            
            # Пытаемся получить из кэша
            cached_result = await cache_manager.get(cache_key, cache_type)
            if cached_result is not None:
                logger.debug(f"Кэш-декоратор: результат получен из кэша для {func.__name__}")
                return cached_result
            
            # Выполняем функцию
            start_time = time.time()
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Сохраняем результат в кэш
            await cache_manager.set(cache_key, result, ttl, cache_type)
            
            logger.debug(f"Кэш-декоратор: результат сохранен в кэш для {func.__name__} (время выполнения: {execution_time:.3f}s)")
            
            return result
        
        return wrapper
    return decorator


def invalidate_cache(prefix: str, cache_type: str = "all"):
    """
    Декоратор для инвалидации кэша после выполнения функции
    
    Args:
        prefix: Префикс для ключей кэша, которые нужно инвалидировать
        cache_type: Тип кэша для инвалидации
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Выполняем функцию
            result = await func(*args, **kwargs)
            
            # Инвалидируем кэш
            await cache_manager.clear_pattern(f"{prefix}*", cache_type)
            
            logger.debug(f"Кэш-декоратор: кэш инвалидирован для {func.__name__}")
            
            return result
        
        return wrapper
    return decorator 