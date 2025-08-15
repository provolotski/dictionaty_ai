# Настройка авторизации

Система авторизации поддерживает два режима работы:
1. **Внешний API** - авторизация через внешний сервер
2. **Локальная авторизация** - авторизация через Django ORM

## Конфигурация

Настройки находятся в `DictionaryFront/settings.py`:

```python
AUTH_CONFIG = {
    'USE_EXTERNAL_API': True,  # True - внешний API, False - только локальная
    'EXTERNAL_API': {
        'BASE_URL': 'http://172.16.251.170:9090/api/v1/auth',
        'ENABLED': True,
        'TIMEOUT': 30,
        'RETRY_ATTEMPTS': 3,
    },
    'LOCAL_AUTH': {
        'ENABLED': True,
        'FALLBACK': True,  # Fallback на локальную авторизацию
    }
}
```

## Команды управления

### Показать текущую конфигурацию
```bash
python manage.py configure_auth --show
```

### Включить внешний API
```bash
python manage.py configure_auth --external-api
```

### Включить только локальную авторизацию
```bash
python manage.py configure_auth --local-auth
```

### Включить fallback на локальную авторизацию
```bash
python manage.py configure_auth --fallback
```

### Изменить URL внешнего API
```bash
python manage.py configure_auth --external-url "http://new-server:9090/api/v1/auth"
```

### Изменить таймаут
```bash
python manage.py configure_auth --timeout 60
```

### Сбросить к настройкам по умолчанию
```bash
python manage.py configure_auth --reset
```

## Режимы работы

### 1. Только внешний API
```python
AUTH_CONFIG = {
    'USE_EXTERNAL_API': True,
    'EXTERNAL_API': {'ENABLED': True},
    'LOCAL_AUTH': {'ENABLED': False, 'FALLBACK': False}
}
```

### 2. Только локальная авторизация
```python
AUTH_CONFIG = {
    'USE_EXTERNAL_API': False,
    'EXTERNAL_API': {'ENABLED': False},
    'LOCAL_AUTH': {'ENABLED': True, 'FALLBACK': False}
}
```

### 3. Внешний API + fallback
```python
AUTH_CONFIG = {
    'USE_EXTERNAL_API': True,
    'EXTERNAL_API': {'ENABLED': True},
    'LOCAL_AUTH': {'ENABLED': True, 'FALLBACK': True}
}
```

## Локальная авторизация

При использовании локальной авторизации система:
1. Проверяет существование пользователя в Django ORM
2. Проверяет пароль
3. Создает mock токены для совместимости с существующим кодом

### Создание локального пользователя
```bash
python manage.py createsuperuser
```

## Логирование

Все операции авторизации логируются в:
- `frontend/logs/belstat.log` - общие логи
- `frontend/logs/django_requests.log` - HTTP запросы

## Безопасность

- Пароли хранятся в хешированном виде
- Токены сессии имеют ограниченное время жизни
- Поддерживается "запомнить меня" с настраиваемым сроком
- Все попытки авторизации логируются

## Troubleshooting

### Внешний API недоступен
1. Проверьте доступность сервера: `ping 172.16.251.170`
2. Проверьте порт: `telnet 172.16.251.170 9090`
3. Включите fallback: `python manage.py configure_auth --fallback`

### Ошибки локальной авторизации
1. Проверьте существование пользователя: `python manage.py shell`
2. Создайте пользователя: `python manage.py createsuperuser`
3. Проверьте права доступа к базе данных

### Проблемы с токенами
1. Очистите сессии: `python manage.py clearsessions`
2. Проверьте настройки сессий в `settings.py`
3. Перезапустите Django сервер
