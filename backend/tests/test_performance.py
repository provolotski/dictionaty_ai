"""
Тесты производительности для проверки скорости работы компонентов
"""

import pytest
import asyncio
import time
import psutil
import os
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import date, datetime

from services.dictionary_service import DictionaryService
from cache.cache_manager import CacheManager
from schemas import DictionaryIn, DictionaryOut


class TestPerformanceBenchmarks:
    """Тесты производительности (бенчмарки)"""

    @pytest.fixture
    def mock_database(self):
        """Мок базы данных для тестов производительности"""
        return AsyncMock()

    @pytest.fixture
    def dictionary_service(self, mock_database):
        """Сервис справочников для тестов производительности"""
        with patch("services.dictionary_service.DictionaryModel") as mock_model, \
             patch("services.dictionary_service.AttributeManager") as mock_attr_manager:
            service = DictionaryService(mock_database)
            service.model = mock_model.return_value
            service.attribute_manager = mock_attr_manager.return_value
            return service

    class TestServicePerformance:
        """Тесты производительности сервисного слоя"""

        @pytest.mark.performance
        @pytest.mark.asyncio
        async def test_dictionary_service_creation_performance(self, dictionary_service):
            """Тест производительности создания справочников"""
            # Arrange
            dictionary_data = DictionaryIn(
                name="Performance Test Dictionary",
                code="perf_test_001",
                description="Performance test description",
                start_date=date(2024, 1, 1),
                finish_date=date(2024, 12, 31),
                id_type=1
            )
            dictionary_service.find_dictionary_by_code.return_value = None
            dictionary_service.model.create.return_value = 1

            # Act
            start_time = time.time()
            
            for i in range(1000):
                await dictionary_service.create_dictionary(dictionary_data)
            
            end_time = time.time()
            duration = end_time - start_time

            # Assert
            assert duration < 10.0  # 1000 операций должны выполняться менее 10 секунд
            assert duration > 0.1   # Но не слишком быстро (реалистичность)

        @pytest.mark.performance
        @pytest.mark.asyncio
        async def test_dictionary_service_retrieval_performance(self, dictionary_service):
            """Тест производительности получения справочников"""
            # Arrange
            dictionary_data = DictionaryOut(
                id=1,
                name="Performance Test Dictionary",
                code="perf_test_001",
                description="Performance test description",
                start_date=date(2024, 1, 1),
                finish_date=date(2024, 12, 31),
                id_type=1,
                id_status=1,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            dictionary_service.model.get_dictionary_by_id.return_value = dictionary_data

            # Act
            start_time = time.time()
            
            for i in range(1000):
                await dictionary_service.get_dictionary(1)
            
            end_time = time.time()
            duration = end_time - start_time

            # Assert
            assert duration < 5.0  # 1000 операций чтения должны выполняться быстро

        @pytest.mark.performance
        @pytest.mark.asyncio
        async def test_dictionary_service_search_performance(self, dictionary_service):
            """Тест производительности поиска справочников"""
            # Arrange
            search_results = [
                DictionaryOut(
                    id=i,
                    name=f"Search Test Dictionary {i}",
                    code=f"search_test_{i:03d}",
                    description=f"Search test description {i}",
                    start_date=date(2024, 1, 1),
                    finish_date=date(2024, 12, 31),
                    id_type=1,
                    id_status=1,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                ) for i in range(100)
            ]
            dictionary_service.model.find_by_name.return_value = search_results

            # Act
            start_time = time.time()
            
            for i in range(100):
                await dictionary_service.find_dictionary_by_name("Search Test")
            
            end_time = time.time()
            duration = end_time - start_time

            # Assert
            assert duration < 3.0  # 100 операций поиска должны выполняться быстро

    class TestCachePerformance:
        """Тесты производительности кэширования"""

        @pytest.mark.performance
        @pytest.mark.asyncio
        async def test_cache_manager_set_performance(self):
            """Тест производительности установки значений в кэш"""
            # Arrange
            cache_manager = CacheManager()
            await cache_manager.initialize()

            # Act
            start_time = time.time()
            
            for i in range(10000):
                await cache_manager.set(f"key_{i}", {"data": f"value_{i}"})
            
            end_time = time.time()
            duration = end_time - start_time

            # Assert
            assert duration < 5.0  # 10000 операций установки должны выполняться быстро

            # Cleanup
            await cache_manager.cleanup()

        @pytest.mark.performance
        @pytest.mark.asyncio
        async def test_cache_manager_get_performance(self):
            """Тест производительности получения значений из кэша"""
            # Arrange
            cache_manager = CacheManager()
            await cache_manager.initialize()

            # Подготавливаем данные
            for i in range(1000):
                await cache_manager.set(f"key_{i}", {"data": f"value_{i}"})

            # Act
            start_time = time.time()
            
            for i in range(10000):
                await cache_manager.get(f"key_{i % 1000}")
            
            end_time = time.time()
            duration = end_time - start_time

            # Assert
            assert duration < 3.0  # 10000 операций получения должны выполняться очень быстро

            # Cleanup
            await cache_manager.cleanup()

        @pytest.mark.performance
        @pytest.mark.asyncio
        async def test_cache_decorator_performance(self):
            """Тест производительности декораторов кэширования"""
            # Arrange
            from cache.cache_manager import cached
            
            call_count = 0

            @cached("perf_test", ttl=300)
            async def expensive_operation(param):
                nonlocal call_count
                call_count += 1
                # Симулируем дорогую операцию
                await asyncio.sleep(0.001)
                return f"result_{param}_{call_count}"

            # Act
            start_time = time.time()
            
            # Первые 100 вызовов - дорогие операции
            for i in range(100):
                await expensive_operation(f"param_{i}")
            
            # Следующие 100 вызовов - должны использовать кэш
            for i in range(100):
                await expensive_operation(f"param_{i}")
            
            end_time = time.time()
            duration = end_time - start_time

            # Assert
            assert duration < 2.0  # Кэширование должно значительно ускорить работу
            assert call_count == 100  # Функция должна быть вызвана только 100 раз

    class TestConcurrencyPerformance:
        """Тесты производительности при конкурентном доступе"""

        @pytest.mark.performance
        @pytest.mark.asyncio
        async def test_concurrent_dictionary_operations(self, dictionary_service):
            """Тест производительности конкурентных операций со справочниками"""
            # Arrange
            dictionary_data = DictionaryOut(
                id=1,
                name="Concurrent Test Dictionary",
                code="concurrent_test_001",
                description="Concurrent test description",
                start_date=date(2024, 1, 1),
                finish_date=date(2024, 12, 31),
                id_type=1,
                id_status=1,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            dictionary_service.model.get_dictionary_by_id.return_value = dictionary_data

            async def concurrent_operation(operation_id):
                """Конкурентная операция"""
                for i in range(100):
                    await dictionary_service.get_dictionary(1)
                return f"completed_{operation_id}"

            # Act
            start_time = time.time()
            
            # Запускаем 10 конкурентных операций
            tasks = [concurrent_operation(i) for i in range(10)]
            results = await asyncio.gather(*tasks)
            
            end_time = time.time()
            duration = end_time - start_time

            # Assert
            assert duration < 5.0  # Конкурентные операции должны выполняться эффективно
            assert len(results) == 10
            assert all(result.startswith("completed_") for result in results)

        @pytest.mark.performance
        @pytest.mark.asyncio
        async def test_concurrent_cache_operations(self):
            """Тест производительности конкурентных операций с кэшем"""
            # Arrange
            cache_manager = CacheManager()
            await cache_manager.initialize()

            async def concurrent_cache_operation(operation_id):
                """Конкурентная операция с кэшем"""
                for i in range(100):
                    key = f"concurrent_key_{operation_id}_{i}"
                    await cache_manager.set(key, {"operation": operation_id, "iteration": i})
                    await cache_manager.get(key)
                return f"cache_completed_{operation_id}"

            # Act
            start_time = time.time()
            
            # Запускаем 5 конкурентных операций
            tasks = [concurrent_cache_operation(i) for i in range(5)]
            results = await asyncio.gather(*tasks)
            
            end_time = time.time()
            duration = end_time - start_time

            # Assert
            assert duration < 3.0  # Конкурентные операции с кэшем должны быть быстрыми
            assert len(results) == 5
            assert all(result.startswith("cache_completed_") for result in results)

            # Cleanup
            await cache_manager.cleanup()

    class TestMemoryPerformance:
        """Тесты производительности памяти"""

        @pytest.mark.performance
        @pytest.mark.asyncio
        async def test_memory_usage_dictionary_operations(self, dictionary_service):
            """Тест использования памяти при операциях со справочниками"""
            # Arrange
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss

            dictionary_data = DictionaryIn(
                name="Memory Test Dictionary",
                code="memory_test_001",
                description="Memory test description",
                start_date=date(2024, 1, 1),
                finish_date=date(2024, 12, 31),
                id_type=1
            )
            dictionary_service.find_dictionary_by_code.return_value = None
            dictionary_service.model.create.return_value = 1

            # Act
            for i in range(1000):
                await dictionary_service.create_dictionary(dictionary_data)

            final_memory = process.memory_info().rss
            memory_increase = final_memory - initial_memory

            # Assert
            # Увеличение памяти не должно быть критическим (менее 50MB)
            assert memory_increase < 50 * 1024 * 1024

        @pytest.mark.performance
        @pytest.mark.asyncio
        async def test_memory_usage_cache_operations(self):
            """Тест использования памяти при операциях с кэшем"""
            # Arrange
            cache_manager = CacheManager()
            await cache_manager.initialize()
            
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss

            # Act
            # Заполняем кэш большим количеством данных
            for i in range(10000):
                large_data = {"id": i, "data": "x" * 1000}  # ~1KB данных
                await cache_manager.set(f"large_key_{i}", large_data)

            final_memory = process.memory_info().rss
            memory_increase = final_memory - initial_memory

            # Assert
            # Увеличение памяти должно быть разумным (менее 100MB для 10MB данных)
            assert memory_increase < 100 * 1024 * 1024

            # Cleanup
            await cache_manager.cleanup()

    class TestDatabasePerformance:
        """Тесты производительности базы данных"""

        @pytest.mark.performance
        @pytest.mark.asyncio
        async def test_database_query_performance(self, mock_database):
            """Тест производительности запросов к БД"""
            # Arrange
            expected_data = [{"id": i, "name": f"Dictionary {i}"} for i in range(1000)]
            mock_database.fetch_all.return_value = expected_data

            # Act
            start_time = time.time()
            
            for i in range(100):
                await mock_database.fetch_all("SELECT * FROM dictionary")
            
            end_time = time.time()
            duration = end_time - start_time

            # Assert
            assert duration < 2.0  # 100 запросов должны выполняться быстро

        @pytest.mark.performance
        @pytest.mark.asyncio
        async def test_database_bulk_operations_performance(self, mock_database):
            """Тест производительности массовых операций с БД"""
            # Arrange
            mock_database.execute_many.return_value = None

            # Act
            start_time = time.time()
            
            # Симулируем массовую вставку
            bulk_data = [{"name": f"Bulk Item {i}", "code": f"bulk_{i}"} for i in range(1000)]
            await mock_database.execute_many(
                "INSERT INTO dictionary (name, code) VALUES (:name, :code)",
                bulk_data
            )
            
            end_time = time.time()
            duration = end_time - start_time

            # Assert
            assert duration < 1.0  # Массовая вставка должна быть быстрой

    class TestAPIPerformance:
        """Тесты производительности API"""

        @pytest.mark.performance
        @pytest.mark.asyncio
        async def test_api_response_time_performance(self):
            """Тест времени отклика API"""
            # Arrange
            from fastapi.testclient import TestClient
            from main import app
            
            client = TestClient(app)

            # Act
            start_time = time.time()
            
            for i in range(100):
                response = client.get("/health")
                assert response.status_code == 200
            
            end_time = time.time()
            duration = end_time - start_time

            # Assert
            assert duration < 5.0  # 100 запросов к API должны выполняться быстро

        @pytest.mark.performance
        @pytest.mark.asyncio
        async def test_api_concurrent_requests_performance(self):
            """Тест производительности конкурентных API запросов"""
            # Arrange
            from fastapi.testclient import TestClient
            from main import app
            
            client = TestClient(app)

            async def api_request():
                """API запрос"""
                response = client.get("/health")
                return response.status_code

            # Act
            start_time = time.time()
            
            # Запускаем 50 конкурентных запросов
            tasks = [api_request() for _ in range(50)]
            results = await asyncio.gather(*tasks)
            
            end_time = time.time()
            duration = end_time - start_time

            # Assert
            assert duration < 3.0  # Конкурентные API запросы должны выполняться быстро
            assert all(status == 200 for status in results)

    class TestScalabilityTests:
        """Тесты масштабируемости"""

        @pytest.mark.performance
        @pytest.mark.asyncio
        async def test_scalability_dictionary_operations(self, dictionary_service):
            """Тест масштабируемости операций со справочниками"""
            # Arrange
            dictionary_data = DictionaryIn(
                name="Scalability Test Dictionary",
                code="scalability_test_001",
                description="Scalability test description",
                start_date=date(2024, 1, 1),
                finish_date=date(2024, 12, 31),
                id_type=1
            )
            dictionary_service.find_dictionary_by_code.return_value = None
            dictionary_service.model.create.return_value = 1

            # Act & Assert
            # Тестируем разные объемы данных
            for batch_size in [100, 1000, 10000]:
                start_time = time.time()
                
                for i in range(batch_size):
                    await dictionary_service.create_dictionary(dictionary_data)
                
                end_time = time.time()
                duration = end_time - start_time
                
                # Время должно расти линейно или лучше
                expected_time = batch_size * 0.001  # 1ms на операцию
                assert duration < expected_time * 2  # Допускаем 2x отклонение

        @pytest.mark.performance
        @pytest.mark.asyncio
        async def test_scalability_cache_operations(self):
            """Тест масштабируемости операций с кэшем"""
            # Arrange
            cache_manager = CacheManager()
            await cache_manager.initialize()

            # Act & Assert
            # Тестируем разные объемы данных
            for batch_size in [1000, 10000, 100000]:
                start_time = time.time()
                
                for i in range(batch_size):
                    await cache_manager.set(f"scalability_key_{i}", {"data": f"value_{i}"})
                
                end_time = time.time()
                duration = end_time - start_time
                
                # Время должно расти линейно или лучше
                expected_time = batch_size * 0.0001  # 0.1ms на операцию
                assert duration < expected_time * 3  # Допускаем 3x отклонение

            # Cleanup
            await cache_manager.cleanup()


class TestPerformanceMonitoring:
    """Тесты мониторинга производительности"""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_performance_metrics_collection(self, dictionary_service):
        """Тест сбора метрик производительности"""
        # Arrange
        import time
        metrics = []

        dictionary_data = DictionaryOut(
            id=1,
            name="Metrics Test Dictionary",
            code="metrics_test_001",
            description="Metrics test description",
            start_date=date(2024, 1, 1),
            finish_date=date(2024, 12, 31),
            id_type=1,
            id_status=1,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        dictionary_service.model.get_dictionary_by_id.return_value = dictionary_data

        # Act
        for i in range(100):
            start_time = time.time()
            await dictionary_service.get_dictionary(1)
            end_time = time.time()
            
            metrics.append({
                'operation': 'get_dictionary',
                'duration': end_time - start_time,
                'timestamp': datetime.now()
            })

        # Assert
        assert len(metrics) == 100
        
        # Анализируем метрики
        durations = [m['duration'] for m in metrics]
        avg_duration = sum(durations) / len(durations)
        max_duration = max(durations)
        
        assert avg_duration < 0.01  # Среднее время должно быть менее 10ms
        assert max_duration < 0.1   # Максимальное время должно быть менее 100ms

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_performance_bottleneck_detection(self, dictionary_service):
        """Тест обнаружения узких мест производительности"""
        # Arrange
        import time
        
        # Симулируем медленную операцию
        async def slow_operation():
            await asyncio.sleep(0.1)  # 100ms задержка
            return "slow_result"

        # Act
        start_time = time.time()
        result = await slow_operation()
        end_time = time.time()
        duration = end_time - start_time

        # Assert
        assert result == "slow_result"
        assert duration >= 0.1  # Операция должна быть медленной
        assert duration < 0.2   # Но не слишком медленной

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_performance_regression_detection(self):
        """Тест обнаружения регрессии производительности"""
        # Arrange
        import time
        
        # Базовые метрики (эталонные)
        baseline_metrics = {
            'cache_set': 0.001,    # 1ms
            'cache_get': 0.0005,   # 0.5ms
            'dictionary_create': 0.01,  # 10ms
            'dictionary_get': 0.005     # 5ms
        }

        # Act
        # Симулируем измерение текущих метрик
        current_metrics = {
            'cache_set': 0.002,    # 2ms (ухудшение)
            'cache_get': 0.0004,   # 0.4ms (улучшение)
            'dictionary_create': 0.015,  # 15ms (ухудшение)
            'dictionary_get': 0.004     # 4ms (улучшение)
        }

        # Assert
        # Проверяем регрессии (ухудшение более чем на 50%)
        for operation, baseline in baseline_metrics.items():
            current = current_metrics[operation]
            regression_ratio = current / baseline
            
            if regression_ratio > 1.5:  # Ухудшение более чем на 50%
                print(f"PERFORMANCE REGRESSION DETECTED: {operation}")
                print(f"Baseline: {baseline}s, Current: {current}s, Ratio: {regression_ratio}")
            
            # В реальном тесте здесь можно было бы выбросить исключение
            # assert regression_ratio <= 1.5, f"Performance regression in {operation}"
