"""
Тесты для кэш-менеджера
"""

import pytest
import hashlib
import json
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta

from cache.cache_manager import CacheManager, cached, invalidate_cache, cache_manager


class TestCacheManager:
    """Тесты для класса CacheManager"""

    @pytest.fixture
    def cache_manager_instance(self):
        """Экземпляр кэш-менеджера"""
        return CacheManager()

    @pytest.fixture
    def sample_data(self):
        """Тестовые данные"""
        return {
            "id": 1,
            "name": "Test Dictionary",
            "code": "test_001",
            "created_at": datetime.now().isoformat()
        }

    class TestInitialization:
        """Тесты инициализации"""

        @pytest.mark.asyncio
        async def test_initialize_success(self, cache_manager_instance):
            """Успешная инициализация кэш-менеджера"""
            # Act
            await cache_manager_instance.initialize()

            # Assert
            assert cache_manager_instance.memory_available is True
            assert cache_manager_instance.redis_available is False

        @pytest.mark.asyncio
        async def test_cleanup_success(self, cache_manager_instance):
            """Успешная очистка ресурсов"""
            # Act
            await cache_manager_instance.cleanup()

            # Assert
            # Очистка прошла без ошибок

    class TestKeyGeneration:
        """Тесты генерации ключей"""

        def test_generate_key_simple(self, cache_manager_instance):
            """Генерация простого ключа"""
            # Act
            key = cache_manager_instance._generate_key("test_prefix", "arg1", "arg2")

            # Assert
            assert isinstance(key, str)
            assert len(key) == 32  # MD5 hash length

        def test_generate_key_with_kwargs(self, cache_manager_instance):
            """Генерация ключа с именованными аргументами"""
            # Act
            key = cache_manager_instance._generate_key(
                "test_prefix", 
                "arg1", 
                param1="value1", 
                param2="value2"
            )

            # Assert
            assert isinstance(key, str)
            assert len(key) == 32

        def test_generate_key_consistent(self, cache_manager_instance):
            """Консистентность генерации ключей"""
            # Act
            key1 = cache_manager_instance._generate_key("prefix", "arg1", "arg2")
            key2 = cache_manager_instance._generate_key("prefix", "arg1", "arg2")

            # Assert
            assert key1 == key2

        def test_generate_key_different_args(self, cache_manager_instance):
            """Разные ключи для разных аргументов"""
            # Act
            key1 = cache_manager_instance._generate_key("prefix", "arg1")
            key2 = cache_manager_instance._generate_key("prefix", "arg2")

            # Assert
            assert key1 != key2

    class TestCacheOperations:
        """Тесты операций с кэшем"""

        @pytest.mark.asyncio
        async def test_set_and_get_success(self, cache_manager_instance, sample_data):
            """Успешная установка и получение значения"""
            # Arrange
            key = "test_key"
            ttl = 3600

            # Act
            set_result = await cache_manager_instance.set(key, sample_data, ttl)
            get_result = await cache_manager_instance.get(key)

            # Assert
            assert set_result is True
            assert get_result == sample_data

        @pytest.mark.asyncio
        async def test_get_nonexistent_key(self, cache_manager_instance):
            """Получение несуществующего ключа"""
            # Act
            result = await cache_manager_instance.get("nonexistent_key")

            # Assert
            assert result is None

        @pytest.mark.asyncio
        async def test_delete_existing_key(self, cache_manager_instance, sample_data):
            """Удаление существующего ключа"""
            # Arrange
            key = "test_key"
            await cache_manager_instance.set(key, sample_data)

            # Act
            delete_result = await cache_manager_instance.delete(key)
            get_result = await cache_manager_instance.get(key)

            # Assert
            assert delete_result is True
            assert get_result is None

        @pytest.mark.asyncio
        async def test_delete_nonexistent_key(self, cache_manager_instance):
            """Удаление несуществующего ключа"""
            # Act
            result = await cache_manager_instance.delete("nonexistent_key")

            # Assert
            assert result is True  # Удаление несуществующего ключа считается успешным

        @pytest.mark.asyncio
        async def test_clear_pattern_all(self, cache_manager_instance, sample_data):
            """Очистка кэша по паттерну 'all'"""
            # Arrange
            await cache_manager_instance.set("key1", sample_data)
            await cache_manager_instance.set("key2", sample_data)

            # Act
            clear_result = await cache_manager_instance.clear_pattern("*", "all")

            # Assert
            assert clear_result is True
            assert await cache_manager_instance.get("key1") is None
            assert await cache_manager_instance.get("key2") is None

        @pytest.mark.asyncio
        async def test_clear_pattern_memory(self, cache_manager_instance, sample_data):
            """Очистка только локального кэша"""
            # Arrange
            await cache_manager_instance.set("key1", sample_data)

            # Act
            clear_result = await cache_manager_instance.clear_pattern("*", "memory")

            # Assert
            assert clear_result is True
            assert await cache_manager_instance.get("key1") is None

    class TestGetStats:
        """Тесты получения статистики"""

        @pytest.mark.asyncio
        async def test_get_stats_success(self, cache_manager_instance):
            """Успешное получение статистики"""
            # Act
            stats = await cache_manager_instance.get_stats()

            # Assert
            assert isinstance(stats, dict)
            assert "memory_cache" in stats
            assert "redis_cache" in stats
            assert "total_hits" in stats
            assert "total_misses" in stats

        @pytest.mark.asyncio
        async def test_get_stats_with_data(self, cache_manager_instance, sample_data):
            """Получение статистики с данными в кэше"""
            # Arrange
            await cache_manager_instance.set("key1", sample_data)
            await cache_manager_instance.set("key2", sample_data)
            await cache_manager_instance.get("key1")
            await cache_manager_instance.get("nonexistent")

            # Act
            stats = await cache_manager_instance.get_stats()

            # Assert
            assert stats["total_hits"] >= 1
            assert stats["total_misses"] >= 1

    class TestErrorHandling:
        """Тесты обработки ошибок"""

        @pytest.mark.asyncio
        async def test_set_with_invalid_data(self, cache_manager_instance):
            """Установка некорректных данных"""
            # Arrange
            invalid_data = object()  # Несериализуемый объект

            # Act
            result = await cache_manager_instance.set("key", invalid_data)

            # Assert
            assert result is True  # Кэш-менеджер должен обработать ошибку

        @pytest.mark.asyncio
        async def test_get_with_corrupted_data(self, cache_manager_instance):
            """Получение поврежденных данных"""
            # Arrange
            key = "test_key"
            # Симулируем поврежденные данные в кэше
            with patch("cache.cache_manager.memory_cache.get") as mock_get:
                mock_get.return_value = None

                # Act
                result = await cache_manager_instance.get(key)

                # Assert
                assert result is None


