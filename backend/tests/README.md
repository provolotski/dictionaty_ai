# Тестовое покрытие проекта

Этот каталог содержит расширенное тестовое покрытие для API справочников ЕИСГС.

## 📁 Структура тестов

```
tests/
├── test_dictionary_router.py      # Тесты API роутеров
├── test_dictionary_service.py     # Тесты сервисного слоя
├── test_model_attribute.py        # Тесты модели атрибутов
├── test_cache_manager.py          # Тесты кэш-менеджера
├── test_config.py                 # Тесты конфигурации
├── test_utils.py                  # Тесты утилит
├── test_middleware.py             # Тесты middleware
├── test_schemas.py                # Тесты схем данных
├── test_exceptions.py             # Тесты исключений
├── test_integration.py            # Интеграционные тесты
├── test_performance.py            # Тесты производительности
└── README.md                      # Этот файл
```

## 🚀 Быстрый старт

### Установка зависимостей

```bash
pip install -r requirements.txt
```

### Запуск всех тестов

```bash
# Из корневой директории backend
pytest

# С подробным выводом
pytest -v

# С покрытием кода
pytest --cov=. --cov-report=html
```

### Запуск конкретных тестов

```bash
# Тесты конкретного модуля
pytest tests/test_dictionary_service.py

# Тесты конкретного класса
pytest tests/test_dictionary_service.py::TestDictionaryService

# Тесты конкретного метода
pytest tests/test_dictionary_service.py::TestDictionaryService::test_create_dictionary_success

# Тесты по маркерам
pytest -m "unit"
pytest -m "integration"
pytest -m "performance"
pytest -m "not slow"
```

## 📊 Типы тестов

### 1. Unit тесты (Модульные)
- **Файлы**: `test_*.py` (кроме `test_integration.py`, `test_performance.py`)
- **Маркер**: `@pytest.mark.unit`
- **Назначение**: Тестирование отдельных функций и методов
- **Запуск**: `pytest -m "unit"`

### 2. Integration тесты (Интеграционные)
- **Файл**: `test_integration.py`
- **Маркер**: `@pytest.mark.integration`
- **Назначение**: Тестирование взаимодействия компонентов
- **Запуск**: `pytest -m "integration"`

### 3. Performance тесты (Производительность)
- **Файл**: `test_performance.py`
- **Маркер**: `@pytest.mark.performance`
- **Назначение**: Тестирование производительности и масштабируемости
- **Запуск**: `pytest -m "performance"`

### 4. Security тесты (Безопасность)
- **Маркер**: `@pytest.mark.security`
- **Назначение**: Тестирование безопасности
- **Запуск**: `pytest -m "security"`

## 🎯 Покрытие кода

### Генерация отчета о покрытии

```bash
# HTML отчет
pytest --cov=. --cov-report=html

# Консольный отчет
pytest --cov=. --cov-report=term-missing

# XML отчет (для CI/CD)
pytest --cov=. --cov-report=xml
```

### Требования к покрытию

- **Минимальное покрытие**: 80%
- **Целевое покрытие**: 90%
- **Критические модули**: 95%

### Просмотр отчета

После генерации HTML отчета:
```bash
# Открыть в браузере
open htmlcov/index.html
```

## 🔧 Конфигурация

### pytest.ini

Основные настройки тестирования:

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
    --cov=.
    --cov-report=html:htmlcov
    --cov-report=term-missing
    --cov-report=xml
    --cov-fail-under=80
    --asyncio-mode=auto
```

### Маркеры

```bash
# Доступные маркеры
pytest --markers

# Список маркеров:
# asyncio: marks tests as async
# slow: marks tests as slow
# integration: marks tests as integration tests
# unit: marks tests as unit tests
# performance: marks tests as performance tests
# security: marks tests as security tests
```

## 🧪 Фикстуры

### Общие фикстуры

```python
@pytest.fixture
def mock_database():
    """Мок базы данных"""
    return AsyncMock()

@pytest.fixture
def dictionary_service(mock_database):
    """Сервис справочников с мок-БД"""
    # ...

