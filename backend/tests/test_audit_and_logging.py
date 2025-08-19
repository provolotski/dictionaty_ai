"""
Тесты аудита действий пользователей и логирования
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import date, datetime, timedelta
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI, HTTPException

from main import app
from routers.audit import audit_router
from routers.users import users_router
from routers.dictionary import dict_router


class TestAuditLogging:
    """Тесты аудита действий пользователей"""

    @pytest.fixture
    def async_client(self):
        """Асинхронный тестовый клиент"""
        transport = ASGITransport(app=app)
        return AsyncClient(transport=transport, base_url="http://test")

    @pytest.fixture
    def security_admin_headers(self):
        """Заголовки администратора безопасности"""
        return {"Authorization": "Bearer security_admin_token"}

    @pytest.fixture
    def regular_user_headers(self):
        """Заголовки обычного пользователя"""
        return {"Authorization": "Bearer user_token"}

    @pytest.mark.asyncio
    async def test_login_audit_logging_success(self, async_client):
        """Тест логирования успешного входа в систему"""
        # Arrange
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
            
            with patch("routers.audit.AuditService.log_action") as mock_audit:
                mock_audit.return_value = True
                
                # Act
                response = await async_client.post("/api/v1/auth/login", json=login_data)
        
        # Assert
        assert response.status_code == 200
        
        # Проверяем что действие было залогировано
        mock_audit.assert_called_once()
        call_args = mock_audit.call_args
        assert call_args[1]["action"] == "LOGIN"
        assert call_args[1]["user_id"] == "testuser"
        assert call_args[1]["status"] == "SUCCESS"

    @pytest.mark.asyncio
    async def test_login_audit_logging_failure(self, async_client):
        """Тест логирования неудачного входа в систему"""
        # Arrange
        login_data = {
            "username": "invaliduser",
            "password": "wrongpass"
        }
        
        with patch("routers.users.external_auth_api") as mock_auth:
            mock_auth.side_effect = Exception("Invalid credentials")
            
            with patch("routers.audit.AuditService.log_action") as mock_audit:
                mock_audit.return_value = True
                
                # Act
                response = await async_client.post("/api/v1/auth/login", json=login_data)
        
        # Assert
        assert response.status_code == 401
        
        # Проверяем что неудачная попытка была залогирована
        mock_audit.assert_called_once()
        call_args = mock_audit.call_args
        assert call_args[1]["action"] == "LOGIN"
        assert call_args[1]["user_id"] == "invaliduser"
        assert call_args[1]["status"] == "FAILURE"

    @pytest.mark.asyncio
    async def test_dictionary_creation_audit_logging(self, async_client, security_admin_headers):
        """Тест логирования создания справочника"""
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
            mock_auth.return_value = ["EISGS_Users"]
            
            with patch("routers.dictionary.DictionaryService.create_dictionary") as mock_service:
                mock_service.return_value = 123
                
                with patch("routers.audit.AuditService.log_action") as mock_audit:
                    mock_audit.return_value = True
                    
                    # Act
                    response = await async_client.post(
                        "/api/v2/models/newDictionary",
                        json=dictionary_data,
                        headers=security_admin_headers
                    )
        
        # Assert
        assert response.status_code == 201
        
        # Проверяем что создание справочника было залогировано
        mock_audit.assert_called_once()
        call_args = mock_audit.call_args
        assert call_args[1]["action"] == "CREATE_DICTIONARY"
        assert call_args[1]["status"] == "SUCCESS"
        assert "dictionary_id" in call_args[1]["details"]

    @pytest.mark.asyncio
    async def test_dictionary_update_audit_logging(self, async_client, security_admin_headers):
        """Тест логирования обновления справочника"""
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
                
                with patch("routers.audit.AuditService.log_action") as mock_audit:
                    mock_audit.return_value = True
                    
                    # Act
                    response = await async_client.put(
                        f"/api/v2/models/{dictionary_id}",
                        json=update_data,
                        headers=security_admin_headers
                    )
        
        # Assert
        assert response.status_code == 200
        
        # Проверяем что обновление было залогировано
        mock_audit.assert_called_once()
        call_args = mock_audit.call_args
        assert call_args[1]["action"] == "UPDATE_DICTIONARY"
        assert call_args[1]["status"] == "SUCCESS"
        assert call_args[1]["dictionary_id"] == dictionary_id

    @pytest.mark.asyncio
    async def test_dictionary_deletion_audit_logging(self, async_client, security_admin_headers):
        """Тест логирования удаления справочника"""
        # Arrange
        dictionary_id = 1
        
        with patch("routers.users.external_auth_api") as mock_auth:
            mock_auth.return_value = ["EISGS_Users"]
            
            with patch("routers.dictionary.DictionaryService.delete_dictionary") as mock_service:
                mock_service.return_value = True
                
                with patch("routers.audit.AuditService.log_action") as mock_audit:
                    mock_audit.return_value = True
                    
                    # Act
                    response = await async_client.delete(
                        f"/api/v2/models/{dictionary_id}",
                        headers=security_admin_headers
                    )
        
        # Assert
        assert response.status_code == 200
        
        # Проверяем что удаление было залогировано
        mock_audit.assert_called_once()
        call_args = mock_audit.call_args
        assert call_args[1]["action"] == "DELETE_DICTIONARY"
        assert call_args[1]["status"] == "SUCCESS"
        assert call_args[1]["dictionary_id"] == dictionary_id

    @pytest.mark.asyncio
    async def test_user_role_change_audit_logging(self, async_client, security_admin_headers):
        """Тест логирования изменения роли пользователя"""
        # Arrange
        user_id = 123
        role_data = {"is_admin": True}
        
        with patch("routers.users.external_auth_api") as mock_auth:
            mock_auth.return_value = ["EISGS_AppSecurity"]
            
            with patch("routers.users.update_user_admin_status") as mock_update:
                mock_update.return_value = True
                
                with patch("routers.audit.AuditService.log_action") as mock_audit:
                    mock_audit.return_value = True
                    
                    # Act
                    response = await async_client.patch(
                        f"/api/v1/users/{user_id}/admin",
                        json=role_data,
                        headers=security_admin_headers
                    )
        
        # Assert
        assert response.status_code == 200
        
        # Проверяем что изменение роли было залогировано
        mock_audit.assert_called_once()
        call_args = mock_audit.call_args
        assert call_args[1]["action"] == "CHANGE_USER_ROLE"
        assert call_args[1]["status"] == "SUCCESS"
        assert call_args[1]["target_user_id"] == user_id


class TestAuditRetrieval:
    """Тесты получения записей аудита"""

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
    async def test_get_audit_logs_success(self, async_client, security_admin_headers):
        """Тест успешного получения записей аудита"""
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
                        "status": "SUCCESS",
                        "details": "Successful login"
                    },
                    {
                        "id": 2,
                        "user_id": "user2",
                        "action": "CREATE_DICTIONARY",
                        "timestamp": datetime.now(),
                        "ip_address": "192.168.1.2",
                        "status": "SUCCESS",
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
        assert data[0]["action"] == "LOGIN"
        assert data[1]["action"] == "CREATE_DICTIONARY"

    @pytest.mark.asyncio
    async def test_get_audit_logs_with_filters(self, async_client, security_admin_headers):
        """Тест получения записей аудита с фильтрами"""
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
                        "status": "SUCCESS",
                        "details": "Successful login"
                    }
                ]
                
                # Act
                response = await async_client.get(
                    "/api/v1/audit/logs?action=LOGIN&user_id=user1&status=SUCCESS",
                    headers=security_admin_headers
                )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["action"] == "LOGIN"
        assert data[0]["user_id"] == "user1"
        assert data[0]["status"] == "SUCCESS"

    @pytest.mark.asyncio
    async def test_get_audit_logs_with_date_range(self, async_client, security_admin_headers):
        """Тест получения записей аудита с диапазоном дат"""
        # Arrange
        start_date = "2025-01-01"
        end_date = "2025-01-31"
        
        with patch("routers.users.external_auth_api") as mock_auth:
            mock_auth.return_value = ["EISGS_AppSecurity"]
            
            with patch("routers.audit.AuditService.get_audit_logs") as mock_service:
                mock_service.return_value = [
                    {
                        "id": 1,
                        "user_id": "user1",
                        "action": "LOGIN",
                        "timestamp": datetime(2025, 1, 15),
                        "ip_address": "192.168.1.1",
                        "status": "SUCCESS",
                        "details": "Successful login"
                    }
                ]
                
                # Act
                response = await async_client.get(
                    f"/api/v1/audit/logs?start_date={start_date}&end_date={end_date}",
                    headers=security_admin_headers
                )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    @pytest.mark.asyncio
    async def test_get_audit_logs_with_pagination(self, async_client, security_admin_headers):
        """Тест получения записей аудита с пагинацией"""
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
                        "status": "SUCCESS",
                        "details": "Successful login"
                    }
                ]
                
                # Act
                response = await async_client.get(
                    "/api/v1/audit/logs?page=1&page_size=10",
                    headers=security_admin_headers
                )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    @pytest.mark.asyncio
    async def test_get_audit_logs_unauthorized(self, async_client):
        """Тест получения записей аудита без авторизации"""
        # Act
        response = await async_client.get("/api/v1/audit/logs")
        
        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_audit_logs_insufficient_permissions(self, async_client, regular_user_headers):
        """Тест получения записей аудита с недостаточными правами"""
        # Arrange
        with patch("routers.users.external_auth_api") as mock_auth:
            mock_auth.return_value = ["EISGS_Users"]  # Только группа пользователей
            
            # Act
            response = await async_client.get(
                "/api/v1/audit/logs",
                headers=regular_user_headers
            )
        
        # Assert
        assert response.status_code == 403


class TestAuditDataIntegrity:
    """Тесты целостности данных аудита"""

    @pytest.fixture
    def async_client(self):
        """Асинхронный тестовый клиент"""
        transport = ASGITransport(app=app)
        return AsyncClient(transport=transport, base_url="http://test")

    @pytest.mark.asyncio
    async def test_audit_log_contains_required_fields(self, async_client):
        """Тест что записи аудита содержат все обязательные поля"""
        # Arrange
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
            
            with patch("routers.audit.AuditService.log_action") as mock_audit:
                mock_audit.return_value = True
                
                # Act
                response = await async_client.post("/api/v1/auth/login", json=login_data)
        
        # Assert
        assert response.status_code == 200
        
        # Проверяем что все обязательные поля были переданы в аудит
        mock_audit.assert_called_once()
        call_args = mock_audit.call_args[1]
        
        required_fields = ["user_id", "action", "timestamp", "ip_address", "status"]
        for field in required_fields:
            assert field in call_args, f"Поле {field} отсутствует в записи аудита"

    @pytest.mark.asyncio
    async def test_audit_log_timestamp_format(self, async_client):
        """Тест формата временной метки в записях аудита"""
        # Arrange
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
            
            with patch("routers.audit.AuditService.log_action") as mock_audit:
                mock_audit.return_value = True
                
                # Act
                response = await async_client.post("/api/v1/auth/login", json=login_data)
        
        # Assert
        assert response.status_code == 200
        
        # Проверяем формат временной метки
        mock_audit.assert_called_once()
        call_args = mock_audit.call_args[1]
        timestamp = call_args["timestamp"]
        
        # Временная метка должна быть datetime объектом
        assert isinstance(timestamp, datetime)
        
        # Временная метка должна быть в разумных пределах (не в будущем и не слишком в прошлом)
        now = datetime.now()
        assert timestamp <= now
        assert timestamp > now - timedelta(minutes=5)  # Не старше 5 минут

    @pytest.mark.asyncio
    async def test_audit_log_ip_address_format(self, async_client):
        """Тест формата IP адреса в записях аудита"""
        # Arrange
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
            
            with patch("routers.audit.AuditService.log_action") as mock_audit:
                mock_audit.return_value = True
                
                # Act
                response = await async_client.post("/api/v1/auth/login", json=login_data)
        
        # Assert
        assert response.status_code == 200
        
        # Проверяем формат IP адреса
        mock_audit.assert_called_once()
        call_args = mock_audit.call_args[1]
        ip_address = call_args["ip_address"]
        
        # IP адрес должен быть строкой
        assert isinstance(ip_address, str)
        
        # IP адрес должен быть в валидном формате (базовая проверка)
        assert "." in ip_address or ":" in ip_address  # IPv4 или IPv6


class TestAuditPerformance:
    """Тесты производительности аудита"""

    @pytest.fixture
    def async_client(self):
        """Асинхронный тестовый клиент"""
        transport = ASGITransport(app=app)
        return AsyncClient(transport=transport, base_url="http://test")

    @pytest.mark.asyncio
    async def test_audit_logging_performance(self, async_client):
        """Тест производительности логирования аудита"""
        # Arrange
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
            
            with patch("routers.audit.AuditService.log_action") as mock_audit:
                mock_audit.return_value = True
                
                # Act
                start_time = datetime.now()
                response = await async_client.post("/api/v1/auth/login", json=login_data)
                end_time = datetime.now()
        
        # Assert
        assert response.status_code == 200
        
        # Время выполнения должно быть приемлемым (менее 1 секунды)
        execution_time = (end_time - start_time).total_seconds()
        assert execution_time < 1.0, f"Время выполнения слишком велико: {execution_time} секунд"

    @pytest.mark.asyncio
    async def test_audit_retrieval_performance(self, async_client, security_admin_headers):
        """Тест производительности получения записей аудита"""
        # Arrange
        with patch("routers.users.external_auth_api") as mock_auth:
            mock_auth.return_value = ["EISGS_AppSecurity"]
            
            with patch("routers.audit.AuditService.get_audit_logs") as mock_service:
                # Мокаем большое количество записей
                mock_service.return_value = [
                    {
                        "id": i,
                        "user_id": f"user{i}",
                        "action": "LOGIN",
                        "timestamp": datetime.now(),
                        "ip_address": f"192.168.1.{i % 255}",
                        "status": "SUCCESS",
                        "details": f"Login attempt {i}"
                    }
                    for i in range(1000)  # 1000 записей
                ]
                
                # Act
                start_time = datetime.now()
                response = await async_client.get(
                    "/api/v1/audit/logs?page=1&page_size=100",
                    headers=security_admin_headers
                )
                end_time = datetime.now()
        
        # Assert
        assert response.status_code == 200
        
        # Время выполнения должно быть приемлемым даже для большого количества записей
        execution_time = (end_time - start_time).total_seconds()
        assert execution_time < 2.0, f"Время выполнения слишком велико: {execution_time} секунд"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
