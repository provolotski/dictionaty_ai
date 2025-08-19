"""
Тесты интеграции с внешними API авторизации
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import date, datetime, timedelta
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI, HTTPException
import httpx

from main import app
from routers.users import users_router
from routers.dictionary import dict_router


class TestExternalAuthAPIIntegration:
    """Тесты интеграции с внешними API авторизации"""

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
    def external_auth_base_url(self):
        """Базовый URL внешнего API авторизации"""
        return "http://127.0.0.1:9090/api/v1/auth"

    @pytest.mark.asyncio
    async def test_check_token_endpoint_integration(self, async_client, external_auth_base_url):
        """Тест интеграции с эндпоинтом проверки токена"""
        # Arrange
        valid_token = "valid_access_token_123"
        headers = {"Authorization": f"Bearer {valid_token}"}
        
        # Мокаем HTTP клиент для внешнего API
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "valid": True,
                "user": {
                    "username": "testuser",
                    "groups": ["EISGS_Users"]
                }
            }
            mock_get.return_value = mock_response
            
            # Act
            response = await async_client.get(
                "/api/v1/auth/check_token",
                headers=headers
            )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert "user" in data

    @pytest.mark.asyncio
    async def test_check_token_expired_integration(self, async_client, external_auth_base_url):
        """Тест интеграции с эндпоинтом проверки истекшего токена"""
        # Arrange
        expired_token = "expired_access_token_456"
        headers = {"Authorization": f"Bearer {expired_token}"}
        
        # Мокаем HTTP клиент для внешнего API
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.json.return_value = {
                "valid": False,
                "expired": True,
                "error": "Token expired"
            }
            mock_get.return_value = mock_response
            
            # Act
            response = await async_client.get(
                "/api/v1/auth/check_token",
                headers=headers
            )
        
        # Assert
        assert response.status_code == 401
        data = response.json()
        assert data["valid"] is False
        assert data["expired"] is True

    @pytest.mark.asyncio
    async def test_refresh_token_endpoint_integration(self, async_client, external_auth_base_url):
        """Тест интеграции с эндпоинтом обновления токена"""
        # Arrange
        refresh_token = "valid_refresh_token_789"
        headers = {"Authorization": f"Bearer {refresh_token}"}
        
        # Мокаем HTTP клиент для внешнего API
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": 200,
                "token": "new_access_token_abc"
            }
            mock_post.return_value = mock_response
            
            # Act
            response = await async_client.post(
                "/api/v1/auth/refresh_token",
                headers=headers
            )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["token"] == "new_access_token_abc"

    @pytest.mark.asyncio
    async def test_refresh_token_invalid_integration(self, async_client, external_auth_base_url):
        """Тест интеграции с эндпоинтом обновления невалидного токена"""
        # Arrange
        invalid_refresh_token = "invalid_refresh_token_xyz"
        headers = {"Authorization": f"Bearer {invalid_refresh_token}"}
        
        # Мокаем HTTP клиент для внешнего API
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.json.return_value = {
                "status": 401,
                "error": "Invalid refresh token"
            }
            mock_post.return_value = mock_response
            
            # Act
            response = await async_client.post(
                "/api/v1/auth/refresh_token",
                headers=headers
            )
        
        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "error" in data

    @pytest.mark.asyncio
    async def test_get_user_data_endpoint_integration(self, async_client, external_auth_base_url):
        """Тест интеграции с эндпоинтом получения данных пользователя"""
        # Arrange
        access_token = "valid_access_token_123"
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Мокаем HTTP клиент для внешнего API
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "guid": "{8c527f4d-c073-453c-b8b5-082e040b4d19}",
                "username": "Админ СП_БД"
            }
            mock_get.return_value = mock_response
            
            # Act
            response = await async_client.get(
                "/api/v1/auth/get_data",
                headers=headers
            )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["guid"] == "{8c527f4d-c073-453c-b8b5-082e040b4d19}"
        assert data["username"] == "Админ СП_БД"

    @pytest.mark.asyncio
    async def test_get_user_groups_endpoint_integration(self, async_client, external_auth_base_url):
        """Тест интеграции с эндпоинтом получения групп пользователя"""
        # Arrange
        access_token = "valid_access_token_123"
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Мокаем HTTP клиент для внешнего API
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = ["EISGS_Users", "EISGS_AppSecurity"]
            mock_get.return_value = mock_response
            
            # Act
            response = await async_client.get(
                "/api/v1/auth/domain/user/groups",
                headers=headers
            )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert "EISGS_Users" in data
        assert "EISGS_AppSecurity" in data

    @pytest.mark.asyncio
    async def test_external_api_connection_error(self, async_client):
        """Тест обработки ошибки подключения к внешнему API"""
        # Arrange
        access_token = "valid_access_token_123"
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Мокаем HTTP клиент для внешнего API с ошибкой подключения
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.side_effect = httpx.ConnectError("Connection failed")
            
            # Act
            response = await async_client.get(
                "/api/v1/auth/check_token",
                headers=headers
            )
        
        # Assert
        assert response.status_code == 503  # Service Unavailable
        data = response.json()
        assert "error" in data

    @pytest.mark.asyncio
    async def test_external_api_timeout_error(self, async_client):
        """Тест обработки ошибки таймаута внешнего API"""
        # Arrange
        access_token = "valid_access_token_123"
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Мокаем HTTP клиент для внешнего API с ошибкой таймаута
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.side_effect = httpx.TimeoutException("Request timeout")
            
            # Act
            response = await async_client.get(
                "/api/v1/auth/check_token",
                headers=headers
            )
        
        # Assert
        assert response.status_code == 504  # Gateway Timeout
        data = response.json()
        assert "error" in data

    @pytest.mark.asyncio
    async def test_external_api_http_error(self, async_client):
        """Тест обработки HTTP ошибки от внешнего API"""
        # Arrange
        access_token = "valid_access_token_123"
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Мокаем HTTP клиент для внешнего API с HTTP ошибкой
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.json.return_value = {
                "error": "Internal server error"
            }
            mock_get.return_value = mock_response
            
            # Act
            response = await async_client.get(
                "/api/v1/auth/check_token",
                headers=headers
            )
        
        # Assert
        assert response.status_code == 502  # Bad Gateway
        data = response.json()
        assert "error" in data


class TestAuthenticationWorkflow:
    """Тесты полного цикла аутентификации"""

    @pytest.fixture
    def async_client(self):
        """Асинхронный тестовый клиент"""
        transport = ASGITransport(app=app)
        return AsyncClient(transport=transport, base_url="http://test")

    @pytest.mark.asyncio
    async def test_full_authentication_workflow(self, async_client):
        """Тест полного цикла аутентификации пользователя"""
        # 1. Вход в систему
        login_data = {
            "username": "testuser",
            "password": "testpass123"
        }
        
        with patch("httpx.AsyncClient.post") as mock_post:
            # Мокаем успешный вход
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "access_token": "initial_access_token",
                "refresh_token": "initial_refresh_token",
                "user": {
                    "username": "testuser",
                    "groups": ["EISGS_Users"]
                }
            }
            mock_post.return_value = mock_response
            
            login_response = await async_client.post("/api/v1/auth/login", json=login_data)
            assert login_response.status_code == 200
            
            access_token = login_response.json()["access_token"]
            refresh_token = login_response.json()["refresh_token"]
            headers = {"Authorization": f"Bearer {access_token}"}
        
        # 2. Проверка токена
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "valid": True,
                "user": {
                    "username": "testuser",
                    "groups": ["EISGS_Users"]
                }
            }
            mock_get.return_value = mock_response
            
            check_response = await async_client.get(
                "/api/v1/auth/check_token",
                headers=headers
            )
            assert check_response.status_code == 200
        
        # 3. Получение данных пользователя
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "guid": "{test-guid-123}",
                "username": "testuser"
            }
            mock_get.return_value = mock_response
            
            user_data_response = await async_client.get(
                "/api/v1/auth/get_data",
                headers=headers
            )
            assert user_data_response.status_code == 200
        
        # 4. Получение групп пользователя
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = ["EISGS_Users"]
            mock_get.return_value = mock_response
            
            groups_response = await async_client.get(
                "/api/v1/auth/domain/user/groups",
                headers=headers
            )
            assert groups_response.status_code == 200

    @pytest.mark.asyncio
    async def test_token_refresh_workflow_integration(self, async_client):
        """Тест полного цикла обновления токена"""
        # 1. Проверяем истекший токен
        expired_token = "expired_access_token"
        headers = {"Authorization": f"Bearer {expired_token}"}
        
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.json.return_value = {
                "valid": False,
                "expired": True
            }
            mock_get.return_value = mock_response
            
            check_response = await async_client.get(
                "/api/v1/auth/check_token",
                headers=headers
            )
            assert check_response.status_code == 401
        
        # 2. Обновляем токен
        refresh_token = "valid_refresh_token"
        refresh_headers = {"Authorization": f"Bearer {refresh_token}"}
        
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": 200,
                "token": "new_access_token"
            }
            mock_post.return_value = mock_response
            
            refresh_response = await async_client.post(
                "/api/v1/auth/refresh_token",
                headers=refresh_headers
            )
            assert refresh_response.status_code == 200
            
            new_token = refresh_response.json()["token"]
            new_headers = {"Authorization": f"Bearer {new_token}"}
        
        # 3. Проверяем новый токен
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "valid": True,
                "user": {
                    "username": "testuser",
                    "groups": ["EISGS_Users"]
                }
            }
            mock_get.return_value = mock_response
            
            new_check_response = await async_client.get(
                "/api/v1/auth/check_token",
                headers=new_headers
            )
            assert new_check_response.status_code == 200


class TestSecurityValidation:
    """Тесты безопасности и валидации"""

    @pytest.fixture
    def async_client(self):
        """Асинхронный тестовый клиент"""
        transport = ASGITransport(app=app)
        return AsyncClient(transport=transport, base_url="http://test")

    @pytest.mark.asyncio
    async def test_malformed_token_handling(self, async_client):
        """Тест обработки некорректно сформированного токена"""
        # Arrange
        malformed_headers = {"Authorization": "InvalidTokenFormat"}
        
        # Act
        response = await async_client.get(
            "/api/v1/auth/check_token",
            headers=malformed_headers
        )
        
        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_empty_token_handling(self, async_client):
        """Тест обработки пустого токена"""
        # Arrange
        empty_headers = {"Authorization": "Bearer "}
        
        # Act
        response = await async_client.get(
            "/api/v1/auth/check_token",
            headers=empty_headers
        )
        
        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_missing_authorization_header(self, async_client):
        """Тест обработки отсутствующего заголовка авторизации"""
        # Act
        response = await async_client.get("/api/v1/auth/check_token")
        
        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_token_injection_prevention(self, async_client):
        """Тест предотвращения инъекции токена"""
        # Arrange
        malicious_headers = {"Authorization": "Bearer '; DROP TABLE users; --"}
        
        # Act
        response = await async_client.get(
            "/api/v1/auth/check_token",
            headers=malicious_headers
        )
        
        # Assert
        # Должен вернуть 401, а не 500 (ошибка сервера)
        assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
