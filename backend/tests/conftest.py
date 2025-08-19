"""
Конфигурация pytest с общими фикстурами
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import date, datetime, timedelta
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from main import app


@pytest.fixture(scope="session")
def event_loop():
    """Создание event loop для асинхронных тестов"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client():
    """Синхронный тестовый клиент FastAPI"""
    return TestClient(app)


@pytest.fixture
def async_client():
    """Асинхронный тестовый клиент"""
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.fixture
def valid_user_data():
    """Валидные данные пользователя для тестов"""
    return {
        "username": "testuser",
        "password": "testpass123"
    }


@pytest.fixture
def admin_user_data():
    """Данные администратора для тестов"""
    return {
        "username": "admin",
        "password": "adminpass123"
    }


@pytest.fixture
def valid_token_headers():
    """Заголовки с валидным токеном"""
    return {"Authorization": "Bearer valid_access_token"}


@pytest.fixture
def security_admin_headers():
    """Заголовки администратора безопасности"""
    return {"Authorization": "Bearer security_admin_token"}


@pytest.fixture
def system_admin_headers():
    """Заголовки администратора системы"""
    return {"Authorization": "Bearer system_admin_token"}


@pytest.fixture
def dictionary_owner_headers():
    """Заголовки владельца справочника"""
    return {"Authorization": "Bearer owner_token"}


@pytest.fixture
def regular_user_headers():
    """Заголовки обычного пользователя"""
    return {"Authorization": "Bearer user_token"}


@pytest.fixture
def sample_dictionary_data():
    """Тестовые данные для справочника"""
    return {
        "name": "Тестовый справочник",
        "code": "TEST_DICT_001",
        "description": "Описание тестового справочника",
        "start_date": "2025-01-01",
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


@pytest.fixture
def minimal_dictionary_data():
    """Минимальные данные для справочника"""
    return {
        "name": "Минимальный справочник",
        "code": "MIN_DICT",
        "description": "Минимальное описание",
        "start_date": "2025-01-01",
        "finish_date": "9999-12-31",
        "id_type": 0
    }


@pytest.fixture
def mock_external_auth_success():
    """Мок успешной авторизации через внешний API"""
    return {
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
    }


@pytest.fixture
def mock_external_auth_admin():
    """Мок авторизации администратора через внешний API"""
    return {
        "access_token": "admin_access_token",
        "refresh_token": "admin_refresh_token",
        "user": {
            "username": "admin",
            "display_name": "Admin User",
            "email": "admin@example.com",
            "groups": ["EISGS_Users", "EISGS_AppSecurity"],
            "department": "Security",
            "title": "Security Administrator",
            "employee_id": "EMP002"
        }
    }


@pytest.fixture
def mock_external_auth_security_admin():
    """Мок авторизации администратора безопасности через внешний API"""
    return {
        "access_token": "security_admin_token",
        "refresh_token": "security_admin_refresh_token",
        "user": {
            "username": "security_admin",
            "display_name": "Security Admin",
            "email": "security@example.com",
            "groups": ["EISGS_AppSecurity"],
            "department": "Security",
            "title": "Security Administrator",
            "employee_id": "EMP003"
        }
    }


@pytest.fixture
def mock_user_groups_eisgs_users():
    """Мок групп пользователя EISGS_Users"""
    return ["EISGS_Users"]


@pytest.fixture
def mock_user_groups_eisgs_appsecurity():
    """Мок групп пользователя EISGS_AppSecurity"""
    return ["EISGS_AppSecurity"]


@pytest.fixture
def mock_user_groups_both():
    """Мок групп пользователя с обеими ролями"""
    return ["EISGS_Users", "EISGS_AppSecurity"]


@pytest.fixture
def mock_user_groups_other():
    """Мок групп пользователя без требуемых ролей"""
    return ["Other_Group", "Another_Group"]


@pytest.fixture
def mock_user_data():
    """Мок данных пользователя"""
    return {
        "guid": "{8c527f4d-c073-453c-b8b5-082e040b4d19}",
        "username": "Админ СП_БД"
    }


@pytest.fixture
def mock_domain_users():
    """Мок пользователей домена"""
    return [
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


@pytest.fixture
def mock_audit_logs():
    """Мок записей аудита"""
    return [
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


@pytest.fixture
def mock_dictionary_service():
    """Мок сервиса справочников"""
    with patch("routers.dictionary.DictionaryService") as mock_service:
        # Настраиваем методы сервиса
        mock_service.create_dictionary.return_value = 123
        mock_service.update_dictionary.return_value = True
        mock_service.delete_dictionary.return_value = True
        mock_service.get_all_dictionaries.return_value = []
        mock_service.get_dictionary.return_value = None
        yield mock_service


@pytest.fixture
def mock_audit_service():
    """Мок сервиса аудита"""
    with patch("routers.audit.AuditService") as mock_service:
        # Настраиваем методы сервиса
        mock_service.log_action.return_value = True
        mock_service.get_audit_logs.return_value = []
        yield mock_service


@pytest.fixture
def mock_database():
    """Мок базы данных"""
    with patch("database.get_database") as mock_db:
        # Настраиваем методы базы данных
        mock_db.fetch_one.return_value = {"total": 0}
        mock_db.fetch_all.return_value = []
        yield mock_db


# Маркеры для категоризации тестов
def pytest_configure(config):
    """Настройка маркеров pytest"""
    config.addinivalue_line(
        "markers", "auth: тесты авторизации и аутентификации"
    )
    config.addinivalue_line(
        "markers", "users: тесты управления пользователями"
    )
    config.addinivalue_line(
        "markers", "dictionaries: тесты справочников"
    )
    config.addinivalue_line(
        "markers", "roles: тесты ролевой модели"
    )
    config.addinivalue_line(
        "markers", "audit: тесты аудита и логирования"
    )
    config.addinivalue_line(
        "markers", "integration: интеграционные тесты"
    )
    config.addinivalue_line(
        "markers", "performance: тесты производительности"
    )
    config.addinivalue_line(
        "markers", "security: тесты безопасности"
    )


# Глобальные настройки для тестов
@pytest.fixture(autouse=True)
def setup_test_environment():
    """Автоматическая настройка тестовой среды"""
    # Здесь можно добавить общую настройку для всех тестов
    pass


@pytest.fixture(autouse=True)
def cleanup_test_environment():
    """Автоматическая очистка тестовой среды"""
    yield
    # Здесь можно добавить общую очистку для всех тестов
    pass