@pytest.fixture
def client():
    """Тестовый клиент FastAPI"""
    return TestClient(app)
```

### Использование фикстур

```python
def test_example(dictionary_service, mock_database):
    # Тест с использованием фикстур
    pass
```

## 📈 Метрики тестирования

### Статистика тестов

```bash
# Количество тестов
pytest --collect-only -q

# Время выполнения
pytest --durations=10

# Медленные тесты
pytest --durations=0
```

### Анализ покрытия

```bash
# Детальный отчет по модулям
pytest --cov=. --cov-report=term-missing

# Покрытие конкретного модуля
pytest --cov=services --cov-report=term-missing
```

## 🚨 Обработка ошибок

### Типичные проблемы

1. **ImportError**: Проверьте PYTHONPATH
   ```bash
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   ```

2. **Database connection errors**: Используйте моки
   ```python
   @patch("database.database")
   def test_with_mock_db(mock_db):
       # ...
   ```

3. **Async test errors**: Используйте `@pytest.mark.asyncio`
   ```python
   @pytest.mark.asyncio
   async def test_async_function():
       # ...
   ```

### Отладка тестов

```bash
# Остановка на первой ошибке
pytest -x

# Подробный вывод
pytest -vvv

# Отладка с pdb
pytest --pdb

# Логирование
pytest --log-cli-level=DEBUG
```

## 🔄 CI/CD интеграция

### GitHub Actions

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
          python-version: 3.12
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest --cov=. --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v1
```

### GitLab CI

```yaml
test:
  stage: test
  script:
    - pip install -r requirements.txt
    - pytest --cov=. --cov-report=xml
  coverage: '/TOTAL.*\s+(\d+%)$/'
```

## 📋 Чек-лист для разработчиков

### Перед коммитом

- [ ] Все тесты проходят: `pytest`
- [ ] Покрытие кода ≥ 80%: `pytest --cov=. --cov-fail-under=80`
- [ ] Нет медленных тестов: `pytest --durations=0`
- [ ] Линтер не выдает ошибок: `flake8`
- [ ] Типы корректны: `mypy .` (если используется)

### При добавлении нового функционала

- [ ] Написаны unit тесты
- [ ] Написаны integration тесты (если необходимо)
- [ ] Добавлены тесты производительности (для критичных операций)
- [ ] Обновлена документация тестов

### При рефакторинге

- [ ] Все существующие тесты проходят
- [ ] Добавлены тесты для новой логики
- [ ] Удалены устаревшие тесты

## 🛠 Утилиты для тестирования

### Генерация тестовых данных

```python
# factories.py
import factory
from schemas import DictionaryIn

class DictionaryInFactory(factory.Factory):
    class Meta:
        model = DictionaryIn
    
    name = factory.Faker('company')
    code = factory.Sequence(lambda n: f'test_{n:03d}')
    description = factory.Faker('text')
    # ...
```

### Моки и патчи

```python
from unittest.mock import patch, AsyncMock

# Мок функции
@patch("module.function")
def test_with_mock(mock_function):
    mock_function.return_value = "mocked"
    # ...

# Мок асинхронной функции
@patch("module.async_function")
async def test_with_async_mock(mock_async_function):
    mock_async_function.return_value = AsyncMock()
    # ...
```

## 📚 Дополнительные ресурсы

- [pytest документация](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [FastAPI тестирование](https://fastapi.tiangolo.com/tutorial/testing/)

## 🤝 Вклад в тестирование

### Добавление новых тестов

1. Создайте файл `test_<module_name>.py`
2. Следуйте соглашениям по именованию
3. Добавьте соответствующие маркеры
4. Обновите этот README при необходимости

### Улучшение существующих тестов

1. Увеличьте покрытие кода
2. Добавьте edge cases
3. Улучшите читаемость тестов
4. Оптимизируйте производительность тестов

### Сообщение о проблемах

При обнаружении проблем с тестами:
1. Создайте issue с описанием проблемы
2. Приложите минимальный пример для воспроизведения
3. Укажите версии зависимостей
4. Опишите ожидаемое поведение
