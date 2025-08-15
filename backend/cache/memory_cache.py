"""
Модуль для локального кэша в памяти
"""

import time
from typing import Any, Optional, Dict, Tuple
from cachetools import TTLCache, LRUCache
from config import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)


class MemoryCache:
    """Класс для локального кэша в памяти"""
    
    def __init__(self):
        # TTL кэш для данных с временем жизни
        self.ttl_cache = TTLCache(
            maxsize=1000,  # Максимум 1000 элементов
            ttl=settings.redis_cache_ttl  # Время жизни в секундах
        )
        
        # LRU кэш для часто используемых данных
        self.lru_cache = LRUCache(maxsize=500)
        
        # Кэш для метаданных справочников (без TTL)
        self.meta_cache = LRUCache(maxsize=100)
        
        logger.info("Локальный кэш в памяти инициализирован")
    
    def get(self, key: str, cache_type: str = "ttl") -> Optional[Any]:
        """Получение значения из кэша"""
        try:
            if cache_type == "ttl":
                return self.ttl_cache.get(key)
            elif cache_type == "lru":
                return self.lru_cache.get(key)
            elif cache_type == "meta":
                return self.meta_cache.get(key)
            else:
                return None
                
        except Exception as e:
            logger.error(f"Ошибка получения из локального кэша: {e}")
            return None
    
    def set(self, key: str, value: Any, cache_type: str = "ttl") -> bool:
        """Установка значения в кэш"""
        try:
            if cache_type == "ttl":
                self.ttl_cache[key] = value
            elif cache_type == "lru":
                self.lru_cache[key] = value
            elif cache_type == "meta":
                self.meta_cache[key] = value
            else:
                return False
            
            logger.debug(f"Значение сохранено в локальный кэш: {key} ({cache_type})")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка сохранения в локальный кэш: {e}")
            return False
    
    def delete(self, key: str, cache_type: str = "all") -> bool:
        """Удаление значения из кэша"""
        try:
            if cache_type == "all":
                self.ttl_cache.pop(key, None)
                self.lru_cache.pop(key, None)
                self.meta_cache.pop(key, None)
            elif cache_type == "ttl":
                self.ttl_cache.pop(key, None)
            elif cache_type == "lru":
                self.lru_cache.pop(key, None)
            elif cache_type == "meta":
                self.meta_cache.pop(key, None)
            
            logger.debug(f"Значение удалено из локального кэша: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка удаления из локального кэша: {e}")
            return False
    
    def clear(self, cache_type: str = "all") -> bool:
        """Очистка кэша"""
        try:
            if cache_type == "all":
                self.ttl_cache.clear()
                self.lru_cache.clear()
                self.meta_cache.clear()
            elif cache_type == "ttl":
                self.ttl_cache.clear()
            elif cache_type == "lru":
                self.lru_cache.clear()
            elif cache_type == "meta":
                self.meta_cache.clear()
            
            logger.info(f"Локальный кэш очищен: {cache_type}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка очистки локального кэша: {e}")
            return False
    
    def get_stats(self) -> Dict[str, int]:
        """Получение статистики кэша"""
        return {
            "ttl_cache_size": len(self.ttl_cache),
            "lru_cache_size": len(self.lru_cache),
            "meta_cache_size": len(self.meta_cache),
            "total_size": len(self.ttl_cache) + len(self.lru_cache) + len(self.meta_cache)
        }


# Глобальный экземпляр локального кэша
memory_cache = MemoryCache() 