class TestCacheDecorators:
    """Тесты декораторов кэширования"""

    @pytest.fixture
    def mock_cache_manager(self):
        """Мок для кэш-менеджера"""
        with patch("cache.cache_manager.cache_manager") as mock_cm:
            yield mock_cm

    class TestCachedDecorator:
        """Тесты декоратора @cached"""

        @pytest.mark.asyncio
        async def test_cached_decorator_success(self, mock_cache_manager):
            """Успешное кэширование с декоратором"""
            # Arrange
            mock_cache_manager.get.return_value = None
            mock_cache_manager.set.return_value = True

            @cached("test_prefix", ttl=3600)
            async def test_function(arg1, arg2, kwarg1="default"):
                return f"result_{arg1}_{arg2}_{kwarg1}"

            # Act
            result = await test_function("val1", "val2", kwarg1="custom")

            # Assert
            assert result == "result_val1_val2_custom"
            mock_cache_manager.get.assert_awaited_once()
            mock_cache_manager.set.assert_awaited_once()

        @pytest.mark.asyncio
        async def test_cached_decorator_cache_hit(self, mock_cache_manager):
            """Попадание в кэш с декоратором"""
            # Arrange
            cached_value = "cached_result"
            mock_cache_manager.get.return_value = cached_value

            @cached("test_prefix", ttl=3600)
            async def test_function(arg1, arg2):
                return f"result_{arg1}_{arg2}"

            # Act
            result = await test_function("val1", "val2")

            # Assert
            assert result == cached_value
            mock_cache_manager.get.assert_awaited_once()
            mock_cache_manager.set.assert_not_awaited()

        @pytest.mark.asyncio
        async def test_cached_decorator_without_ttl(self, mock_cache_manager):
            """Декоратор без TTL"""
            # Arrange
            mock_cache_manager.get.return_value = None
            mock_cache_manager.set.return_value = True

            @cached("test_prefix")
            async def test_function(arg1):
                return f"result_{arg1}"

            # Act
            result = await test_function("val1")

            # Assert
            assert result == "result_val1"
            mock_cache_manager.set.assert_awaited_once()

    class TestInvalidateCacheDecorator:
        """Тесты декоратора @invalidate_cache"""

        @pytest.mark.asyncio
        async def test_invalidate_cache_decorator_success(self, mock_cache_manager):
            """Успешная инвалидация кэша с декоратором"""
            # Arrange
            mock_cache_manager.clear_pattern.return_value = True

            @invalidate_cache("test_prefix")
            async def test_function(arg1, arg2):
                return f"result_{arg1}_{arg2}"

            # Act
            result = await test_function("val1", "val2")

            # Assert
            assert result == "result_val1_val2"
            mock_cache_manager.clear_pattern.assert_awaited_once_with("test_prefix*", "all")

        @pytest.mark.asyncio
        async def test_invalidate_cache_decorator_memory_only(self, mock_cache_manager):
            """Инвалидация только локального кэша"""
            # Arrange
            mock_cache_manager.clear_pattern.return_value = True

            @invalidate_cache("test_prefix", "memory")
            async def test_function(arg1):
                return f"result_{arg1}"

            # Act
            result = await test_function("val1")

            # Assert
            assert result == "result_val1"
            mock_cache_manager.clear_pattern.assert_awaited_once_with("test_prefix*", "memory")


