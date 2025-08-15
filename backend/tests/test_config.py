"""
Тесты для конфигурации приложения
"""

import pytest
import os
from unittest.mock import patch
from pydantic import ValidationError

from config import Settings


class TestSettings:
    """Тесты для класса Settings"""

    @pytest.fixture
    def clean_env(self):
        """Очистка переменных окружения для тестов"""
        # Сохраняем оригинальные значения
        original_env = {}
        for key in [
            "LOG_LEVEL", "LOG_FILE", "POSTGRES_USER", "POSTGRES_PASSWORD",
            "POSTGRES_HOST", "POSTGRES_PORT", "POSTGRES_DB", "API_HOST",
            "API_PORT", "CORS_ORIGINS", "REDIS_HOST", "REDIS_PORT"
        ]:
            if key in os.environ:
                original_env[key] = os.environ[key]
                del os.environ[key]
        
        yield
        
        # Восстанавливаем оригинальные значения
        for key, value in original_env.items():
            os.environ[key] = value

    class TestDefaultValues:
        """Тесты значений по умолчанию"""

        def test_default_log_settings(self, clean_env):
            """Проверка настроек логирования по умолчанию"""
            # Act
            settings = Settings()

            # Assert
            assert settings.log_level == "INFO"
            assert settings.log_file == "logs/dictionaryAPI.log"
            assert "asctime" in settings.log_format
            assert "Y-m-d" in settings.log_date

        def test_default_database_settings(self, clean_env):
            """Проверка настроек базы данных по умолчанию"""
            # Act
            settings = Settings()

            # Assert
            assert settings.postgres_user == "postgres"
            assert settings.postgres_password == "postgres"
            assert settings.postgres_host == "localhost"
            assert settings.postgres_port == "5432"
            assert settings.postgres_schema == "nsi"
            assert settings.postgres_db == "nsi_database"

        def test_default_api_settings(self, clean_env):
            """Проверка настроек API по умолчанию"""
            # Act
            settings = Settings()

            # Assert
            assert settings.api_title == "Сервис доступа к справочникам ЕИСГС"
            assert settings.api_version == "2.0.0"
            assert settings.api_host == "0.0.0.0"
            assert settings.api_port == 9092

        def test_default_cors_settings(self, clean_env):
            """Проверка настроек CORS по умолчанию"""
            # Act
            settings = Settings()

            # Assert
            assert "localhost:3000" in settings.cors_origins
            assert "localhost:8080" in settings.cors_origins
            assert settings.cors_allow_credentials is True
            assert "GET" in settings.cors_allow_methods
            assert "POST" in settings.cors_allow_methods
            assert settings.cors_allow_headers == "*"

        def test_default_redis_settings(self, clean_env):
            """Проверка настроек Redis по умолчанию"""
            # Act
            settings = Settings()

            # Assert
            assert settings.redis_host == "localhost"
            assert settings.redis_port == 6379
            assert settings.redis_db == 0
            assert settings.redis_password == ""
            assert settings.redis_use_cache is True
            assert settings.redis_cache_ttl == 3600

    class TestEnvironmentVariables:
        """Тесты переменных окружения"""

        def test_log_level_from_env(self, clean_env):
            """Установка уровня логирования из переменной окружения"""
            # Arrange
            os.environ["LOG_LEVEL"] = "DEBUG"

            # Act
            settings = Settings()

            # Assert
            assert settings.log_level == "DEBUG"

        def test_database_settings_from_env(self, clean_env):
            """Установка настроек БД из переменных окружения"""
            # Arrange
            os.environ["POSTGRES_USER"] = "test_user"
            os.environ["POSTGRES_PASSWORD"] = "test_password"
            os.environ["POSTGRES_HOST"] = "test_host"
            os.environ["POSTGRES_PORT"] = "5433"
            os.environ["POSTGRES_DB"] = "test_db"

            # Act
            settings = Settings()

            # Assert
            assert settings.postgres_user == "test_user"
            assert settings.postgres_password == "test_password"
            assert settings.postgres_host == "test_host"
            assert settings.postgres_port == "5433"
            assert settings.postgres_db == "test_db"

        def test_api_settings_from_env(self, clean_env):
            """Установка настроек API из переменных окружения"""
            # Arrange
            os.environ["API_HOST"] = "127.0.0.1"
            os.environ["API_PORT"] = "8000"

            # Act
            settings = Settings()

            # Assert
            assert settings.api_host == "127.0.0.1"
            assert settings.api_port == 8000

        def test_cors_settings_from_env(self, clean_env):
            """Установка настроек CORS из переменных окружения"""
            # Arrange
            os.environ["CORS_ORIGINS"] = "https://example.com,https://test.com"
            os.environ["CORS_ALLOW_METHODS"] = "GET,POST"
            os.environ["CORS_ALLOW_HEADERS"] = "Content-Type,Authorization"

            # Act
            settings = Settings()

            # Assert
            assert "https://example.com" in settings.cors_origins
            assert "https://test.com" in settings.cors_origins
            assert "GET" in settings.cors_allow_methods
            assert "POST" in settings.cors_allow_methods
            assert "Content-Type" in settings.cors_allow_headers
            assert "Authorization" in settings.cors_allow_headers

        def test_redis_settings_from_env(self, clean_env):
            """Установка настроек Redis из переменных окружения"""
            # Arrange
            os.environ["REDIS_HOST"] = "redis.example.com"
            os.environ["REDIS_PORT"] = "6380"
            os.environ["REDIS_DB"] = "1"
            os.environ["REDIS_PASSWORD"] = "redis_password"
            os.environ["REDIS_USE_CACHE"] = "false"
            os.environ["REDIS_CACHE_TTL"] = "1800"

            # Act
            settings = Settings()

            # Assert
            assert settings.redis_host == "redis.example.com"
            assert settings.redis_port == 6380
            assert settings.redis_db == 1
            assert settings.redis_password == "redis_password"
            assert settings.redis_use_cache is False
            assert settings.redis_cache_ttl == 1800

    class TestValidation:
        """Тесты валидации"""

        def test_invalid_log_level(self, clean_env):
            """Некорректный уровень логирования"""
            # Arrange
            os.environ["LOG_LEVEL"] = "INVALID_LEVEL"

            # Act & Assert
            with pytest.raises(ValidationError, match="log_level должен быть одним из"):
                Settings()

        def test_invalid_postgres_port(self, clean_env):
            """Некорректный порт PostgreSQL"""
            # Arrange
            os.environ["POSTGRES_PORT"] = "99999"

            # Act & Assert
            with pytest.raises(ValidationError, match="Порт должен быть в диапазоне"):
                Settings()

        def test_invalid_postgres_port_string(self, clean_env):
            """Некорректный порт PostgreSQL (строка)"""
            # Arrange
            os.environ["POSTGRES_PORT"] = "invalid_port"

            # Act & Assert
            with pytest.raises(ValidationError, match="Некорректный порт"):
                Settings()

        def test_invalid_redis_port(self, clean_env):
            """Некорректный порт Redis"""
            # Arrange
            os.environ["REDIS_PORT"] = "99999"

            # Act & Assert
            with pytest.raises(ValidationError):
                Settings()

        def test_invalid_redis_db(self, clean_env):
            """Некорректная база данных Redis"""
            # Arrange
            os.environ["REDIS_DB"] = "invalid_db"

            # Act & Assert
            with pytest.raises(ValidationError):
                Settings()

        def test_invalid_api_port(self, clean_env):
            """Некорректный порт API"""
            # Arrange
            os.environ["API_PORT"] = "99999"

            # Act & Assert
            with pytest.raises(ValidationError):
                Settings()

    class TestStringParsing:
        """Тесты парсинга строковых значений"""

        def test_cors_origins_parsing(self, clean_env):
            """Парсинг CORS origins"""
            # Arrange
            os.environ["CORS_ORIGINS"] = "  https://example.com , https://test.com  "

            # Act
            settings = Settings()

            # Assert
            origins = [origin.strip() for origin in settings.cors_origins.split(",")]
            assert "https://example.com" in origins
            assert "https://test.com" in origins

        def test_cors_methods_parsing(self, clean_env):
            """Парсинг CORS методов"""
            # Arrange
            os.environ["CORS_ALLOW_METHODS"] = "  GET , POST , PUT  "

            # Act
            settings = Settings()

            # Assert
            methods = [method.strip() for method in settings.cors_allow_methods.split(",")]
            assert "GET" in methods
            assert "POST" in methods
            assert "PUT" in methods

        def test_cors_headers_parsing(self, clean_env):
            """Парсинг CORS заголовков"""
            # Arrange
            os.environ["CORS_ALLOW_HEADERS"] = "  Content-Type , Authorization  "

            # Act
            settings = Settings()

            # Assert
            headers = [header.strip() for header in settings.cors_allow_headers.split(",")]
            assert "Content-Type" in headers
            assert "Authorization" in headers

    class TestBooleanParsing:
        """Тесты парсинга булевых значений"""

        def test_cors_credentials_true(self, clean_env):
            """CORS credentials = true"""
            # Arrange
            os.environ["CORS_ALLOW_CREDENTIALS"] = "true"

            # Act
            settings = Settings()

            # Assert
            assert settings.cors_allow_credentials is True

        def test_cors_credentials_false(self, clean_env):
            """CORS credentials = false"""
            # Arrange
            os.environ["CORS_ALLOW_CREDENTIALS"] = "false"

            # Act
            settings = Settings()

            # Assert
            assert settings.cors_allow_credentials is False

        def test_redis_use_cache_true(self, clean_env):
            """Redis use cache = true"""
            # Arrange
            os.environ["REDIS_USE_CACHE"] = "true"

            # Act
            settings = Settings()

            # Assert
            assert settings.redis_use_cache is True

        def test_redis_use_cache_false(self, clean_env):
            """Redis use cache = false"""
            # Arrange
            os.environ["REDIS_USE_CACHE"] = "false"

            # Act
            settings = Settings()

            # Assert
            assert settings.redis_use_cache is False

    class TestConfigFile:
        """Тесты файла конфигурации"""

        @pytest.fixture
        def temp_env_file(self, tmp_path):
            """Временный .env файл"""
            env_file = tmp_path / ".env"
            env_file.write_text("""
LOG_LEVEL=DEBUG
POSTGRES_USER=env_user
POSTGRES_PASSWORD=env_password
API_PORT=8000
CORS_ORIGINS=https://env.example.com
REDIS_HOST=env.redis.com
            """)
            return env_file

        def test_env_file_loading(self, clean_env, temp_env_file):
            """Загрузка настроек из .env файла"""
            # Arrange
            with patch("config.Settings.Config.env_file", str(temp_env_file)):
                # Act
                settings = Settings()

                # Assert
                assert settings.log_level == "DEBUG"
                assert settings.postgres_user == "env_user"
                assert settings.postgres_password == "env_password"
                assert settings.api_port == 8000
                assert "https://env.example.com" in settings.cors_origins
                assert settings.redis_host == "env.redis.com"

        def test_env_file_priority(self, clean_env, temp_env_file):
            """Приоритет переменных окружения над .env файлом"""
            # Arrange
            os.environ["LOG_LEVEL"] = "ERROR"
            os.environ["POSTGRES_USER"] = "env_var_user"

            with patch("config.Settings.Config.env_file", str(temp_env_file)):
                # Act
                settings = Settings()

                # Assert
                assert settings.log_level == "ERROR"  # Из переменной окружения
                assert settings.postgres_user == "env_var_user"  # Из переменной окружения
                assert settings.postgres_password == "env_password"  # Из .env файла

    class TestDatabaseUrl:
        """Тесты формирования URL базы данных"""

        def test_database_url_format(self, clean_env):
            """Формат URL базы данных"""
            # Arrange
            settings = Settings()

            # Act
            # Проверяем, что настройки содержат все необходимые поля для формирования URL
            assert hasattr(settings, 'postgres_user')
            assert hasattr(settings, 'postgres_password')
            assert hasattr(settings, 'postgres_host')
            assert hasattr(settings, 'postgres_port')
            assert hasattr(settings, 'postgres_db')

        def test_database_url_with_custom_settings(self, clean_env):
            """URL БД с пользовательскими настройками"""
            # Arrange
            os.environ["POSTGRES_USER"] = "custom_user"
            os.environ["POSTGRES_PASSWORD"] = "custom_pass"
            os.environ["POSTGRES_HOST"] = "custom.host.com"
            os.environ["POSTGRES_PORT"] = "5433"
            os.environ["POSTGRES_DB"] = "custom_db"

            # Act
            settings = Settings()

            # Assert
            assert settings.postgres_user == "custom_user"
            assert settings.postgres_password == "custom_pass"
            assert settings.postgres_host == "custom.host.com"
            assert settings.postgres_port == "5433"
            assert settings.postgres_db == "custom_db"

    class TestRedisUrl:
        """Тесты формирования URL Redis"""

        def test_redis_url_format(self, clean_env):
            """Формат URL Redis"""
            # Arrange
            settings = Settings()

            # Act
            # Проверяем, что настройки содержат все необходимые поля для формирования URL
            assert hasattr(settings, 'redis_host')
            assert hasattr(settings, 'redis_port')
            assert hasattr(settings, 'redis_db')
            assert hasattr(settings, 'redis_password')

        def test_redis_url_with_custom_settings(self, clean_env):
            """URL Redis с пользовательскими настройками"""
            # Arrange
            os.environ["REDIS_HOST"] = "custom.redis.com"
            os.environ["REDIS_PORT"] = "6380"
            os.environ["REDIS_DB"] = "2"
            os.environ["REDIS_PASSWORD"] = "custom_redis_pass"

            # Act
            settings = Settings()

            # Assert
            assert settings.redis_host == "custom.redis.com"
            assert settings.redis_port == 6380
            assert settings.redis_db == 2
            assert settings.redis_password == "custom_redis_pass"


