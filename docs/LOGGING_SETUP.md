# Настройка автоматического логирования с датой и временем

## Обзор

Система логирования была обновлена для автоматического добавления даты и времени ко всем записям логов. Теперь каждая запись в логе содержит временную метку в формате `YYYY-MM-DD HH:MM:SS`.

## Обновления в Frontend (Django)

### 1. Настройки логирования (settings.py)

Обновлена конфигурация `LOGGING` с добавлением форматтеров:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{asctime} {levelname} {name} {module} {funcName} {lineno} {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'simple': {
            'format': '{asctime} {levelname} {name} {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'auth_format': {
            'format': '{asctime} {levelname} {name} {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
    },
    # ... остальные настройки
}
```

### 2. Новые функции логирования (accounts/utils.py)

#### log_auth_event()
Логирует события авторизации:
```python
from .utils import log_auth_event

log_auth_event(
    'login_attempt',      # Тип события
    username,             # Имя пользователя
    domain,               # Домен
    ip_address,           # IP адрес
    True,                 # Успешность
    None                  # Сообщение об ошибке
)
```

#### log_user_action()
Логирует действия пользователя:
```python
from .utils import log_user_action

log_user_action(
    'user_login',         # Действие
    {'method': 'form'},   # Детали
    user_info,            # Информация о пользователе
    ip_address,           # IP адрес
    True                  # Успешность
)
```

#### log_system_event()
Логирует системные события:
```python
from .utils import log_system_event

log_system_event(
    'page_view',          # Тип события
    'Login page accessed', # Сообщение
    'INFO',               # Уровень
    {'page': 'login'}     # Дополнительные данные
)
```

## Обновления в Backend (FastAPI)

### 1. Конфигурация (config.py)

Обновлен формат логов:
```python
log_format: str = Field(
    default="%(asctime)s %(name)-30s %(levelname)-8s %(module)s:%(funcName)s:%(lineno)d %(message)s",
    description="Формат логов"
)
log_date: str = Field(default="%Y-%m-%d %H:%M:%S", description="Формат даты в логах")
```

### 2. Утилиты логирования (utils/logger.py)

#### log_api_request()
Логирует API запросы:
```python
from utils.logger import log_api_request

log_api_request(
    logger,               # Логгер
    'GET',                # HTTP метод
    '/api/users',         # URL
    200,                  # Статус код
    0.125,                # Время ответа
    user_info,            # Информация о пользователе
    ip_address            # IP адрес
)
```

#### log_database_operation()
Логирует операции с БД:
```python
from utils.logger import log_database_operation

log_database_operation(
    logger,               # Логгер
    'SELECT',             # Операция
    'users',              # Таблица
    123,                  # ID записи
    True,                 # Успешность
    None,                 # Ошибка
    0.045                 # Время выполнения
)
```

#### log_user_action()
Логирует действия пользователя:
```python
from utils.logger import log_user_action

log_user_action(
    logger,               # Логгер
    'create_dictionary',  # Действие
    {'name': 'Test'},     # Детали
    user_info,            # Информация о пользователе
    ip_address,           # IP адрес
    True                  # Успешность
)
```

## Примеры использования

### Логирование входа пользователя
```python
# В Django view
def login_view(request):
    ip_address = get_client_ip(request)
    
    # Попытка входа
    log_auth_event('login_attempt', username, domain, ip_address, True, None)
    
    if authentication_successful:
        log_auth_event('login_success', username, domain, ip_address, True, None)
        log_user_action('user_login', {'method': 'form'}, user_info, ip_address, True)
    else:
        log_auth_event('login_failed', username, domain, ip_address, False, error_message)
```

### Логирование API запроса
```python
# В FastAPI endpoint
@app.get("/api/users")
async def get_users(request: Request):
    start_time = time.time()
    
    try:
        # ... логика получения пользователей ...
        response_time = time.time() - start_time
        
        log_api_request(
            logger,
            'GET',
            str(request.url),
            200,
            response_time,
            user_info,
            request.client.host
        )
        
        return users
    except Exception as e:
        response_time = time.time() - start_time
        log_api_request(
            logger,
            'GET',
            str(request.url),
            500,
            response_time,
            user_info,
            request.client.host
        )
        raise
```

## Форматы логов

### Frontend (Django)
```
2025-01-15 14:30:25 INFO accounts.views login_view:45 USER_ACTION: user_login - {'method': 'form_login', 'domain': 'belstat'}
2025-01-15 14:30:25 INFO accounts.utils log_auth_event:45 AUTH_EVENT: login_success - User: admin@belstat - IP: 127.0.0.1
```

### Backend (FastAPI)
```
2025-01-15 14:30:25 dictionary_api                    INFO     routers.dictionary:get_dictionaries:45 API_REQUEST: GET /api/v2/dictionaries - 200 (0.125s)
2025-01-15 14:30:25 dictionary_api                    INFO     models.dictionary:create_dictionary:23 DB_OPERATION: INSERT on dictionaries - Success
```

## Преимущества

1. **Автоматические временные метки** - каждая запись содержит дату и время
2. **Структурированное логирование** - четкий формат для всех типов событий
3. **Детальная информация** - включает модуль, функцию, строку кода
4. **Централизованное управление** - единые настройки для всего приложения
5. **Ротация логов** - автоматическое управление размером файлов логов
6. **Разделение по уровням** - отдельные файлы для ошибок и обычных логов

## Мониторинг и анализ

Логи теперь содержат достаточно информации для:
- Анализа производительности API
- Отслеживания действий пользователей
- Диагностики ошибок
- Аудита безопасности
- Мониторинга использования системы