class TestCacheManagerIntegration:
    """Интеграционные тесты для кэш-менеджера"""

    @pytest.mark.asyncio
    async def test_full_cache_workflow(self):
        """Полный рабочий процесс кэширования"""
        # Arrange
        cache_mgr = CacheManager()
        await cache_mgr.initialize()

        test_data = {"id": 1, "name": "Test", "timestamp": datetime.now().isoformat()}
        key = "integration_test_key"

        # Act & Assert
        # 1. Установка значения
        set_result = await cache_mgr.set(key, test_data, ttl=3600)
        assert set_result is True

        # 2. Получение значения
        get_result = await cache_mgr.get(key)
        assert get_result == test_data

        # 3. Обновление значения
        updated_data = {"id": 1, "name": "Updated Test", "timestamp": datetime.now().isoformat()}
        update_result = await cache_mgr.set(key, updated_data, ttl=3600)
        assert update_result is True

        # 4. Проверка обновления
        updated_get_result = await cache_mgr.get(key)
        assert updated_get_result == updated_data

        # 5. Удаление значения
        delete_result = await cache_mgr.delete(key)
        assert delete_result is True

        # 6. Проверка удаления
        final_get_result = await cache_mgr.get(key)
        assert final_get_result is None

        # 7. Очистка ресурсов
        await cache_mgr.cleanup()

    @pytest.mark.asyncio
    async def test_cache_decorators_integration(self):
        """Интеграция декораторов кэширования"""
        # Arrange
        call_count = 0

        @cached("integration_test", ttl=300)
        async def expensive_operation(param):
            nonlocal call_count
            call_count += 1
            return f"expensive_result_{param}_{call_count}"

        @invalidate_cache("integration_test")
        async def update_operation(param):
            return f"updated_result_{param}"

        # Act & Assert
        # 1. Первый вызов - вычисление
        result1 = await expensive_operation("test1")
        assert result1 == "expensive_result_test1_1"
        assert call_count == 1

        # 2. Второй вызов - из кэша
        result2 = await expensive_operation("test1")
        assert result2 == "expensive_result_test1_1"
        assert call_count == 1  # Не увеличился

        # 3. Инвалидация кэша
        update_result = await update_operation("test1")
        assert update_result == "updated_result_test1"

        # 4. Третий вызов после инвалидации - снова вычисление
        result3 = await expensive_operation("test1")
        assert result3 == "expensive_result_test1_2"
        assert call_count == 2


class TestCacheManagerPerformance:
    """Тесты производительности кэш-менеджера"""

    @pytest.mark.asyncio
    async def test_bulk_operations(self):
        """Тест массовых операций"""
        # Arrange
        cache_mgr = CacheManager()
        await cache_mgr.initialize()

        # Act
        start_time = datetime.now()
        
        # Массовая установка
        for i in range(100):
            await cache_mgr.set(f"key_{i}", {"id": i, "data": f"value_{i}"})

        # Массовое получение
        for i in range(100):
            await cache_mgr.get(f"key_{i}")

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Assert
        assert duration < 1.0  # Операции должны выполняться быстро

        # Cleanup
        await cache_mgr.cleanup()

    @pytest.mark.asyncio
    async def test_concurrent_access(self):
        """Тест конкурентного доступа"""
        import asyncio

        # Arrange
        cache_mgr = CacheManager()
        await cache_mgr.initialize()

        async def concurrent_operation(operation_id):
            """Конкурентная операция"""
            for i in range(10):
                key = f"concurrent_key_{operation_id}_{i}"
                await cache_mgr.set(key, {"operation": operation_id, "iteration": i})
                await cache_mgr.get(key)

        # Act
        start_time = datetime.now()
        
        # Запуск 5 конкурентных операций
        tasks = [concurrent_operation(i) for i in range(5)]
        await asyncio.gather(*tasks)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Assert
        assert duration < 2.0  # Конкурентные операции должны выполняться быстро

        # Cleanup
        await cache_mgr.cleanup()
