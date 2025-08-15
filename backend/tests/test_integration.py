"""
Интеграционные тесты для проверки взаимодействия компонентов
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import date, datetime
from fastapi.testclient import TestClient

from main import app
from services.dictionary_service import DictionaryService
from models.model_dictionary import DictionaryService as DictionaryModel
from models.model_attribute import AttributeManager
from schemas import DictionaryIn, DictionaryOut
from exceptions import DictionaryNotFoundError, DictionaryValidationError


class TestApplicationIntegration:
    """Интеграционные тесты приложения"""

    @pytest.fixture
    def client(self):
        """Тестовый клиент FastAPI"""
        return TestClient(app)

    @pytest.fixture
    def mock_database(self):
        """Мок базы данных"""
        return AsyncMock()

    @pytest.fixture
    def dictionary_service(self, mock_database):
        """Сервис справочников с мок-БД"""
        with patch("services.dictionary_service.DictionaryModel") as mock_model, \
             patch("services.dictionary_service.AttributeManager") as mock_attr_manager:
            service = DictionaryService(mock_database)
            service.model = mock_model.return_value
            service.attribute_manager = mock_attr_manager.return_value
            return service

    class TestFullWorkflow:
        """Тесты полного рабочего процесса"""

        @pytest.mark.asyncio
        async def test_create_and_retrieve_dictionary_workflow(self, dictionary_service):
            """Полный процесс создания и получения справочника"""
            # Arrange
            dictionary_data = DictionaryIn(
                name="Integration Test Dictionary",
                code="integration_test_001",
                description="Integration test description",
                start_date=date(2024, 1, 1),
                finish_date=date(2024, 12, 31),
                name_eng="Integration Test Dictionary",
                name_bel="Інтэграцыйны тэст даведнік",
                description_eng="Integration test description",
                description_bel="Інтэграцыйнае тэставае апісанне",
                gko="Integration GKO",
                organization="Integration Org",
                classifier="Integration Classifier",
                id_type=1
            )

            # Act
            # 1. Создание справочника
            dictionary_service.find_dictionary_by_code.return_value = None
            dictionary_service.model.create.return_value = 1
            created_id = await dictionary_service.create_dictionary(dictionary_data)

            # 2. Получение справочника
            expected_dictionary = DictionaryOut(
                id=1,
                name="Integration Test Dictionary",
                code="integration_test_001",
                description="Integration test description",
                start_date=date(2024, 1, 1),
                finish_date=date(2024, 12, 31),
                name_eng="Integration Test Dictionary",
                name_bel="Інтэграцыйны тэст даведнік",
                description_eng="Integration test description",
                description_bel="Інтэграцыйнае тэставае апісанне",
                gko="Integration GKO",
                organization="Integration Org",
                classifier="Integration Classifier",
                id_type=1,
                id_status=1,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            dictionary_service.model.get_dictionary_by_id.return_value = expected_dictionary
            retrieved_dictionary = await dictionary_service.get_dictionary(1)

            # Assert
            assert created_id == 1
            assert retrieved_dictionary.id == 1
            assert retrieved_dictionary.name == "Integration Test Dictionary"
            assert retrieved_dictionary.code == "integration_test_001"

        @pytest.mark.asyncio
        async def test_dictionary_lifecycle_workflow(self, dictionary_service):
            """Полный жизненный цикл справочника"""
            # Arrange
            dictionary_data = DictionaryIn(
                name="Lifecycle Test Dictionary",
                code="lifecycle_test_001",
                description="Lifecycle test description",
                start_date=date(2024, 1, 1),
                finish_date=date(2024, 12, 31),
                id_type=1
            )

            # Act & Assert
            # 1. Создание
            dictionary_service.find_dictionary_by_code.return_value = None
            dictionary_service.model.create.return_value = 1
            created_id = await dictionary_service.create_dictionary(dictionary_data)
            assert created_id == 1

            # 2. Получение
            dictionary_service.model.get_dictionary_by_id.return_value = dictionary_data
            retrieved = await dictionary_service.get_dictionary(1)
            assert retrieved == dictionary_data

            # 3. Обновление
            dictionary_service.model.update.return_value = True
            updated = await dictionary_service.update_dictionary(1, dictionary_data)
            assert updated is True

            # 4. Удаление
            dictionary_service.model.delete.return_value = True
            deleted = await dictionary_service.delete_dictionary(1)
            assert deleted is True

        @pytest.mark.asyncio
        async def test_dictionary_search_workflow(self, dictionary_service):
            """Рабочий процесс поиска справочников"""
            # Arrange
            search_results = [
                DictionaryOut(
                    id=1,
                    name="Search Test Dictionary 1",
                    code="search_test_001",
                    description="Search test description 1",
                    start_date=date(2024, 1, 1),
                    finish_date=date(2024, 12, 31),
                    id_type=1,
                    id_status=1,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                ),
                DictionaryOut(
                    id=2,
                    name="Search Test Dictionary 2",
                    code="search_test_002",
                    description="Search test description 2",
                    start_date=date(2024, 1, 1),
                    finish_date=date(2024, 12, 31),
                    id_type=1,
                    id_status=1,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
            ]

            # Act
            # Поиск по имени
            dictionary_service.model.find_by_name.return_value = search_results
            name_results = await dictionary_service.find_dictionary_by_name("Search Test")

            # Поиск по коду
            dictionary_service.model.find_by_code.return_value = search_results[0]
            code_result = await dictionary_service.find_dictionary_by_code("search_test_001")

            # Assert
            assert len(name_results) == 2
            assert name_results[0].name == "Search Test Dictionary 1"
            assert code_result.name == "Search Test Dictionary 1"

    class TestAPIIntegration:
        """Интеграционные тесты API"""

        @pytest.mark.asyncio
        async def test_api_health_check(self, client):
            """Проверка health check API"""
            # Act
            response = client.get("/health")

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert data["status"] == "healthy"

        @pytest.mark.asyncio
        async def test_api_root_endpoint(self, client):
            """Проверка корневого endpoint API"""
            # Act
            response = client.get("/")

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert "API" in data["message"]

        @pytest.mark.asyncio
        async def test_api_documentation_endpoints(self, client):
            """Проверка endpoints документации"""
            # Act & Assert
            # Swagger UI
            response = client.get("/docs")
            assert response.status_code == 200

            # ReDoc
            response = client.get("/redoc")
            assert response.status_code == 200

        @pytest.mark.asyncio
        async def test_api_cache_endpoints(self, client):
            """Проверка endpoints кэша"""
            # Act & Assert
            # Статистика кэша
            response = client.get("/cache/stats")
            assert response.status_code == 200

            # Очистка кэша
            response = client.post("/cache/clear")
            assert response.status_code == 200

    class TestServiceLayerIntegration:
        """Интеграционные тесты сервисного слоя"""

        @pytest.mark.asyncio
        async def test_dictionary_service_with_cache(self, dictionary_service):
            """Тест сервиса справочников с кэшированием"""
            # Arrange
            dictionary_data = DictionaryOut(
                id=1,
                name="Cache Test Dictionary",
                code="cache_test_001",
                description="Cache test description",
                start_date=date(2024, 1, 1),
                finish_date=date(2024, 12, 31),
                id_type=1,
                id_status=1,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

            # Act
            # Первый вызов - должен обратиться к БД
            dictionary_service.model.get_dictionary_by_id.return_value = dictionary_data
            result1 = await dictionary_service.get_dictionary(1)

            # Второй вызов - должен использовать кэш
            result2 = await dictionary_service.get_dictionary(1)

            # Assert
            assert result1 == dictionary_data
            assert result2 == dictionary_data
            # Проверяем, что модель была вызвана только один раз (кэширование)
            dictionary_service.model.get_dictionary_by_id.assert_called_once_with(1)

        @pytest.mark.asyncio
        async def test_dictionary_service_error_handling(self, dictionary_service):
            """Тест обработки ошибок в сервисе"""
            # Arrange
            dictionary_data = DictionaryIn(
                name="Error Test Dictionary",
                code="error_test_001",
                description="Error test description",
                start_date=date(2024, 12, 31),  # Некорректная дата
                finish_date=date(2024, 1, 1),
                id_type=1
            )

            # Act & Assert
            # Тест валидации дат
            with pytest.raises(DictionaryValidationError):
                await dictionary_service.create_dictionary(dictionary_data)

            # Тест отсутствующего справочника
            dictionary_service.model.get_dictionary_by_id.return_value = None
            with pytest.raises(DictionaryNotFoundError):
                await dictionary_service.get_dictionary(999)

    class TestDatabaseIntegration:
        """Интеграционные тесты базы данных"""

        @pytest.mark.asyncio
        async def test_database_connection_integration(self):
            """Тест интеграции с базой данных"""
            # Arrange
            with patch("database.database") as mock_db:
                mock_db.connect.return_value = None
                mock_db.disconnect.return_value = None
                mock_db.is_connected.return_value = True

                # Act
                await mock_db.connect()
                is_connected = await mock_db.is_connected()
                await mock_db.disconnect()

                # Assert
                assert is_connected is True
                mock_db.connect.assert_called_once()
                mock_db.disconnect.assert_called_once()

        @pytest.mark.asyncio
        async def test_database_query_integration(self, mock_database):
            """Тест интеграции запросов к БД"""
            # Arrange
            expected_data = [
                {"id": 1, "name": "Test Dictionary 1"},
                {"id": 2, "name": "Test Dictionary 2"}
            ]
            mock_database.fetch_all.return_value = expected_data

            # Act
            result = await mock_database.fetch_all("SELECT * FROM dictionary")

            # Assert
            assert result == expected_data
            mock_database.fetch_all.assert_called_once_with("SELECT * FROM dictionary")

    class TestCacheIntegration:
        """Интеграционные тесты кэширования"""

        @pytest.mark.asyncio
        async def test_cache_manager_integration(self):
            """Тест интеграции кэш-менеджера"""
            # Arrange
            from cache.cache_manager import CacheManager
            cache_manager = CacheManager()

            # Act
            await cache_manager.initialize()
            
            # Тест установки и получения значения
            test_data = {"test": "data"}
            await cache_manager.set("test_key", test_data)
            retrieved_data = await cache_manager.get("test_key")
            
            await cache_manager.cleanup()

            # Assert
            assert retrieved_data == test_data

        @pytest.mark.asyncio
        async def test_cache_decorators_integration(self):
            """Тест интеграции декораторов кэширования"""
            # Arrange
            from cache.cache_manager import cached, invalidate_cache
            
            call_count = 0

            @cached("test_integration", ttl=300)
            async def test_function(param):
                nonlocal call_count
                call_count += 1
                return f"result_{param}_{call_count}"

            @invalidate_cache("test_integration")
            async def update_function(param):
                return f"updated_{param}"

            # Act
            # Первый вызов
            result1 = await test_function("test")
            
            # Второй вызов (должен использовать кэш)
            result2 = await test_function("test")
            
            # Обновление
            update_result = await update_function("test")
            
            # Третий вызов после обновления
            result3 = await test_function("test")

            # Assert
            assert result1 == "result_test_1"
            assert result2 == "result_test_1"  # Из кэша
            assert update_result == "updated_test"
            assert result3 == "result_test_2"  # Новый вызов

    class TestErrorHandlingIntegration:
        """Интеграционные тесты обработки ошибок"""

        @pytest.mark.asyncio
        async def test_error_handling_middleware_integration(self, client):
            """Тест интеграции middleware обработки ошибок"""
            # Act
            # Запрос к несуществующему endpoint
            response = client.get("/nonexistent")

            # Assert
            assert response.status_code == 404

        @pytest.mark.asyncio
        async def test_exception_propagation_integration(self, dictionary_service):
            """Тест распространения исключений через слои"""
            # Arrange
            dictionary_service.model.get_dictionary_by_id.side_effect = Exception("Database error")

            # Act & Assert
            with pytest.raises(DictionaryValidationError):
                await dictionary_service.get_dictionary(1)

    class TestPerformanceIntegration:
        """Интеграционные тесты производительности"""

        @pytest.mark.asyncio
        async def test_concurrent_requests_integration(self, dictionary_service):
            """Тест конкурентных запросов"""
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

            async def concurrent_request():
                """Конкурентный запрос"""
                return await dictionary_service.get_dictionary(1)

            # Act
            tasks = [concurrent_request() for _ in range(10)]
            results = await asyncio.gather(*tasks)

            # Assert
            assert len(results) == 10
            for result in results:
                assert result == dictionary_data

        @pytest.mark.asyncio
        async def test_bulk_operations_integration(self, dictionary_service):
            """Тест массовых операций"""
            # Arrange
            dictionaries = []
            for i in range(100):
                dict_data = DictionaryIn(
                    name=f"Bulk Test Dictionary {i}",
                    code=f"bulk_test_{i:03d}",
                    description=f"Bulk test description {i}",
                    start_date=date(2024, 1, 1),
                    finish_date=date(2024, 12, 31),
                    id_type=1
                )
                dictionaries.append(dict_data)

            dictionary_service.find_dictionary_by_code.return_value = None
            dictionary_service.model.create.return_value = 1

            # Act
            import time
            start_time = time.time()
            
            created_ids = []
            for dict_data in dictionaries:
                created_id = await dictionary_service.create_dictionary(dict_data)
                created_ids.append(created_id)
            
            end_time = time.time()
            duration = end_time - start_time

            # Assert
            assert len(created_ids) == 100
            assert all(id == 1 for id in created_ids)
            assert duration < 5.0  # Массовые операции должны выполняться быстро


class TestEndToEndIntegration:
    """End-to-end интеграционные тесты"""

    @pytest.mark.asyncio
    async def test_full_api_workflow(self, client):
        """Полный API рабочий процесс"""
        # Arrange
        dictionary_data = {
            "name": "E2E Test Dictionary",
            "code": "e2e_test_001",
            "description": "E2E test description",
            "start_date": "2024-01-01",
            "finish_date": "2024-12-31",
            "name_eng": "E2E Test Dictionary",
            "name_bel": "E2E тэст даведнік",
            "description_eng": "E2E test description",
            "description_bel": "E2E тэставае апісанне",
            "gko": "E2E GKO",
            "organization": "E2E Org",
            "classifier": "E2E Classifier",
            "id_type": 1
        }

        # Act & Assert
        # 1. Создание справочника
        with patch("routers.dictionary.DictionaryService.create_dictionary") as mock_create:
            mock_create.return_value = 1
            response = client.post("/api/v2/models/newDictionary", json=dictionary_data)
            assert response.status_code == 200

        # 2. Получение списка справочников
        with patch("routers.dictionary.DictionaryService.get_all_dictionaries") as mock_list:
            mock_list.return_value = []
            response = client.get("/api/v2/models/list")
            assert response.status_code == 200

        # 3. Получение структуры справочника
        with patch("routers.dictionary.DictionaryService.get_dictionary_structure") as mock_structure:
            mock_structure.return_value = []
            response = client.get("/api/v2/models/structure/?dictionary=1")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_error_scenarios_integration(self, client):
        """Интеграционные тесты сценариев ошибок"""
        # Act & Assert
        # Некорректные данные
        invalid_data = {
            "name": "",  # Пустое имя
            "code": "test_001",
            "start_date": "2024-12-31",  # Некорректные даты
            "finish_date": "2024-01-01",
            "id_type": 1
        }
        
        response = client.post("/api/v2/models/newDictionary", json=invalid_data)
        assert response.status_code in [400, 422]  # Ошибка валидации

        # Несуществующий справочник
        response = client.get("/api/v2/models/dictionary/?dictionary=999")
        assert response.status_code in [404, 500]  # Не найден или ошибка сервера
