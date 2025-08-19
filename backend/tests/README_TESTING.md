# Руководство по тестированию системы справочников

## Обзор

Этот документ описывает структуру тестов для системы управления справочниками, включая тесты авторизации, пользователей, справочников и ролевой модели доступа.

## Структура тестов

### Основные файлы тестов

1. **`test_auth_comprehensive.py`** - Комплексные тесты авторизации и аутентификации
2. **`test_external_auth_integration.py`** - Тесты интеграции с внешними API авторизации
3. **`test_role_based_access.py`** - Тесты ролевой модели доступа
4. **`test_audit_and_logging.py`** - Тесты аудита и логирования
5. **`conftest.py`** - Общие фикстуры и конфигурация pytest

### Существующие тесты

- **`test_auth_and_users.py`** - Базовые тесты авторизации и пользователей
- **`test_dictionary_service.py`** - Тесты сервиса справочников
- **`test_dictionary_router.py`** - Тесты роутера справочников
- **`test_middleware.py`** - Тесты middleware
- **`test_integration.py`** - Интеграционные тесты

## Установка и настройка

### Предварительные требования

- Python 3.8+
- pytest
- pytest-asyncio
- httpx
- fastapi[testing]

### Установка зависимостей

```bash
cd backend
pip install -r requirements.txt
pip install pytest pytest-asyncio httpx fastapi[testing]
```

## Запуск тестов

### Запуск всех тестов

```bash
cd backend
pytest tests/ -v
```

### Запуск тестов по категориям

```bash
# Тесты авторизации
pytest tests/ -m auth -v

# Тесты пользователей
pytest tests/ -m users -v

# Тесты справочников
pytest tests/ -m dictionaries -v

# Тесты ролевой модели
pytest tests/ -m roles -v

# Тесты аудита
pytest tests/ -m audit -v

# Интеграционные тесты
pytest tests/ -m integration -v

# Тесты производительности
pytest tests/ -m performance -v

# Тесты безопасности
pytest tests/ -m security -v
```

### Запуск конкретного файла тестов

```bash
# Тесты авторизации
pytest tests/test_auth_comprehensive.py -v

# Тесты ролевой модели
pytest tests/test_role_based_access.py -v

# Тесты аудита
pytest tests/test_audit_and_logging.py -v
```

### Запуск конкретного теста

```bash
# Конкретный тест
pytest tests/test_auth_comprehensive.py::TestAuthenticationComprehensive::test_login_with_domain_groups_check -v

# Тесты конкретного класса
pytest tests/test_role_based_access.py::TestSecurityAdministratorRole -v
```

## Структура тестов

### Тесты авторизации (`test_auth_comprehensive.py`)

- **TestAuthenticationComprehensive** - Комплексные тесты авторизации
  - Вход с проверкой групп домена
  - Обработка пользователей без требуемых прав
  - Цикл обновления токенов
  - Аудит попыток входа

- **TestDomainUserManagement** - Управление пользователями домена
  - Получение пользователей домена
  - Фильтрация по группам
  - Получение групп пользователя
  - Получение данных пользователя

- **TestDictionaryComprehensive** - Комплексные тесты справочников
  - Получение списка с пагинацией
  - Фильтрация по типу и статусу
  - Создание с полными и минимальными данными
  - Валидация данных

### Тесты интеграции с внешними API (`test_external_auth_integration.py`)

- **TestExternalAuthAPIIntegration** - Интеграция с внешними API
  - Проверка токенов
  - Обновление токенов
  - Получение данных пользователя
  - Обработка ошибок подключения

- **TestAuthenticationWorkflow** - Полный цикл аутентификации
  - Вход → проверка → получение данных → получение групп
  - Обновление токенов

- **TestSecurityValidation** - Валидация безопасности
  - Обработка некорректных токенов
  - Предотвращение инъекций

### Тесты ролевой модели (`test_role_based_access.py`)

- **TestSecurityAdministratorRole** - Администратор безопасности
  - Доступ к странице аудита
  - Просмотр всех записей аудита
  - Назначение ролей администратора системы
  - Запрет создания справочников

- **TestSystemAdministratorRole** - Администратор системы
  - Создание справочников
  - Назначение владельцев справочников
  - Владение всеми справочниками
  - Запрет доступа к аудиту

- **TestDictionaryOwnerRole** - Владелец справочника
  - Редактирование своих справочников
  - Импорт данных
  - Запрет редактирования чужих справочников
  - Запрет создания новых справочников

- **TestRegularUserRole** - Обычный пользователь
  - Просмотр справочников
  - Экспорт данных
  - Запрет создания и редактирования
  - Запрет доступа к аудиту

### Тесты аудита (`test_audit_and_logging.py`)

- **TestAuditLogging** - Логирование действий
  - Успешные и неудачные попытки входа
  - Создание, обновление, удаление справочников
  - Изменение ролей пользователей

- **TestAuditRetrieval** - Получение записей аудита
  - Базовое получение
  - Фильтрация по параметрам
  - Диапазоны дат
  - Пагинация
  - Проверка прав доступа

- **TestAuditDataIntegrity** - Целостность данных
  - Обязательные поля
  - Формат временных меток
  - Формат IP адресов

- **TestAuditPerformance** - Производительность
  - Время логирования
  - Время получения записей

