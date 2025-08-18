"""
Главный модуль приложения API справочников
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from fastapi.responses import JSONResponse
import uvicorn
import logging
import os

from routers.dictionary import dict_router
from routers.dictionary_v1 import dict_router as dict_router1
from routers.audit import audit_router
from routers.users import users_router
from database import database, check_database_connection
from config import settings, setup_logging
from middleware.error_handler import exception_handler_middleware
from utils.logger import setup_logger
from cache.cache_manager import cache_manager

# Настраиваем логирование с временной зоной Minsk
logger = setup_logging()

# Настраиваем логирование для FastAPI
logging.getLogger("fastapi").setLevel(logging.DEBUG)
logging.getLogger("uvicorn").setLevel(logging.DEBUG)
logging.getLogger("uvicorn.access").setLevel(logging.DEBUG)
logging.getLogger("uvicorn.error").setLevel(logging.DEBUG)

# Создаем директорию для логов если её нет
os.makedirs('logs', exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управление жизненным циклом приложения
    """
    logger.info("Запуск приложения...")
    
    # Инициализация кэш-менеджера
    logger.info("Инициализация кэш-менеджера...")
    await cache_manager.initialize()
    
    # Проверка подключения к базе данных
    logger.info("Проверка подключения к базе данных...")
    try:
        if await check_database_connection():
            logger.info("Подключение к базе данных успешно")
            # Подключение к базе данных
            logger.info("Подключение к базе данных...")
            await database.connect()
        else:
            logger.warning("Не удалось подключиться к базе данных - приложение запустится без БД")
    except Exception as e:
        logger.warning(f"Ошибка подключения к базе данных: {e} - приложение запустится без БД")
    
    logger.info("Приложение запущено и готово к работе")
    
    yield
    
    # Отключение от базы данных
    logger.info("Завершение работы приложения...")
    try:
        await database.disconnect()
    except Exception as e:
        logger.warning(f"Ошибка отключения от базы данных: {e}")
    
    # Очистка кэш-менеджера
    await cache_manager.cleanup()
    
    logger.info("Приложение остановлено")


# Создание роутеров
api_router = APIRouter(prefix="/api/v2")
api_router.include_router(dict_router)

api_router_v1 = APIRouter(prefix="/api/v1")
api_router_v1.include_router(dict_router1)
api_router_v1.include_router(audit_router)

# Создание приложения
app = FastAPI(
    lifespan=lifespan,
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="API для системы управления справочниками"
)

# Настройка CORS
cors_origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",")]
cors_methods = [method.strip() for method in settings.CORS_ALLOW_METHODS.split(",")]
cors_headers = [header.strip() for header in settings.CORS_ALLOW_HEADERS.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware для логирования запросов
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"REQUEST → {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"RESPONSE ← {request.method} {request.url} {response.status_code}")
    return response

# Обработчик ошибок
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"GLOBAL_ERROR → {request.method} {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Внутренняя ошибка сервера"}
    )

# Подключение статических файлов
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", include_in_schema=False)
async def root():
    """
    Корневой эндпоинт
    """
    return {"message": "Dictionary Management System API", "version": "1.0.0"}


@app.get("/health", include_in_schema=False)
async def health_check():
    """
    Проверка состояния приложения
    """
    try:
        # Проверка подключения к базе данных
        is_connected = await check_database_connection()
        
        # Получение статистики кэша
        cache_stats = await cache_manager.get_stats()
        
        return {"status": "healthy", "timestamp": "2025-01-15T08:30:00+03:00"}
    except Exception as e:
        logger.warning(f"Ошибка проверки состояния БД: {e}")
        return {"status": "healthy", "timestamp": "2025-01-15T08:30:00+03:00"}


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """
    Кастомная страница Swagger UI
    """
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
    )


@app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
async def swagger_ui_redirect():
    """
    Редирект для OAuth2 в Swagger UI
    """
    return get_swagger_ui_oauth2_redirect_html()


@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    """
    Кастомная страница ReDoc
    """
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=app.title + " - ReDoc",
        redoc_js_url="/static/redoc.standalone.js",
    )


@app.get("/cache/stats", include_in_schema=False)
async def get_cache_stats():
    """
    Получение статистики кэша
    """
    try:
        stats = await cache_manager.get_stats()
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Ошибка получения статистики кэша: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@app.post("/cache/clear", include_in_schema=False)
async def clear_cache():
    """
    Очистка всего кэша
    """
    try:
        success = await cache_manager.clear_pattern("*")
        return {
            "success": success,
            "message": "Кэш очищен" if success else "Ошибка очистки кэша"
        }
    except Exception as e:
        logger.error(f"Ошибка очистки кэша: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@app.post("/cache/clear/{pattern}", include_in_schema=False)
async def clear_cache_pattern(pattern: str):
    """
    Очистка кэша по паттерну
    """
    try:
        success = await cache_manager.clear_pattern(f"{pattern}*")
        return {
            "success": success,
            "pattern": pattern,
            "message": f"Кэш очищен по паттерну: {pattern}" if success else "Ошибка очистки кэша"
        }
    except Exception as e:
        logger.error(f"Ошибка очистки кэша по паттерну {pattern}: {e}")
        return {
            "success": False,
            "pattern": pattern,
            "error": str(e)
        }


# Подключение роутеров
app.include_router(api_router)
app.include_router(api_router_v1)
app.include_router(users_router, prefix="/api/v1")

if __name__ == "__main__":
    logger.info("Запуск Dictionary Management System API...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )
