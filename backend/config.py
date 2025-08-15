"""
Конфигурация приложения с использованием pydantic-settings
"""

from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import List
import os


class Settings(BaseSettings):
    # Логирование
    log_level: str = Field(default="INFO", description="Уровень логирования")
    log_file: str = Field(default="logs/dictionaryAPI.log", description="Файл логов")
    log_format: str = Field(
        default="%(asctime)s %(name)-30s %(levelname)-8s %(module)s:%(funcName)s:%(lineno)d %(message)s",
        description="Формат логов"
    )
    log_date: str = Field(default="%Y-%m-%d %H:%M:%S", description="Формат даты в логах")

    # База данных
    postgres_user: str = Field(default="postgres", description="Пользователь PostgreSQL")
    postgres_password: str = Field(default="postgres", description="Пароль PostgreSQL")
    postgres_host: str = Field(default="localhost", description="Хост PostgreSQL")
    postgres_port: str = Field(default="5432", description="Порт PostgreSQL")
    postgres_schema: str = Field(default="nsi", description="Схема PostgreSQL")
    postgres_db: str = Field(default="nsi_database", description="Имя базы данных PostgreSQL")

    # CORS настройки
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:8080",
        description="Разрешенные origins для CORS (разделенные запятыми)"
    )
    cors_allow_credentials: bool = Field(default=True, description="Разрешить credentials в CORS")
    cors_allow_methods: str = Field(
        default="GET,POST,PUT,DELETE,OPTIONS",
        description="Разрешенные HTTP методы (разделенные запятыми)"
    )
    cors_allow_headers: str = Field(
        default="*",
        description="Разрешенные HTTP заголовки (разделенные запятыми)"
    )

    # API настройки
    api_title: str = Field(default="Сервис доступа к справочникам ЕИСГС", description="Название API")
    api_version: str = Field(default="2.0.0", description="Версия API")
    api_host: str = Field(default="0.0.0.0", description="Хост для запуска API")
    api_port: int = Field(default=9092, description="Порт для запуска API")

    # Redis настройки
    redis_host: str = Field(default="localhost", description="Хост Redis")
    redis_port: int = Field(default=6379, description="Порт Redis")
    redis_db: int = Field(default=0, description="База данных Redis")
    redis_password: str = Field(default="", description="Пароль Redis")
    redis_use_cache: bool = Field(default=True, description="Использовать кэширование")
    redis_cache_ttl: int = Field(default=3600, description="Время жизни кэша в секундах")

    # Active Directory настройки
    ldap_server: str = Field(default="ldap://localhost:389", description="LDAP сервер")
    ldap_domain: str = Field(default="example.com", description="Домен Active Directory")
    ldap_base_dn: str = Field(default="DC=example,DC=com", description="Базовый DN")
    ldap_bind_dn: str = Field(default="", description="DN для привязки к LDAP")
    ldap_bind_password: str = Field(default="", description="Пароль для привязки к LDAP")
    ldap_user_search_base: str = Field(default="OU=Users,DC=example,DC=com", description="Базовый DN для поиска пользователей")
    ldap_group_search_base: str = Field(default="OU=Groups,DC=example,DC=com", description="Базовый DN для поиска групп")
    ldap_required_group: str = Field(default="EISGS_Users", description="Обязательная группа для доступа")
    ldap_use_ssl: bool = Field(default=False, description="Использовать SSL для LDAP")
    ldap_use_tls: bool = Field(default=True, description="Использовать TLS для LDAP")
    ldap_timeout: int = Field(default=10, description="Таймаут LDAP соединения в секундах")

    # JWT настройки
    jwt_secret_key: str = Field(default="your-secret-key-change-in-production", description="Секретный ключ для JWT")
    jwt_algorithm: str = Field(default="HS256", description="Алгоритм JWT")
    jwt_access_token_expire_minutes: int = Field(default=30, description="Время жизни access token в минутах")
    jwt_refresh_token_expire_days: int = Field(default=7, description="Время жизни refresh token в днях")

    @validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"log_level должен быть одним из: {valid_levels}")
        return v.upper()

    @validator("postgres_port")
    @classmethod
    def validate_postgres_port(cls, v):
        try:
            port = int(v)
            if not (1 <= port <= 65535):
                raise ValueError("Порт должен быть в диапазоне 1-65535")
            return str(port)
        except ValueError as e:
            raise ValueError(f"Некорректный порт: {e}")

    @validator("ldap_timeout")
    @classmethod
    def validate_ldap_timeout(cls, v):
        if v < 1 or v > 60:
            raise ValueError("LDAP таймаут должен быть в диапазоне 1-60 секунд")
        return v

    @validator("jwt_access_token_expire_minutes")
    @classmethod
    def validate_jwt_access_token_expire(cls, v):
        if v < 1 or v > 1440:  # 24 часа
            raise ValueError("Время жизни access token должно быть в диапазоне 1-1440 минут")
        return v

    @validator("jwt_refresh_token_expire_days")
    @classmethod
    def validate_jwt_refresh_token_expire(cls, v):
        if v < 1 or v > 365:
            raise ValueError("Время жизни refresh token должно быть в диапазоне 1-365 дней")
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Создаем экземпляр настроек
settings = Settings()

# Создаем директорию для логов если её нет
os.makedirs(os.path.dirname(settings.log_file), exist_ok=True)
