# API Справочников ЕИСГС

Сервис доступа к справочникам Единой информационной системы государственной статистики (ЕИСГС).

## 🚀 Возможности

- Создание и управление справочниками
- Импорт данных из CSV файлов
- Поиск по справочникам
- REST API с документацией Swagger/ReDoc
- Поддержка версионирования API (v1, v2)
- Многоязычность (русский, белорусский, английский)

## 🛠 Технологии

- **FastAPI** - современный веб-фреймворк для Python
- **PostgreSQL** - база данных
- **Pydantic** - валидация данных
- **Pandas** - обработка данных
- **Docker** - контейнеризация
- **Pytest** - тестирование

## 📋 Требования

- Python 3.12+
- PostgreSQL 12+
- Docker (опционально)

## 🚀 Быстрый старт

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd dictionary_v2
```

### 2. Настройка переменных окружения

Скопируйте файл с примерами переменных окружения:

```bash
cp env.example .env
```

Отредактируйте `.env` файл, указав ваши настройки:

```env
# Настройки базы данных
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_SCHEMA=nsi
POSTGRES_DB=nsi_database

# Настройки логирования
LOG_LEVEL=INFO
LOG_FILE=logs/dictionaryAPI.log

# Настройки API
API_HOST=0.0.0.0
API_PORT=9092

# CORS настройки
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Настройка базы данных

Создайте базу данных PostgreSQL и выполните SQL скрипты из папки `database/public/`:

```bash
psql -U your_user -d nsi_database -f database/public/dictionary.sql
psql -U your_user -d nsi_database -f database/public/dictionary_type.sql
# ... и так далее для всех файлов
```

### 5. Запуск приложения

#### Локальный запуск

```bash
python main.py
```

#### Через uvicorn

```bash
uvicorn main:app --host 0.0.0.0 --port 9092 --reload
```

#### Через Docker

```bash
# Сборка образа
docker build -t dictionary-api .

# Запуск контейнера
docker run -p 9092:9092 --env-file .env dictionary-api
```

### 6. Проверка работоспособности

Откройте браузер и перейдите по адресу:
- API документация: http://localhost:9092/docs
- ReDoc документация: http://localhost:9092/redoc
- Проверка состояния: http://localhost:9092/health

## 📚 API Документация

### Основные эндпоинты

#### Справочники

- `POST /api/v2/models/newDictionary` - Создание нового справочника
- `GET /api/v2/models/list` - Получение списка справочников
- `GET /api/v2/models/getDictionaryByID` - Получение справочника по ID
- `POST /api/v2/models/EditDictionary` - Редактирование справочника
- `DELETE /api/v2/models/deleteDictonaryById` - Удаление справочника

#### Позиции справочников

- `POST /api/v2/models/CreatePosition` - Создание позиции
- `POST /api/v2/models/EditPosition` - Редактирование позиции
- `GET /api/v2/models/dictionary/` - Получение значений справочника
- `GET /api/v2/models/dictionaryValueByCode/` - Поиск по коду
- `GET /api/v2/models/dictionaryValueByID` - Поиск по ID

#### Импорт данных

- `POST /api/v2/models/importCSV` - Импорт данных из CSV файла

### Примеры запросов

#### Создание справочника

```bash
curl -X POST "http://localhost:9092/api/v2/models/newDictionary" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Тестовый справочник",
    "code": "TEST_001",
    "description": "Описание тестового справочника",
    "start_date": "2024-01-01",
    "finish_date": "2024-12-31",
    "name_eng": "Test Dictionary",
    "name_bel": "Тэставы даведнік",
    "description_eng": "Test dictionary description",
    "description_bel": "Апісанне тэставага даведніка",
    "gko": "Test GKO",
    "organization": "Test Organization",
    "classifier": "TEST_CLASS",
    "id_type": 1
  }'
```

#### Получение списка справочников

```bash
curl -X GET "http://localhost:9092/api/v2/models/list"
```

## 🧪 Тестирование

### Запуск тестов