## Фикстуры и моки

### Общие фикстуры (`conftest.py`)

- **Клиенты**: `client`, `async_client`
- **Данные пользователей**: `valid_user_data`, `admin_user_data`
- **Заголовки**: различные типы токенов для разных ролей
- **Данные справочников**: `sample_dictionary_data`, `minimal_dictionary_data`
- **Моки внешних API**: авторизация, группы, пользователи
- **Моки сервисов**: справочники, аудит, база данных

### Использование фикстур

```python
def test_example(async_client, valid_token_headers, sample_dictionary_data):
    """Пример использования фикстур"""
    response = await async_client.post(
        "/api/v2/models/newDictionary",
        json=sample_dictionary_data,
        headers=valid_token_headers
    )
    assert response.status_code == 201
```

## Маркеры pytest

### Доступные маркеры

- `@pytest.mark.auth` - тесты авторизации
- `@pytest.mark.users` - тесты пользователей
- `@pytest.mark.dictionaries` - тесты справочников
- `@pytest.mark.roles` - тесты ролевой модели
- `@pytest.mark.audit` - тесты аудита
- `@pytest.mark.integration` - интеграционные тесты
- `@pytest.mark.performance` - тесты производительности
- `@pytest.mark.security` - тесты безопасности

### Пример использования маркеров

```python
@pytest.mark.auth
@pytest.mark.security
async def test_secure_login():
    """Тест безопасного входа в систему"""
    pass
```

## Настройка тестовой среды

### Переменные окружения

Создайте файл `.env.test` для тестовой среды:

```env
DATABASE_URL=postgresql://test_user:test_pass@localhost:5432/test_db
EXTERNAL_AUTH_API_URL=http://127.0.0.1:9090/api/v1/auth
LOG_LEVEL=DEBUG
```

### Конфигурация pytest

Файл `pytest.ini` уже настроен с оптимальными параметрами:

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers --disable-warnings --cov=. --cov-report=html:htmlcov --cov-report=term-missing --cov-report=xml --cov-fail-under=80 --asyncio-mode=auto
```

## Покрытие кода

### Запуск с покрытием

```bash
# С HTML отчетом
pytest tests/ --cov=. --cov-report=html

# С консольным отчетом
pytest tests/ --cov=. --cov-report=term-missing

# С XML отчетом для CI/CD
pytest tests/ --cov=. --cov-report=xml
```

### Просмотр отчета о покрытии

После запуска с HTML отчетом откройте `htmlcov/index.html` в браузере.

## Отладка тестов

### Подробный вывод

```bash
pytest tests/ -v -s --tb=long
```

### Остановка на первой ошибке

```bash
pytest tests/ -x
```

### Запуск только падающих тестов

```bash
pytest tests/ --lf
```

### Отладка конкретного теста

```bash
pytest tests/test_example.py::test_function -s --pdb
```

## CI/CD интеграция

### GitHub Actions

Создайте файл `.github/workflows/test.yml`:

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-asyncio pytest-cov
    - name: Run tests
      run: |
        pytest tests/ --cov=. --cov-report=xml
    - name: Upload coverage
      uses: codecov/codecov-action@v1
```

### GitLab CI

Создайте файл `.gitlab-ci.yml`:

```yaml
test:
  stage: test
  image: python:3.9
  script:
    - pip install -r requirements.txt
    - pip install pytest pytest-asyncio pytest-cov
    - pytest tests/ --cov=. --cov-report=xml
  coverage: '/TOTAL.*\s+(\d+%)$/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
```

## Лучшие практики

### Написание тестов

1. **Используйте описательные имена** для тестов и классов
2. **Следуйте паттерну AAA** (Arrange, Act, Assert)
3. **Используйте фикстуры** для общих данных и настроек
4. **Мокайте внешние зависимости** для изоляции тестов
5. **Проверяйте граничные случаи** и ошибки

### Организация тестов

1. **Группируйте связанные тесты** в классы
2. **Используйте маркеры** для категоризации
3. **Создавайте общие фикстуры** в `conftest.py`
4. **Разделяйте unit и integration тесты**

### Производительность

1. **Используйте `@pytest.mark.asyncio`** для асинхронных тестов
2. **Мокайте тяжелые операции** (база данных, внешние API)
3. **Запускайте тесты параллельно** где возможно
4. **Используйте `scope="session"`** для дорогих фикстур

## Устранение неполадок

### Частые проблемы

1. **Ошибки импорта**: убедитесь, что PYTHONPATH настроен правильно
2. **Проблемы с асинхронностью**: используйте `@pytest.mark.asyncio`
3. **Ошибки моков**: проверьте правильность путей к мокаемым объектам
4. **Проблемы с базой данных**: используйте тестовую базу данных

### Получение помощи

1. Проверьте логи pytest для детальной информации об ошибках
2. Используйте `-s` флаг для вывода print statements
3. Добавьте `--pdb` для отладки в интерактивном режиме
4. Проверьте документацию pytest и pytest-asyncio

## Заключение

Эта система тестов обеспечивает комплексное покрытие функциональности системы справочников, включая авторизацию, ролевую модель, управление справочниками и аудит. Регулярное выполнение тестов поможет обеспечить качество и надежность системы.
