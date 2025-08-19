"""
Тесты ролевой модели доступа к системе справочников
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
from routers.audit import audit_router
from services.dictionary_service import DictionaryService
from schemas import DictionaryIn, DictionaryOut, UserInfo
from exceptions import DictionaryNotFoundError, DictionaryValidationError, InsufficientPermissionsError


class TestSecurityAdministratorRole:
    """Тесты роли администратора безопасности"""

    @pytest.fixture
    def async_client(self):
        """Асинхронный тестовый клиент"""
        transport = ASGITransport(app=app)
        return AsyncClient(transport=transport, base_url="http://test")

    @pytest.fixture
    def security_admin_headers(self):
        """Заголовки администратора безопасности"""
        return {"Authorization": "Bearer security_admin_token"}

    @pytest.mark.asyncio
    async def test_security_admin_can_access_audit_page(self, async_client, security_admin_headers):
        """Тест доступа администратора безопасности к странице аудита"""
        # Arrange
        with patch("routers.users.external_auth_api") as mock_auth:
            mock_auth.return_value = ["EISGS_AppSecurity"]
            
            # Act
            response = await async_client.get(
                "/api/v1/audit/logs",
                headers=security_admin_headers
            )
        
        # Assert
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_security_admin_can_view_all_audit_logs(self, async_client, security_admin_headers):
        """Тест просмотра всех записей аудита администратором безопасности"""
        # Arrange
        with patch("routers.users.external_auth_api") as mock_auth:
            mock_auth.return_value = ["EISGS_AppSecurity"]
            
            with patch("routers.audit.AuditService.get_audit_logs") as mock_service:
                mock_service.return_value = [
                    {
                        "id": 1,
                        "user_id": "user1",
                        "action": "LOGIN",
                        "timestamp": datetime.now(),
                        "ip_address": "192.168.1.1",
                        "details": "Successful login"
                    },
                    {
                        "id": 2,
                        "user_id": "user2",
                        "action": "CREATE_DICTIONARY",
                        "timestamp": datetime.now(),
                        "ip_address": "192.168.1.2",
                        "details": "Created dictionary TEST_DICT"
                    }
                ]
                
                # Act
                response = await async_client.get(
                    "/api/v1/audit/logs",
                    headers=security_admin_headers
                )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_security_admin_can_filter_audit_logs(self, async_client, security_admin_headers):
        """Тест фильтрации записей аудита администратором безопасности"""
        # Arrange
        with patch("routers.users.external_auth_api") as mock_auth:
            mock_auth.return_value = ["EISGS_AppSecurity"]
            
            with patch("routers.audit.AuditService.get_audit_logs") as mock_service:
                mock_service.return_value = [
                    {
                        "id": 1,
                        "user_id": "user1",
                        "action": "LOGIN",
                        "timestamp": datetime.now(),
                        "ip_address": "192.168.1.1",
                        "details": "Successful login"
                    }
                ]
                
                # Act
                response = await async_client.get(
                    "/api/v1/audit/logs?action=LOGIN&user_id=user1",
                    headers=security_admin_headers
                )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["action"] == "LOGIN"

    @pytest.mark.asyncio
    async def test_security_admin_can_assign_system_admin_role(self, async_client, security_admin_headers):
        """Тест назначения роли администратора системы"""
        # Arrange
        user_id = 123
        role_data = {"is_admin": True}
        
        with patch("routers.users.external_auth_api") as mock_auth:
            mock_auth.return_value = ["EISGS_AppSecurity"]
            
            with patch("routers.users.update_user_admin_status") as mock_update:
                mock_update.return_value = True
                
                # Act
                response = await async_client.patch(
                    f"/api/v1/users/{user_id}/admin",
                    json=role_data,
                    headers=security_admin_headers
                )
        
        # Assert
        assert response.status_code == 200
        mock_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_security_admin_cannot_create_dictionary(self, async_client, security_admin_headers):
        """Тест запрета создания справочника администратором безопасности"""
        # Arrange
        dictionary_data = {
            "name": "Тестовый справочник",
            "code": "TEST_DICT",
            "description": "Описание",
            "start_date": "2025-01-01",
            "finish_date": "9999-12-31",
            "id_type": 0
        }
        
        with patch("routers.users.external_auth_api") as mock_auth:
            mock_auth.return_value = ["EISGS_AppSecurity"]  # Только группа безопасности
            
            # Act
            response = await async_client.post(
                "/api/v2/models/newDictionary",
                json=dictionary_data,
                headers=security_admin_headers
            )
        
        # Assert
        assert response.status_code == 403  # Forbidden


class TestSystemAdministratorRole:
    """Тесты роли администратора системы"""

    @pytest.fixture
    def async_client(self):
        """Асинхронный тестовый клиент"""
        transport = ASGITransport(app=app)
        return AsyncClient(transport=transport, base_url="http://test")

    @pytest.fixture
    def system_admin_headers(self):
        """Заголовки администратора системы"""
        return {"Authorization": "Bearer system_admin_token"}

    @pytest.mark.asyncio
    async def test_system_admin_can_create_dictionary(self, async_client, system_admin_headers):
        """Тест создания справочника администратором системы"""
        # Arrange
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
                    headers=system_admin_headers
                )
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["id"] == 789

    @pytest.mark.asyncio
    async def test_system_admin_can_assign_dictionary_owner(self, async_client, system_admin_headers):
        """Тест назначения владельца справочника администратором системы"""
        # Arrange
        dictionary_id = 1
        owner_data = {"user_id": 456, "username": "new_owner"}
        
        with patch("routers.users.external_auth_api") as mock_auth:
            mock_auth.return_value = ["EISGS_Users"]
            
            with patch("routers.dictionary.DictionaryService.assign_owner") as mock_service:
                mock_service.return_value = True
                
                # Act
                response = await async_client.post(
                    f"/api/v2/models/{dictionary_id}/owner",
                    json=owner_data,
                    headers=system_admin_headers
                )
        
        # Assert
        assert response.status_code == 200
        mock_service.assert_called_once()

    @pytest.mark.asyncio
    async def test_system_admin_is_owner_of_all_dictionaries(self, async_client, system_admin_headers):
        """Тест что администратор системы является владельцем всех справочников"""
        # Arrange
        with patch("routers.users.external_auth_api") as mock_auth:
            mock_auth.return_value = ["EISGS_Users"]
            
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
                    )
                ]
                
                # Act
                response = await async_client.get(
                    "/api/v2/models/list",
                    headers=system_admin_headers
                )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    @pytest.mark.asyncio
    async def test_system_admin_cannot_access_audit_page(self, async_client, system_admin_headers):
        """Тест запрета доступа к странице аудита администратором системы"""
        # Arrange
        with patch("routers.users.external_auth_api") as mock_auth:
            mock_auth.return_value = ["EISGS_Users"]  # Только группа пользователей
            
            # Act
            response = await async_client.get(
                "/api/v1/audit/logs",
                headers=system_admin_headers
            )
        
        # Assert
        assert response.status_code == 403  # Forbidden


class TestDictionaryOwnerRole:
    """Тесты роли владельца справочника"""

    @pytest.fixture
    def async_client(self):
        """Асинхронный тестовый клиент"""
        transport = ASGITransport(app=app)
        return AsyncClient(transport=transport, base_url="http://test")

    @pytest.fixture
    def dictionary_owner_headers(self):
        """Заголовки владельца справочника"""
        return {"Authorization": "Bearer owner_token"}

    @pytest.mark.asyncio
    async def test_dictionary_owner_can_edit_owned_dictionary(self, async_client, dictionary_owner_headers):
        """Тест редактирования справочника его владельцем"""
        # Arrange
        dictionary_id = 1
        update_data = {
            "name": "Обновленное название",
            "description": "Обновленное описание"
        }
        
        with patch("routers.users.external_auth_api") as mock_auth:
            mock_auth.return_value = ["EISGS_Users"]
            
            with patch("routers.dictionary.DictionaryService.update_dictionary") as mock_service:
                mock_service.return_value = True
                
                # Act
                response = await async_client.put(
                    f"/api/v2/models/{dictionary_id}",
                    json=update_data,
                    headers=dictionary_owner_headers
                )
        
        # Assert
        assert response.status_code == 200
        mock_service.assert_called_once()

    @pytest.mark.asyncio
    async def test_dictionary_owner_can_import_data(self, async_client, dictionary_owner_headers):
        """Тест импорта данных владельцем справочника"""
        # Arrange
        dictionary_id = 1
        import_data = {
            "positions": [
                {
                    "code": "POS_001",
                    "name": "Позиция 1",
                    "description": "Описание позиции 1"
                }
            ]
        }
        
        with patch("routers.users.external_auth_api") as mock_auth:
            mock_auth.return_value = ["EISGS_Users"]
            
            with patch("routers.dictionary.DictionaryService.import_positions") as mock_service:
                mock_service.return_value = 1  # Количество импортированных позиций
                
                # Act
                response = await async_client.post(
                    f"/api/v2/models/{dictionary_id}/import",
                    json=import_data,
                    headers=dictionary_owner_headers
                )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "imported_count" in data
        assert data["imported_count"] == 1

    @pytest.mark.asyncio
    async def test_dictionary_owner_cannot_edit_other_dictionary(self, async_client, dictionary_owner_headers):
        """Тест запрета редактирования чужого справочника"""
        # Arrange
        other_dictionary_id = 999
        update_data = {"name": "Попытка редактирования"}
        
        with patch("routers.users.external_auth_api") as mock_auth:
            mock_auth.return_value = ["EISGS_Users"]
            
            with patch("routers.dictionary.DictionaryService.update_dictionary") as mock_service:
                mock_service.side_effect = InsufficientPermissionsError("Недостаточно прав")
                
                # Act
                response = await async_client.put(
                    f"/api/v2/models/{other_dictionary_id}",
                    json=update_data,
                    headers=dictionary_owner_headers
                )
        
        # Assert
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_dictionary_owner_cannot_create_new_dictionary(self, async_client, dictionary_owner_headers):
        """Тест запрета создания нового справочника владельцем"""
        # Arrange
        dictionary_data = {
            "name": "Новый справочник",
            "code": "NEW_DICT",
            "description": "Описание",
            "start_date": "2025-01-01",
            "finish_date": "9999-12-31",
            "id_type": 0
        }
        
        with patch("routers.users.external_auth_api") as mock_auth:
            mock_auth.return_value = ["EISGS_Users"]
            
            # Act
            response = await async_client.post(
                "/api/v2/models/newDictionary",
                json=dictionary_data,
                headers=dictionary_owner_headers
            )
        
        # Assert
        assert response.status_code == 403  # Forbidden


class TestRegularUserRole:
    """Тесты роли обычного пользователя"""

    @pytest.fixture
    def async_client(self):
        """Асинхронный тестовый клиент"""
        transport = ASGITransport(app=app)
        return AsyncClient(transport=transport, base_url="http://test")

    @pytest.fixture
    def regular_user_headers(self):
        """Заголовки обычного пользователя"""
        return {"Authorization": "Bearer user_token"}

    @pytest.mark.asyncio
    async def test_regular_user_can_view_dictionaries(self, async_client, regular_user_headers):
        """Тест просмотра справочников обычным пользователем"""
        # Arrange
        with patch("routers.users.external_auth_api") as mock_auth:
            mock_auth.return_value = ["EISGS_Users"]
            
            with patch("routers.dictionary.DictionaryService.get_all_dictionaries") as mock_service:
                mock_service.return_value = [
                    DictionaryOut(
                        id=1,
                        name="Публичный справочник",
                        code="PUBLIC_DICT",
                        description="Описание",
                        start_date=date(2025, 1, 1),
                        finish_date=date(2025, 12, 31),
                        name_eng="Public Dictionary",
                        name_bel="Публічны даведнік",
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
                    "/api/v2/models/list",
                    headers=regular_user_headers
                )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    @pytest.mark.asyncio
    async def test_regular_user_can_export_dictionary(self, async_client, regular_user_headers):
        """Тест экспорта справочника обычным пользователем"""
        # Arrange
        dictionary_id = 1
        
        with patch("routers.users.external_auth_api") as mock_auth:
            mock_auth.return_value = ["EISGS_Users"]
            
            with patch("routers.dictionary.DictionaryService.export_dictionary") as mock_service:
                mock_service.return_value = {
                    "format": "json",
                    "data": {"dictionary": "exported_data"}
                }
                
                # Act
                response = await async_client.get(
                    f"/api/v2/models/{dictionary_id}/export?format=json",
                    headers=regular_user_headers
                )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    @pytest.mark.asyncio
    async def test_regular_user_cannot_create_dictionary(self, async_client, regular_user_headers):
        """Тест запрета создания справочника обычным пользователем"""
        # Arrange
        dictionary_data = {
            "name": "Пользовательский справочник",
            "code": "USER_DICT",
            "description": "Описание",
            "start_date": "2025-01-01",
            "finish_date": "9999-12-31",
            "id_type": 0
        }
        
        with patch("routers.users.external_auth_api") as mock_auth:
            mock_auth.return_value = ["EISGS_Users"]
            
            # Act
            response = await async_client.post(
                "/api/v2/models/newDictionary",
                json=dictionary_data,
                headers=regular_user_headers
            )
        
        # Assert
        assert response.status_code == 403  # Forbidden

    @pytest.mark.asyncio
    async def test_regular_user_cannot_edit_dictionary(self, async_client, regular_user_headers):
        """Тест запрета редактирования справочника обычным пользователем"""
        # Arrange
        dictionary_id = 1
        update_data = {"name": "Попытка редактирования"}
        
        with patch("routers.users.external_auth_api") as mock_auth:
            mock_auth.return_value = ["EISGS_Users"]
            
            # Act
            response = await async_client.put(
                f"/api/v2/models/{dictionary_id}",
                json=update_data,
                headers=regular_user_headers
            )
        
        # Assert
        assert response.status_code == 403  # Forbidden

    @pytest.mark.asyncio
    async def test_regular_user_cannot_access_audit_page(self, async_client, regular_user_headers):
        """Тест запрета доступа к странице аудита обычным пользователем"""
        # Arrange
        with patch("routers.users.external_auth_api") as mock_auth:
            mock_auth.return_value = ["EISGS_Users"]
            
            # Act
            response = await async_client.get(
                "/api/v1/audit/logs",
                headers=regular_user_headers
            )
        
        # Assert
        assert response.status_code == 403  # Forbidden


class TestRoleHierarchy:
    """Тесты иерархии ролей"""

    @pytest.fixture
    def async_client(self):
        """Асинхронный тестовый клиент"""
        transport = ASGITransport(app=app)
        return AsyncClient(transport=transport, base_url="http://test")

    @pytest.mark.asyncio
    async def test_user_with_multiple_roles(self, async_client):
        """Тест пользователя с несколькими ролями"""
        # Arrange
        multi_role_headers = {"Authorization": "Bearer multi_role_token"}
        
        with patch("routers.users.external_auth_api") as mock_auth:
            mock_auth.return_value = ["EISGS_Users", "EISGS_AppSecurity"]
            
            # Act 1: Доступ к справочникам (EISGS_Users)
            dict_response = await async_client.get(
                "/api/v2/models/list",
                headers=multi_role_headers
            )
            
            # Act 2: Доступ к аудиту (EISGS_AppSecurity)
            audit_response = await async_client.get(
                "/api/v1/audit/logs",
                headers=multi_role_headers
            )
        
        # Assert
        assert dict_response.status_code == 200
        assert audit_response.status_code == 200

    @pytest.mark.asyncio
    async def test_role_inheritance(self, async_client):
        """Тест наследования ролей"""
        # Arrange
        admin_headers = {"Authorization": "Bearer admin_token"}
        
        with patch("routers.users.external_auth_api") as mock_auth:
            mock_auth.return_value = ["EISGS_Users", "EISGS_AppSecurity"]
            
            # Act: Администратор безопасности должен иметь доступ ко всем функциям
            responses = []
            
            # Доступ к справочникам
            dict_response = await async_client.get(
                "/api/v2/models/list",
                headers=admin_headers
            )
            responses.append(dict_response.status_code)
            
            # Доступ к аудиту
            audit_response = await async_client.get(
                "/api/v1/audit/logs",
                headers=admin_headers
            )
            responses.append(audit_response.status_code)
            
            # Доступ к пользователям
            users_response = await async_client.get(
                "/api/v1/users",
                headers=admin_headers
            )
            responses.append(users_response.status_code)
        
        # Assert: Все запросы должны быть успешными
        assert all(status == 200 for status in responses)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