```bash
# Все тесты
pytest

# С подробным выводом
pytest -v

# С покрытием кода
pytest --cov=.

# Конкретный тест
pytest tests/test_dictionary_router.py::test_create_new_dictionary
```

### Структура тестов

- `tests/test_dictionary_router.py` - Тесты API эндпоинтов
- `tests/test_model_attribute.py` - Тесты модели атрибутов

## 📁 Структура проекта

```
dictionary_v2/
├── config.py                 # Конфигурация приложения
├── database.py              # Настройки базы данных
├── exceptions.py            # Пользовательские исключения
├── main.py                  # Главный модуль приложения
├── schemas.py               # Pydantic модели
├── requirements.txt         # Зависимости Python
├── Dockerfile              # Docker конфигурация
├── README.md               # Документация
├── env.example             # Пример переменных окружения
├── database/               # SQL скрипты
│   └── public/
├── logs/                   # Логи приложения
├── middleware/             # Middleware
│   └── error_handler.py
├── models/                 # Модели данных
│   ├── model_dictionary.py
│   └── model_attribute.py
├── routers/                # API роутеры
│   ├── dictionary.py
│   └── dictionary_v1.py
├── services/               # Бизнес-логика
│   └── dictionary_service.py
├── static/                 # Статические файлы
├── tests/                  # Тесты
│   ├── test_dictionary_router.py
│   └── test_model_attribute.py
└── utils/                  # Утилиты
    └── logger.py
```

## 🔧 Конфигурация

### Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `POSTGRES_USER` | Пользователь PostgreSQL | - |
| `POSTGRES_PASSWORD` | Пароль PostgreSQL | - |
| `POSTGRES_HOST` | Хост PostgreSQL | - |
| `POSTGRES_PORT` | Порт PostgreSQL | 5432 |
| `POSTGRES_DB` | Имя базы данных | - |
| `POSTGRES_SCHEMA` | Схема базы данных | nsi |
| `LOG_LEVEL` | Уровень логирования | INFO |
| `API_HOST` | Хост для API | 0.0.0.0 |
| `API_PORT` | Порт для API | 9092 |
| `CORS_ORIGINS` | Разрешенные origins | localhost |

### Логирование

Логи сохраняются в файл `logs/dictionaryAPI.log` с ротацией (максимум 10MB, 5 файлов).

## 🐳 Docker

### Сборка образа

```bash
docker build -t dictionary-api .
```

### Запуск контейнера

```bash
docker run -d \
  --name dictionary-api \
  -p 9092:9092 \
  --env-file .env \
  dictionary-api
```

### Docker Compose

Создайте файл `docker-compose.yml`:

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "9092:9092"
    env_file:
      - .env
    depends_on:
      - postgres
    restart: unless-stopped

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: nsi_database
      POSTGRES_USER: nsi_user
      POSTGRES_PASSWORD: nsi_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

Запуск:

```bash
docker-compose up -d
```

## 🔒 Безопасность

- Все учетные данные хранятся в переменных окружения
- Настроен CORS для ограничения доступа
- Валидация всех входных данных
- Централизованная обработка ошибок
- Логирование всех операций

## 📝 Логирование

Приложение использует структурированное логирование с ротацией файлов:

- Уровни: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Формат: `%(asctime)s %(name)-30s %(levelname)-8s %(message)s`
- Ротация: 10MB на файл, максимум 5 файлов

## 🤝 Вклад в проект

1. Форкните репозиторий
2. Создайте ветку для новой функции
3. Внесите изменения
4. Добавьте тесты
5. Создайте Pull Request

## 📄 Лицензия

Этот проект распространяется под лицензией MIT.

## 🆘 Поддержка

При возникновении проблем:

1. Проверьте логи в файле `logs/dictionaryAPI.log`
2. Убедитесь, что база данных доступна
3. Проверьте настройки в файле `.env`
4. Создайте Issue в репозитории

## 🔄 Версионирование

- **v1** - Устаревшая версия API (поддержка для обратной совместимости)
- **v2** - Текущая версия API с улучшенной архитектурой 