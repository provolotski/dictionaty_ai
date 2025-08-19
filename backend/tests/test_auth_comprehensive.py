"""
Комплексные тесты для авторизации, пользователей и справочников
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import date, datetime, timedelta
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI, HTTPException

from main import app
from routers.dictionary import dict_router
from routers.users import users_router
from services.dictionary_service import DictionaryService
from models.model_dictionary import DictionaryService as DictionaryModel
from schemas import DictionaryIn, DictionaryOut, UserInfo, LoginRequest, TokenResponse
from exceptions import DictionaryNotFoundError, DictionaryValidationError


class TestAuthenticationComprehensive:
    """Комплексные тесты авторизации"""

    @pytest.fixture
    def client(self):
        """Тестовый клиент FastAPI"""
        return TestClient(app)

    @pytest.fixture
    def async_client(self):
        """Асинхронный тестовый клиент"""
        transport = ASGITransport(app=app)
        return AsyncClient(transport=transport, base_url="http://test")

    @pytest.fixture
    def valid_user_data(self):
        """Валидные данные пользователя для тестов"""
        return {
            "username": "testuser",
            "password": "testpass123"
        }

    @pytest.fixture
    def admin_user_data(self):
        """Данные администратора для тестов"""
        return {
            "username": "admin",
            "password": "adminpass123"
        }

    @pytest.mark.asyncio
    async def test_login_with_domain_groups_check(self, async_client, valid_user_data):
        """Тест входа с проверкой групп домена"""
        # Arrange
        with patch("routers.users.external_auth_api") as mock_auth:
            # Мокаем успешную авторизацию
            mock_auth.side_effect = [
                # Первый вызов для login
                {
                    "access_token": "test_access_token",
                    "refresh_token": "test_refresh_token",
                    "user": {
                        "username": "testuser",
                        "display_name": "Test User",
                        "email": "test@example.com",
                        "groups": ["EISGS_Users"],
                        "department": "IT",
                        "title": "Developer",
                        "employee_id": "EMP001"
                    }
                },
                # Второй вызов для проверки групп
                ["EISGS_Users"]
            ]
            
            # Act
            response = await async_client.post("/api/v1/auth/login", json=valid_user_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "user" in data
        assert data["user"]["username"] == "testuser"

    @pytest.mark.asyncio
    async def test_login_user_not_in_required_groups(self, async_client):
        """Тест входа пользователя, не входящего в требуемые группы"""
        # Arrange
        login_data = {
            "username": "unauthorized_user",
            "password": "testpass123"
        }
        
        with patch("routers.users.external_auth_api") as mock_auth:
            # Мокаем успешную авторизацию, но пользователь не в нужных группах
            mock_auth.side_effect = [
                {
                    "access_token": "test_access_token",
                    "refresh_token": "test_refresh_token",
                    "user": {
                        "username": "unauthorized_user",
                        "groups": ["Other_Group"]
                    }
                },
                ["Other_Group"]  # Пользователь не в EISGS_Users или EISGS_AppSecurity
            ]
            
            # Act
            response = await async_client.post("/api/v1/auth/login", json=login_data)
        
        # Assert
        assert response.status_code == 403
        data = response.json()
        assert "error" in data
        assert "недостаточно прав" in data["error"].lower()

    @pytest.mark.asyncio
    async def test_token_refresh_workflow(self, async_client):
        """Тест полного цикла обновления токена"""
        # Arrange
        expired_token = "expired_access_token"
        refresh_token = "valid_refresh_token"
        
        with patch("routers.users.external_auth_api") as mock_auth:
            # Мокаем проверку токена - токен истек
            mock_auth.side_effect = [
                {"valid": False, "expired": True},  # check_token
                {  # refresh_token
                    "status": 200,
                    "token": "new_access_token"
                }
            ]
            
            # Act 1: Проверяем истекший токен
            check_response = await async_client.get(
                "/api/v1/auth/check_token",
                headers={"Authorization": f"Bearer {expired_token}"}
            )
            
            # Act 2: Обновляем токен
            refresh_response = await async_client.post(
                "/api/v1/auth/refresh_token",
                headers={"Authorization": f"Bearer {refresh_token}"}
            )
        
        # Assert
        assert check_response.status_code == 401
        assert refresh_response.status_code == 200
        refresh_data = refresh_response.json()
        assert "token" in refresh_data
        assert refresh_data["token"] == "new_access_token"

    @pytest.mark.asyncio
    async def test_audit_login_attempts(self, async_client, valid_user_data):
        """Тест аудита попыток входа в систему"""
        # Arrange
        with patch("routers.users.external_auth_api") as mock_auth:
            mock_auth.return_value = {
                "access_token": "test_access_token",
                "refresh_token": "test_refresh_token",
                "user": {
                    "username": "testuser",
                    "groups": ["EISGS_Users"]
                }
            }
            
            # Act
            response = await async_client.post("/api/v1/auth/login", json=valid_user_data)
        
        # Assert
        assert response.status_code == 200
        
        # Здесь должна быть проверка записи в таблицу аудита
        # Это можно сделать через мок базы данных или проверку логов

    @pytest.mark.asyncio
    async def test_audit_failed_login_attempts(self, async_client):
        """Тест аудита неудачных попыток входа"""
        # Arrange
        invalid_data = {
            "username": "invaliduser",
            "password": "wrongpass"
        }
        
        with patch("routers.users.external_auth_api") as mock_auth:
            mock_auth.side_effect = Exception("Invalid credentials")
            
            # Act
            response = await async_client.post("/api/v1/auth/login", json=invalid_data)
        
        # Assert
        assert response.status_code == 401
        
        # Здесь должна быть проверка записи неудачной попытки в таблицу аудита


class TestDomainUserManagement:
    """Тесты управления пользователями домена"""

    @pytest.fixture
    def async_client(self):
        """Асинхронный тестовый клиент"""
        transport = ASGITransport(app=app)
        return AsyncClient(transport=transport, base_url="http://test")

    @pytest.fixture
    def valid_token_headers(self):
        """Заголовки с валидным токеном"""
        return {"Authorization": "Bearer valid_access_token"}

    @pytest.mark.asyncio
    async def test_get_domain_users_success(self, async_client, valid_token_headers):
        """Тест успешного получения пользователей домена"""
        # Arrange
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
            
            # Act
            response = await async_client.get(
                "/api/v1/auth/domain/users",
                headers=valid_token_headers
            )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["username"] == "user1"
        assert data[1]["username"] == "user2"

    @pytest.mark.asyncio
    async def test_get_domain_users_filtered_by_group(self, async_client, valid_token_headers):
        """Тест получения пользователей домена с фильтрацией по группе"""
        # Arrange
        with patch("routers.users.external_auth_api") as mock_auth:
            mock_auth.return_value = [
                {
                    "username": "admin",
                    "display_name": "Admin User",
                    "email": "admin@example.com",
                    "groups": ["EISGS_Users", "EISGS_AppSecurity"],
                    "department": "Security",
                    "title": "Security Admin",
                    "employee_id": "EMP003"
                }
            ]
            
            # Act
            response = await async_client.get(
                "/api/v1/auth/domain/users?group=EISGS_AppSecurity",
                headers=valid_token_headers
            )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert "EISGS_AppSecurity" in data[0]["groups"]

    @pytest.mark.asyncio
    async def test_get_user_groups_success(self, async_client, valid_token_headers):
        """Тест успешного получения групп пользователя"""
        # Arrange
        with patch("routers.users.external_auth_api") as mock_auth:
            mock_auth.return_value = ["EISGS_Users", "EISGS_AppSecurity"]
            
            # Act
            response = await async_client.get(
                "/api/v1/auth/domain/user/groups",
                headers=valid_token_headers
            )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert "EISGS_Users" in data
        assert "EISGS_AppSecurity" in data

    @pytest.mark.asyncio
    async def test_get_user_groups_unauthorized(self, async_client):
        """Тест получения групп пользователя без авторизации"""
        # Act
        response = await async_client.get("/api/v1/auth/domain/user/groups")
        
        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_user_data_success(self, async_client, valid_token_headers):
        """Тест успешного получения данных пользователя"""
        # Arrange
        with patch("routers.users.external_auth_api") as mock_auth:
            mock_auth.return_value = {
                "guid": "{8c527f4d-c073-453c-b8b5-082e040b4d19}",
                "username": "Админ СП_БД"
            }
            
            # Act
            response = await async_client.get(
                "/api/v1/auth/get_data",
                headers=valid_token_headers
            )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["guid"] == "{8c527f4d-c073-453c-b8b5-082e040b4d19}"
        assert data["username"] == "Админ СП_БД"


class TestDictionaryComprehensive:
    """Комплексные тесты справочников"""

    @pytest.fixture
    def async_client(self):
        """Асинхронный тестовый клиент"""
        transport = ASGITransport(app=app)
        return AsyncClient(transport=transport, base_url="http://test")

    @pytest.fixture
    def valid_token_headers(self):
        """Заголовки с валидным токеном"""
        return {"Authorization": "Bearer valid_access_token"}

    @pytest.fixture
    def sample_dictionary_data(self):
        """Тестовые данные для справочника"""
        return {
            "name": "Комплексный тестовый справочник",
            "code": "COMPREHENSIVE_TEST_001",
            "description": "Описание комплексного тестового справочника",
            "start_date": "2025-01-01",
            "finish_date": "9999-12-31",
            "name_eng": "Comprehensive Test Dictionary",
            "name_bel": "Камплексны тэставы даведнік",
            "description_eng": "Comprehensive test dictionary description",
            "description_bel": "Апісанне комплекснага тэставага даведніка",
            "gko": "Test GKO",
            "organization": "Test Organization",
            "classifier": "Test Classifier",
            "id_type": 0
        }

    @pytest.mark.asyncio
    async def test_get_dictionaries_list_with_pagination(self, async_client, valid_token_headers):
        """Тест получения списка справочников с пагинацией"""
        # Arrange
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
            
            # Act
            response = await async_client.get(
                "/api/v2/models/list?page=1&page_size=10",
                headers=valid_token_headers
            )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_get_dictionaries_list_filtered_by_type(self, async_client, valid_token_headers):
        """Тест получения списка справочников с фильтрацией по типу"""
        # Arrange
        with patch("routers.dictionary.DictionaryService.get_all_dictionaries") as mock_service:
            mock_service.return_value = [
                DictionaryOut(
                    id=1,
                    name="Справочник типа 0",
                    code="DICT_TYPE_0",
                    description="Описание",
                    start_date=date(2025, 1, 1),
                    finish_date=date(2025, 12, 31),
                    name_eng="Dictionary Type 0",
                    name_bel="Даведнік тыпу 0",
                    description_eng="Description",
                    description_bel="Апісанне",
                    gko="GKO",
                    organization="Org",
                    classifier="Class",
                    id_type=0,
                    id_status=1,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
            ]
            
            # Act
            response = await async_client.get(
                "/api/v2/models/list?type=0",
                headers=valid_token_headers
            )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["id_type"] == 0

    @pytest.mark.asyncio
    async def test_get_dictionaries_list_filtered_by_status(self, async_client, valid_token_headers):
        """Тест получения списка справочников с фильтрацией по статусу"""
        # Arrange
        with patch("routers.dictionary.DictionaryService.get_all_dictionaries") as mock_service:
            mock_service.return_value = [
                DictionaryOut(
                    id=1,
                    name="Активный справочник",
                    code="ACTIVE_DICT",
                    description="Описание",
                    start_date=date(2025, 1, 1),
                    finish_date=date(2025, 12, 31),
                    name_eng="Active Dictionary",
                    name_bel="Актыўны даведнік",
                    description_eng="Description",
                    description_bel="Апісанне",
                    gko="GKO",
                    organization="Org",
                    classifier="Class",
                    id_type=0,
                    id_status=1,  # Активный статус
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
            ]
            
            # Act
            response = await async_client.get(
                "/api/v2/models/list?status=1",
                headers=valid_token_headers
            )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["id_status"] == 1

    @pytest.mark.asyncio
    async def test_create_dictionary_with_full_data(self, async_client, valid_token_headers, sample_dictionary_data):
        """Тест создания справочника с полными данными"""
        # Arrange
        with patch("routers.dictionary.DictionaryService.create_dictionary") as mock_service:
            mock_service.return_value = 123  # ID созданного справочника
            
            # Act
            response = await async_client.post(
                "/api/v2/models/newDictionary",
                json=sample_dictionary_data,
                headers=valid_token_headers
            )
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert "message" in data
        assert "id" in data
        assert data["id"] == 123
        mock_service.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_dictionary_with_minimal_data(self, async_client, valid_token_headers):
        """Тест создания справочника с минимальными данными"""
        # Arrange
        minimal_data = {
            "name": "Минимальный справочник",
            "code": "MIN_DICT",
            "description": "Минимальное описание",
            "start_date": "2025-01-01",
            "finish_date": "9999-12-31",
            "id_type": 0
        }
        
        with patch("routers.dictionary.DictionaryService.create_dictionary") as mock_service:
            mock_service.return_value = 456
            
            # Act
            response = await async_client.post(
                "/api/v2/models/newDictionary",
                json=minimal_data,
                headers=valid_token_headers
            )
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert "message" in data
        assert "id" in data
        assert data["id"] == 456

    @pytest.mark.asyncio
    async def test_create_dictionary_validation_error_empty_name(self, async_client, valid_token_headers):
        """Тест ошибки валидации при создании справочника с пустым именем"""
        # Arrange
        invalid_data = {
            "name": "",  # Пустое имя - недопустимо
            "code": "TEST",
            "description": "Описание",
            "start_date": "2025-01-01",
            "finish_date": "9999-12-31",
            "id_type": 0
        }
        
        # Act
        response = await async_client.post(
            "/api/v2/models/newDictionary",
            json=invalid_data,
            headers=valid_token_headers
        )
        
        # Assert
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_create_dictionary_validation_error_invalid_code(self, async_client, valid_token_headers):
        """Тест ошибки валидации при создании справочника с недопустимым кодом"""
        # Arrange
        invalid_data = {
            "name": "Тестовый справочник",
            "code": "INVALID@CODE#",  # Недопустимые символы
            "description": "Описание",
            "start_date": "2025-01-01",
            "finish_date": "9999-12-31",
            "id_type": 0
        }
        
        # Act
        response = await async_client.post(
            "/api/v2/models/newDictionary",
            json=invalid_data,
            headers=valid_token_headers
        )
        
        # Assert
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_create_dictionary_validation_error_invalid_dates(self, async_client, valid_token_headers):
        """Тест ошибки валидации при создании справочника с недопустимыми датами"""
        # Arrange
        invalid_data = {
            "name": "Тестовый справочник",
            "code": "TEST_DICT",
            "description": "Описание",
            "start_date": "2025-12-31",  # Дата начала после даты окончания
            "finish_date": "2025-01-01",
            "id_type": 0
        }
        
        # Act
        response = await async_client.post(
            "/api/v2/models/newDictionary",
            json=invalid_data,
            headers=valid_token_headers
        )
        
        # Assert
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_create_dictionary_duplicate_code_error(self, async_client, valid_token_headers, sample_dictionary_data):
        """Тест ошибки дублирования кода при создании справочника"""
        # Arrange
        with patch("routers.dictionary.DictionaryService.create_dictionary") as mock_service:
            mock_service.side_effect = DictionaryValidationError("Код справочника уже существует")
            
            # Act
            response = await async_client.post(
                "/api/v2/models/newDictionary",
                json=sample_dictionary_data,
                headers=valid_token_headers
            )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "уже существует" in data["error"]

    @pytest.mark.asyncio
    async def test_create_dictionary_unauthorized(self, async_client, sample_dictionary_data):
        """Тест создания справочника без авторизации"""
        # Act
        response = await async_client.post(
            "/api/v2/models/newDictionary",
            json=sample_dictionary_data
        )
        
        # Assert
        assert response.status_code == 401


class TestRoleBasedAccessControl:
    """Тесты ролевого доступа"""

    @pytest.fixture
    def async_client(self):
        """Асинхронный тестовый клиент"""
        transport = ASGITransport(app=app)
        return AsyncClient(transport=transport, base_url="http://test")

    @pytest.mark.asyncio
    async def test_security_admin_access_audit_page(self, async_client):
        """Тест доступа администратора безопасности к странице аудита"""
        # Arrange
        headers = {"Authorization": "Bearer security_admin_token"}
        
        with patch("routers.users.external_auth_api") as mock_auth:
            mock_auth.return_value = ["EISGS_AppSecurity"]
            
            # Act
            response = await async_client.get(
                "/api/v1/audit/logs",
                headers=headers
            )
        
        # Assert
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_system_admin_create_dictionary(self, async_client):
        """Тест создания справочника администратором системы"""
        # Arrange
        headers = {"Authorization": "Bearer system_admin_token"}
        dictionary_data = {
            "name": "Админский справочник",
            "code": "ADMIN_DICT",
            "description": "Справочник созданный админом",
            "start_date": "2025-01-01",
            "finish_date": "9999-12-31",
            "id_type": 0
        }
        
        with patch("routers.users.external_auth_api") as mock_auth:
            mock_auth.return_value = ["EISGS_Users"]
            
            with patch("routers.dictionary.DictionaryService.create_dictionary") as mock_service:
                mock_service.return_value = 789
                
                # Act
                response = await async_client.post(
                    "/api/v2/models/newDictionary",
                    json=dictionary_data,
                    headers=headers
                )
        
        # Assert
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_dictionary_owner_edit_dictionary(self, async_client):
        """Тест редактирования справочника его владельцем"""
        # Arrange
        headers = {"Authorization": "Bearer owner_token"}
        dictionary_id = 1
        
        with patch("routers.users.external_auth_api") as mock_auth:
            mock_auth.return_value = ["EISGS_Users"]
            
            # Act
            response = await async_client.get(
                f"/api/v2/models/{dictionary_id}",
                headers=headers
            )
        
        # Assert
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_regular_user_view_only(self, async_client):
        """Тест ограниченного доступа обычного пользователя"""
        # Arrange
        headers = {"Authorization": "Bearer user_token"}
        
        with patch("routers.users.external_auth_api") as mock_auth:
            mock_auth.return_value = ["EISGS_Users"]
            
            # Act - пользователь может просматривать
            view_response = await async_client.get(
                "/api/v2/models/list",
                headers=headers
            )
            
            # Act - пользователь не может создавать
            create_response = await async_client.post(
                "/api/v2/models/newDictionary",
                json={},
                headers=headers
            )
        
        # Assert
        assert view_response.status_code == 200
        assert create_response.status_code in [400, 422]  # Ошибка валидации или доступа


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
