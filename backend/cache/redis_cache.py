"""
Модуль для работы с Redis кэшем
"""

import json
import pickle
from typing import Any, Optional, Union
import aioredis
from config import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)


class RedisCache:
    """Класс для работы с Redis кэшем"""
    
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self.connected = False
        self.prefix = "dictionary_api:"
    
    async def connect(self) -> bool:
        """Подключение к Redis"""
        try:
            if settings.redis_password:
                self.redis = aioredis.Redis(
                    host=settings.redis_host,
                    port=settings.redis_port,
                    db=settings.redis_db,
                    password=settings.redis_password,
                    decode_responses=False,
                    encoding="utf-8"
                )
            else:
                self.redis = aioredis.Redis(
                    host=settings.redis_host,
                    port=settings.redis_port,
                    db=settings.redis_db,
                    decode_responses=False,
                    encoding="utf-8"
                )
            
            # Проверка подключения
            await self.redis.ping()
            self.connected = True
            logger.info(f"Подключение к Redis успешно: {settings.redis_host}:{settings.redis_port}")
            return True
            
        except Exception as e:
            logger.warning(f"Не удалось подключиться к Redis: {e}")
            self.connected = False
            return False
    
    async def disconnect(self):
        """Отключение от Redis"""
        if self.redis:
            await self.redis.close()
            self.connected = False
            logger.info("Отключение от Redis")
    
    def _get_key(self, key: str) -> str:
        """Получение полного ключа с префиксом"""
        return f"{self.prefix}{key}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Получение значения из кэша"""
        if not self.connected or not settings.redis_use_cache:
            return None
        
        try:
            full_key = self._get_key(key)
            value = await self.redis.get(full_key)
            
            if value is None:
                return None
            
            # Попытка десериализации JSON
            try:
                return json.loads(value.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                # Если не JSON, попробуем pickle
                try:
                    return pickle.loads(value)
                except:
                    return value.decode('utf-8')
                    
        except Exception as e:
            logger.error(f"Ошибка получения из кэша: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Установка значения в кэш"""
        if not self.connected or not settings.redis_use_cache:
            return False
        
        try:
            full_key = self._get_key(key)
            
            # Попытка сериализации в JSON
            try:
                serialized_value = json.dumps(value, ensure_ascii=False, default=str)
            except (TypeError, ValueError):
                # Если не удается сериализовать в JSON, используем pickle
                serialized_value = pickle.dumps(value)
            
            ttl = ttl or settings.redis_cache_ttl
            await self.redis.setex(full_key, ttl, serialized_value)
            
            logger.debug(f"Значение сохранено в кэш: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка сохранения в кэш: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Удаление значения из кэша"""
        if not self.connected:
            return False
        
        try:
            full_key = self._get_key(key)
            await self.redis.delete(full_key)
            logger.debug(f"Значение удалено из кэша: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка удаления из кэша: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> bool:
        """Очистка кэша по паттерну"""
        if not self.connected:
            return False
        
        try:
            full_pattern = self._get_key(pattern)
            keys = await self.redis.keys(full_pattern)
            
            if keys:
                await self.redis.delete(*keys)
                logger.info(f"Удалено {len(keys)} ключей из кэша по паттерну: {pattern}")
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка очистки кэша по паттерну: {e}")
            return False
    
    async def clear_all(self) -> bool:
        """Очистка всего кэша приложения"""
        return await self.clear_pattern("*")


# Глобальный экземпляр кэша
redis_cache = RedisCache() 