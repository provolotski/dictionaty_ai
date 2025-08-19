# Backend исправлен и готов к запуску!

## Что было исправлено:
1. **Конфигурация Pydantic** - добавлены все недостающие поля в `config.py`
2. **Имена полей** - исправлены во всех файлах (например, `log_level` → `LOG_LEVEL`)
3. **Скрипт запуска** - исправлен `start_app.sh`
4. **Конфигурация API** - IP адрес и порт бэкенда теперь берутся из конфигурации Django

## Как запустить:

### Вариант 1: Запуск через скрипт
```bash
./start_app.sh
```

### Вариант 2: Ручной запуск backend
```bash
cd backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Проверка работы:
```bash
curl http://localhost:8000/health
```

## Доступные URL:
- **Backend API**: http://localhost:8000
- **API Документация**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Примечание:
База данных не подключается из-за неправильных учетных данных в `.env` файле, но это не мешает запуску приложения - оно работает без БД.

## Логи:
- Backend: `logs/backend.log`
- Frontend: `logs/frontend.log`

## Конфигурация API

### Переменные окружения
Для настройки URL API используются переменные окружения:

```bash
# API для справочников (FastAPI)
BACKEND_API_URL=http://127.0.0.1:8000/api/v2

# API для авторизации (Auth Service)
AUTH_API_URL=http://127.0.0.1:9090/api/v1/auth
```

### Проверка конфигурации
Запустите скрипт проверки конфигурации:

```bash
cd frontend
python check_config.py
```

### Автоматическое добавление в шаблоны
Переменная `backend_api_url` автоматически добавляется во все шаблоны Django через context processor.

Подробная документация: `frontend/API_CONFIG.md`