class TestSettingsIntegration:
    """Интеграционные тесты настроек"""

    def test_settings_singleton_behavior(self):
        """Поведение настроек как синглтона"""
        # Act
        settings1 = Settings()
        settings2 = Settings()

        # Assert
        assert settings1 is not settings2  # Каждый вызов создает новый экземпляр
        assert settings1.log_level == settings2.log_level  # Но значения одинаковые

    def test_settings_immutability(self):
        """Неизменяемость настроек после создания"""
        # Arrange
        settings = Settings()
        original_log_level = settings.log_level

        # Act & Assert
        # Попытка изменить значение должна вызвать ошибку
        with pytest.raises(TypeError):
            settings.log_level = "DEBUG"

        # Значение должно остаться неизменным
        assert settings.log_level == original_log_level

    def test_settings_serialization(self):
        """Сериализация настроек"""
        # Arrange
        settings = Settings()

        # Act
        settings_dict = settings.dict()

        # Assert
        assert isinstance(settings_dict, dict)
        assert "log_level" in settings_dict
        assert "postgres_user" in settings_dict
        assert "api_host" in settings_dict
        assert "cors_origins" in settings_dict
        assert "redis_host" in settings_dict

    def test_settings_json_serialization(self):
        """JSON сериализация настроек"""
        # Arrange
        settings = Settings()

        # Act
        settings_json = settings.json()

        # Assert
        assert isinstance(settings_json, str)
        assert "log_level" in settings_json
        assert "postgres_user" in settings_json
