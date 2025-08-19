# Конфигурация API

## Переменные окружения

Для настройки URL API используются следующие переменные окружения:

### BACKEND_API_URL
URL для API справочников (FastAPI)
- **По умолчанию**: `http://127.0.0.1:8000/api/v2`
- **Примеры**:
  - Разработка: `http://127.0.0.1:8000/api/v2`
  - Продакшн: `https://api.example.com/api/v2`
  - Docker: `http://backend:8000/api/v2`

### AUTH_API_URL
URL для API авторизации (Auth Service)
- **По умолчанию**: `http://127.0.0.1:9090/api/v1/auth`
- **Примеры**:
  - Разработка: `http://127.0.0.1:9090/api/v1/auth`
  - Продакшн: `https://auth.example.com/api/v1/auth`
  - Docker: `http://auth:9090/api/v1/auth`

## Настройка

### 1. Создание файла .env
Создайте файл `.env` в корневой директории frontend:

```bash
# API для справочников
BACKEND_API_URL=http://127.0.0.1:8000/api/v2

# API для авторизации
AUTH_API_URL=http://127.0.0.1:9090/api/v1/auth
```

### 2. Загрузка переменных окружения
Убедитесь, что переменные окружения загружаются в Django. Можно использовать python-dotenv:

```python
# В settings.py
from dotenv import load_dotenv
import os

load_dotenv()

# Теперь можно использовать os.environ.get()
BACKEND_API_URL = os.environ.get('BACKEND_API_URL', 'http://127.0.0.1:8000/api/v2')
```

### 3. Автоматическое добавление в шаблоны
Переменная `backend_api_url` автоматически добавляется во все шаблоны Django через context processor `DictionaryFront.context_processors.backend_api_url`.

## Использование в шаблонах

В шаблонах Django теперь можно использовать:

```html
<script>
const apiUrl = `{{ backend_api_url }}/api/v2/models/dictionary/?dictionary=${dictionaryId}`;
</script>
```

## Использование в Python коде

В Python коде используйте настройки Django:

```python
from django.conf import settings

# URL для API справочников
backend_url = settings.API_DICT['BASE_URL']

# URL для API авторизации
auth_url = settings.API_OATH['BASE_URL']
```

## Преимущества

1. **Гибкость**: Легко изменять URL для разных окружений
2. **Безопасность**: URL не захардкожены в коде
3. **Автоматизация**: Context processor автоматически добавляет переменные в шаблоны
4. **Обратная совместимость**: Fallback значения обеспечивают работу по умолчанию
