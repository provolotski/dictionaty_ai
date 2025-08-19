# Тестирование проекта Dictionary AI

## Обзор

Проект содержит комплексные тесты для всех основных компонентов:

- **Backend (FastAPI)**: Тесты API, сервисов, моделей и интеграции
- **Frontend (Django)**: Тесты views, API прокси и пользовательского интерфейса
- **Интеграционные тесты**: Тесты полных рабочих процессов

## Структура тестов

### Backend тесты (`backend/tests/`)

- `test_auth_and_users.py` - Тесты авторизации и управления пользователями
- `test_dictionary_router.py` - Тесты API роутеров справочников
- `test_dictionary_service.py` - Тесты сервисного слоя
- `test_integration.py` - Интеграционные тесты
- `test_middleware.py` - Тесты middleware
- `test_schemas.py` - Тесты Pydantic схем
- `test_utils.py` - Тесты утилит
- `test_config.py` - Тесты конфигурации
- `test_cache_manager.py` - Тесты кэширования
- `test_model_attribute.py` - Тесты модели атрибутов
- `test_performance.py` - Тесты производительности
- `test_exceptions.py` - Тесты обработки исключений

### Frontend тесты (`frontend/tests/`)

- `test_api_views.py` - Тесты Django API views
- `test_views.py` - Тесты Django views (accounts, home)

## Установка зависимостей для тестирования

### Backend

```bash
cd backend
source venv/bin/activate
pip install pytest pytest-asyncio pytest-cov httpx
```

### Frontend

```bash
cd frontend
source venv/bin/activate
pip install pytest pytest-django pytest-cov
```

## Запуск тестов

### Все тесты

```bash
# Из корневой директории проекта
pytest

# С подробным выводом
pytest -v

# С покрытием кода
pytest --cov=. --cov-report=html
```

### Тесты по категориям

```bash
# Только backend тесты
pytest backend/tests/

# Только frontend тесты
pytest frontend/tests/

# Только тесты авторизации
pytest -m auth

# Только тесты справочников
pytest -m dictionaries

# Только интеграционные тесты
pytest -m integration

# Только unit тесты
pytest -m unit
```

### Тесты по файлам

```bash
# Тесты авторизации и пользователей
pytest backend/tests/test_auth_and_users.py

# Тесты API views
pytest frontend/tests/test_api_views.py

# Тесты Django views
pytest frontend/tests/test_views.py
```

### Тесты с фильтрацией

```bash
# Исключить медленные тесты
pytest -m "not slow"

# Только тесты API
pytest -m api

# Только тесты views
pytest -m views
```

## Конфигурация pytest

Файл `pytest.ini` содержит настройки:

- **DJANGO_SETTINGS_MODULE**: Настройки Django для frontend тестов
- **testpaths**: Пути к тестам
- **markers**: Маркеры для категоризации тестов
- **addopts**: Дополнительные опции (покрытие, миграции, etc.)

## Маркеры тестов

- `@pytest.mark.auth` - Тесты авторизации
- `@pytest.mark.users` - Тесты управления пользователями
- `@pytest.mark.dictionaries` - Тесты справочников
- `@pytest.mark.api` - Тесты API
- `@pytest.mark.views` - Тесты Django views
- `@pytest.mark.backend` - Backend тесты
- `@pytest.mark.frontend` - Frontend тесты
- `@pytest.mark.integration` - Интеграционные тесты
- `@pytest.mark.unit` - Unit тесты
- `@pytest.mark.slow` - Медленные тесты

## Покрытие кода

Тесты настроены для измерения покрытия кода:

```bash
# Запуск с покрытием
pytest --cov=. --cov-report=html --cov-report=term-missing

# Покрытие только backend
pytest --cov=backend --cov-report=html

# Покрытие только frontend
pytest --cov=frontend --cov-report=html
```

Отчеты покрытия сохраняются в `htmlcov/` директории.

## Моки и фикстуры

Тесты используют:

- **unittest.mock**: Для мокирования внешних API и сервисов
- **pytest.fixture**: Для настройки тестового окружения
- **AsyncMock**: Для асинхронных функций
- **MagicMock**: Для сложных объектов

## Примеры тестов

### Тест авторизации

```python
@pytest.mark.asyncio
async def test_login_success(self, async_client):
    """Тест успешного входа в систему"""
    login_data = {
        "username": "testuser",
        "password": "testpass123"
    }
    
    with patch("routers.users.external_auth_api") as mock_auth:
        mock_auth.return_value = {
            "access_token": "test_access_token",
            "user": {"username": "testuser", "groups": ["EISGS_Users"]}
        }
        
        response = await async_client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
```

### Тест создания справочника

```python
@pytest.mark.asyncio
async def test_create_dictionary_success(self, async_client, sample_dictionary_data):
    """Тест успешного создания справочника"""
    headers = {"Authorization": "Bearer valid_token"}
    
    with patch("routers.dictionary.DictionaryService.create_dictionary") as mock_service:
        mock_service.return_value = 123
        
        response = await async_client.post(
            "/api/v2/models/newDictionary", 
            json=sample_dictionary_data,
            headers=headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == 123
```

## Интеграционные тесты

Тесты проверяют полные рабочие процессы:

1. **Авторизация пользователя**
2. **Получение списка справочников**
3. **Создание нового справочника**
4. **Проверка прав доступа**

## Тестирование ошибок

Тесты покрывают различные сценарии ошибок:

- Неверные учетные данные
- Отсутствующие обязательные поля
- Ошибки валидации
- Ошибки backend API
- Проблемы с правами доступа

## Запуск в CI/CD

Для интеграции в CI/CD pipeline:

```yaml
# GitHub Actions пример
- name: Run Backend Tests
  run: |
    cd backend
    source venv/bin/activate
    pytest --cov=. --cov-report=xml

- name: Run Frontend Tests
  run: |
    cd frontend
    source venv/bin/activate
    pytest --cov=. --cov-report=xml
```

## Отладка тестов

### Подробный вывод

```bash
pytest -v -s --tb=long
```

### Остановка на первой ошибке

```bash
pytest -x
```

### Запуск конкретного теста

```bash
pytest test_auth_and_users.py::TestAuthentication::test_login_success
```

### Параллельное выполнение

```bash
pytest -n auto
```

## Требования к покрытию

Проект настроен на минимальное покрытие 80%:

```bash
pytest --cov-fail-under=80
```

## Поддержка и обновление

При добавлении новых функций:

1. Создайте соответствующие тесты
2. Добавьте маркеры для категоризации
3. Обновите документацию
4. Проверьте покрытие кода

## Полезные команды

```bash
# Показать все доступные маркеры
pytest --markers

# Показать тесты без их запуска
pytest --collect-only

# Запуск тестов с определенным паттерном
pytest -k "login"

# Запуск тестов с временными метками
pytest --durations=10
```
