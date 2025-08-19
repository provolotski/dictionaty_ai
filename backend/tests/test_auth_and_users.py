"""
Тесты для авторизации, пользователей и справочников
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import date, datetime
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI

from main import app
from routers.dictionary import dict_router
from routers.users import user_router
from services.dictionary_service import DictionaryService
from models.model_dictionary import DictionaryService as DictionaryModel
from schemas import DictionaryIn, DictionaryOut, UserInfo, LoginRequest, TokenResponse
from exceptions import DictionaryNotFoundError, DictionaryValidationError


@pytest.mark.backend
@pytest.mark.auth
class TestAuthentication:
    """Тесты авторизации"""

    @pytest.fixture
    def client(self):
        """Тестовый клиент FastAPI"""
        return TestClient(app)

    @pytest.fixture
    def async_client(self):
        """Асинхронный тестовый клиент"""
        transport = ASGITransport(app=app)
        return AsyncClient(transport=transport, base_url="http://test")

    @pytest.mark.asyncio
    async def test_login_success(self, async_client):
        """Тест успешного входа в систему"""
        # Arrange
        login_data = {
            "username": "testuser",
            "password": "testpass123"
        }
        
        # Act
        with patch("routers.users.external_auth_api") as mock_auth:
            mock_auth.return_value = {
                "access_token": "test_access_token",
                "refresh_token": "test_refresh_token",
                "user": {
                    "username": "testuser",
                    "display_name": "Test User",
                    "email": "test@example.com",
                    "groups": ["EISGS_Users", "EISGS_AppSecurity"],
                    "department": "IT",
                    "title": "Developer",
                    "employee_id": "EMP001"
                }
            }
            
            response = await async_client.post("/api/v1/auth/login", json=login_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "user" in data
        assert data["user"]["username"] == "testuser"

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, async_client):
        """Тест входа с неверными учетными данными"""
        # Arrange
        login_data = {
            "username": "invaliduser",
            "password": "wrongpass"
        }
        
        # Act
        with patch("routers.users.external_auth_api") as mock_auth:
            mock_auth.side_effect = Exception("Invalid credentials")
            
            response = await async_client.post("/api/v1/auth/login", json=login_data)
        
        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "error" in data

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, async_client):
        """Тест успешного обновления токена"""
        # Arrange
        refresh_data = {
            "refresh_token": "valid_refresh_token"
        }
        
        # Act
        with patch("routers.users.external_auth_api") as mock_auth:
            mock_auth.return_value = {
                "access_token": "new_access_token",
                "refresh_token": "new_refresh_token"
            }
            
            response = await async_client.post("/api/v1/auth/refresh", json=refresh_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    @pytest.mark.asyncio
    async def test_check_token_valid(self, async_client):
        """Тест проверки валидного токена"""
        # Arrange
        headers = {"Authorization": "Bearer valid_token"}
        
        # Act
        with patch("routers.users.external_auth_api") as mock_auth:
            mock_auth.return_value = {
                "valid": True,
                "user": {
                    "username": "testuser",
                    "groups": ["EISGS_Users"]
                }
            }
            
            response = await async_client.get("/api/v1/auth/check_token", headers=headers)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True


@pytest.mark.backend
@pytest.mark.users
class TestUserManagement:
    """Тесты управления пользователями"""

    @pytest.fixture
    def async_client(self):
        """Асинхронный тестовый клиент"""
        transport = ASGITransport(app=app)
        return AsyncClient(transport=transport, base_url="http://test")

    @pytest.mark.asyncio
    async def test_get_user_data_success(self, async_client):
        """Тест успешного получения данных пользователя"""
        # Arrange
        headers = {"Authorization": "Bearer valid_token"}
        
        # Act
        with patch("routers.users.external_auth_api") as mock_auth:
            mock_auth.return_value = {
                "username": "testuser",
                "display_name": "Test User",
                "email": "test@example.com",
                "groups": ["EISGS_Users", "EISGS_AppSecurity"],
                "department": "IT",
                "title": "Developer",
                "employee_id": "EMP001"
            }
            
            response = await async_client.get("/api/v1/auth/get_data", headers=headers)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert "EISGS_Users" in data["groups"]
        assert "EISGS_AppSecurity" in data["groups"]

    @pytest.mark.asyncio
    async def test_get_user_groups_success(self, async_client):
        """Тест успешного получения групп пользователя"""
        # Arrange
        headers = {"Authorization": "Bearer valid_token"}
        
        # Act
        with patch("routers.users.external_auth_api") as mock_auth:
            mock_auth.return_value = ["EISGS_Users", "EISGS_AppSecurity"]
            
            response = await async_client.get("/api/v1/auth/domain/user/groups", headers=headers)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert "EISGS_Users" in data
        assert "EISGS_AppSecurity" in data

    @pytest.mark.asyncio
    async def test_get_all_users_success(self, async_client):
        """Тест успешного получения списка всех пользователей"""
        # Arrange
        headers = {"Authorization": "Bearer valid_token"}
        
        # Act
        with patch("routers.users.external_auth_api") as mock_auth:
            mock_auth.return_value = [
                {
                    "username": "user1",
                    "display_name": "User One",
                    "email": "user1@example.com",
                    "groups": ["EISGS_Users"],
                    "department": "IT",
                    "title": "Developer",
                    "employee_id": "EMP001"
                },
                {
                    "username": "user2",
                    "display_name": "User Two",
                    "email": "user2@example.com",
                    "groups": ["EISGS_Users", "EISGS_AppSecurity"],
                    "department": "HR",
                    "title": "Manager",
                    "employee_id": "EMP002"
                }
            ]
            
            response = await async_client.get("/api/v1/users", headers=headers)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["username"] == "user1"
        assert data[1]["username"] == "user2"

    @pytest.mark.asyncio
    async def test_get_user_by_username_success(self, async_client):
        """Тест успешного получения пользователя по имени"""
        # Arrange
        headers = {"Authorization": "Bearer valid_token"}
        username = "testuser"
        
        # Act
        with patch("routers.users.external_auth_api") as mock_auth:
            mock_auth.return_value = {
                "username": "testuser",
                "display_name": "Test User",
                "email": "test@example.com",
                "groups": ["EISGS_Users"],
                "department": "IT",
                "title": "Developer",
                "employee_id": "EMP001"
            }
            
            response = await async_client.get(f"/api/v1/users/{username}", headers=headers)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == username


@pytest.mark.backend
@pytest.mark.dictionaries
class TestDictionaryManagement:
    """Тесты управления справочниками"""

    @pytest.fixture
    def async_client(self):
        """Асинхронный тестовый клиент"""
        transport = ASGITransport(app=app)
        return AsyncClient(transport=transport, base_url="http://test")

    @pytest.fixture
    def sample_dictionary_data(self):
        """Тестовые данные для справочника"""
        return {
            "name": "Тестовый справочник",
            "code": "TEST_DICT_001",
            "description": "Описание тестового справочника",
            "start_date": "2025-08-18",
            "finish_date": "9999-12-31",
            "name_eng": "Test Dictionary",
            "name_bel": "Тэставы даведнік",
            "description_eng": "Test dictionary description",
            "description_bel": "Апісанне тэставага даведніка",
            "gko": "Test GKO",
            "organization": "Test Organization",
            "classifier": "Test Classifier",
            "id_type": 0
        }

    @pytest.mark.asyncio
    async def test_get_dictionaries_list_success(self, async_client):
        """Тест успешного получения списка справочников"""
        # Arrange
        headers = {"Authorization": "Bearer valid_token"}
        
        # Act
        with patch("routers.dictionary.DictionaryService.get_all_dictionaries") as mock_service:
            mock_service.return_value = [
                DictionaryOut(
                    id=1,
                    name="Справочник 1",
                    code="DICT_001",
                    description="Описание 1",
                    start_date=date(2025, 1, 1),
                    finish_date=date(2025, 12, 31),
                    name_eng="Dictionary 1",
                    name_bel="Даведнік 1",
                    description_eng="Description 1",
                    description_bel="Апісанне 1",
                    gko="GKO1",
                    organization="Org1",
                    classifier="Class1",
                    id_type=0,
                    id_status=1,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                ),
                DictionaryOut(
                    id=2,
                    name="Справочник 2",
                    code="DICT_002",
                    description="Описание 2",
                    start_date=date(2025, 1, 1),
                    finish_date=date(2025, 12, 31),
                    name_eng="Dictionary 2",
                    name_bel="Даведнік 2",
                    description_eng="Description 2",
                    description_bel="Апісанне 2",
                    gko="GKO2",
                    organization="Org2",
                    classifier="Class2",
                    id_type=1,
                    id_status=1,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
            ]
            
            response = await async_client.get("/api/v2/models/list", headers=headers)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["name"] == "Справочник 1"
        assert data[1]["name"] == "Справочник 2"

    @pytest.mark.asyncio
    async def test_create_dictionary_success(self, async_client, sample_dictionary_data):
        """Тест успешного создания справочника"""
        # Arrange
        headers = {"Authorization": "Bearer valid_token"}
        
        # Act
        with patch("routers.dictionary.DictionaryService.create_dictionary") as mock_service:
            mock_service.return_value = 123  # ID созданного справочника
            
            response = await async_client.post(
                "/api/v2/models/newDictionary", 
                json=sample_dictionary_data,
                headers=headers
            )
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert "message" in data
        assert "id" in data
        assert data["id"] == 123
        mock_service.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_dictionary_validation_error(self, async_client):
        """Тест ошибки валидации при создании справочника"""
        # Arrange
        headers = {"Authorization": "Bearer valid_token"}
        invalid_data = {
            "name": "",  # Пустое имя - недопустимо
            "code": "TEST"
        }
        
        # Act
        with patch("routers.dictionary.DictionaryService.create_dictionary") as mock_service:
            mock_service.side_effect = DictionaryValidationError("Имя справочника не может быть пустым")
            
            response = await async_client.post(
                "/api/v2/models/newDictionary", 
                json=invalid_data,
                headers=headers
            )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "error" in data

    @pytest.mark.asyncio
    async def test_create_dictionary_duplicate_code(self, async_client, sample_dictionary_data):
        """Тест ошибки дублирования кода при создании справочника"""
        # Arrange
        headers = {"Authorization": "Bearer valid_token"}
        
        # Act
        with patch("routers.dictionary.DictionaryService.create_dictionary") as mock_service:
            mock_service.side_effect = DictionaryValidationError("Код справочника уже существует")
            
            response = await async_client.post(
                "/api/v2/models/newDictionary", 
                json=sample_dictionary_data,
                headers=headers
            )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "error" in data

    @pytest.mark.asyncio
    async def test_get_dictionary_by_id_success(self, async_client):
        """Тест успешного получения справочника по ID"""
        # Arrange
        headers = {"Authorization": "Bearer valid_token"}
        dictionary_id = 1
        
        # Act
        with patch("routers.dictionary.DictionaryService.get_dictionary") as mock_service:
            mock_service.return_value = DictionaryOut(
                id=1,
                name="Тестовый справочник",
                code="TEST_DICT",
                description="Описание",
                start_date=date(2025, 1, 1),
                finish_date=date(2025, 12, 31),
                name_eng="Test Dictionary",
                name_bel="Тэставы даведнік",
                description_eng="Test description",
                description_bel="Тэставае апісанне",
                gko="Test GKO",
                organization="Test Org",
                classifier="Test Classifier",
                id_type=0,
                id_status=1,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            response = await async_client.get(
                f"/api/v2/models/{dictionary_id}", 
                headers=headers
            )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == dictionary_id
        assert data["name"] == "Тестовый справочник"

    @pytest.mark.asyncio
    async def test_get_dictionary_not_found(self, async_client):
        """Тест получения несуществующего справочника"""
        # Arrange
        headers = {"Authorization": "Bearer valid_token"}
        dictionary_id = 999
        
        # Act
        with patch("routers.dictionary.DictionaryService.get_dictionary") as mock_service:
            mock_service.side_effect = DictionaryNotFoundError(dictionary_id)
            
            response = await async_client.get(
                f"/api/v2/models/{dictionary_id}", 
                headers=headers
            )
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "error" in data


@pytest.mark.backend
@pytest.mark.integration
class TestIntegrationWorkflow:
    """Интеграционные тесты рабочего процесса"""

    @pytest.fixture
    def async_client(self):
        """Асинхронный тестовый клиент"""
        transport = ASGITransport(app=app)
        return AsyncClient(transport=transport, base_url="http://test")

    @pytest.mark.asyncio
    async def test_full_user_workflow(self, async_client):
        """Полный тест рабочего процесса пользователя"""
        # 1. Вход в систему
        login_data = {
            "username": "testuser",
            "password": "testpass123"
        }
        
        with patch("routers.users.external_auth_api") as mock_auth:
            mock_auth.return_value = {
                "access_token": "test_access_token",
                "refresh_token": "test_refresh_token",
                "user": {
                    "username": "testuser",
                    "groups": ["EISGS_Users"]
                }
            }
            
            login_response = await async_client.post("/api/v1/auth/login", json=login_data)
            assert login_response.status_code == 200
            
            access_token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {access_token}"}
        
        # 2. Получение списка справочников
        with patch("routers.dictionary.DictionaryService.get_all_dictionaries") as mock_service:
            mock_service.return_value = []
            
            dict_response = await async_client.get("/api/v2/models/list", headers=headers)
            assert dict_response.status_code == 200
        
        # 3. Создание нового справочника
        dictionary_data = {
            "name": "Интеграционный тест",
            "code": "INTEGRATION_TEST",
            "description": "Тест интеграции",
            "start_date": "2025-08-18",
            "finish_date": "9999-12-31",
            "id_type": 0
        }
        
        with patch("routers.dictionary.DictionaryService.create_dictionary") as mock_service:
            mock_service.return_value = 456
            
            create_response = await async_client.post(
                "/api/v2/models/newDictionary",
                json=dictionary_data,
                headers=headers
            )
            assert create_response.status_code == 201

    @pytest.mark.asyncio
    async def test_user_permissions_workflow(self, async_client):
        """Тест рабочего процесса с проверкой прав пользователя"""
        # 1. Вход пользователя с правами администратора
        login_data = {
            "username": "admin",
            "password": "adminpass123"
        }
        
        with patch("routers.users.external_auth_api") as mock_auth:
            mock_auth.return_value = {
                "access_token": "admin_token",
                "refresh_token": "admin_refresh",
                "user": {
                    "username": "admin",
                    "groups": ["EISGS_Users", "EISGS_AppSecurity"]
                }
            }
            
            login_response = await async_client.post("/api/v1/auth/login", json=login_data)
            assert login_response.status_code == 200
            
            access_token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {access_token}"}
        
        # 2. Проверка прав доступа
        with patch("routers.users.external_auth_api") as mock_auth:
            mock_auth.return_value = {
                "username": "admin",
                "groups": ["EISGS_Users", "EISGS_AppSecurity"]
            }
            
            user_response = await async_client.get("/api/v1/auth/get_data", headers=headers)
            assert user_response.status_code == 200
            
            user_data = user_response.json()
            assert "EISGS_AppSecurity" in user_data["groups"]
            assert "EISGS_Users" in user_data["groups"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
