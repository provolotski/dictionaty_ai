"""
Middleware для обработки исключений
"""

import traceback
from typing import Dict, Any
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

from exceptions import DictionaryAPIException
from utils.logger import setup_logger

logger = setup_logger(__name__)


async def exception_handler_middleware(request: Request, call_next):
    """
    Middleware для обработки исключений
    
    Args:
        request: HTTP запрос
        call_next: Следующий обработчик
        
    Returns:
        Response: HTTP ответ
    """
    try:
        response = await call_next(request)
        return response
    except Exception as exc:
        return await handle_exception(request, exc)


async def handle_exception(request: Request, exc: Exception) -> JSONResponse:
    """
    Обработка исключений
    
    Args:
        request: HTTP запрос
        exc: Исключение
        
    Returns:
        JSONResponse: Ответ с ошибкой
    """
    # Детальное логирование исключения
    logger.error(f"=== ОБРАБОТКА ИСКЛЮЧЕНИЯ ===")
    logger.error(f"Метод запроса: {request.method}")
    logger.error(f"URL запроса: {request.url}")
    logger.error(f"Тип исключения: {type(exc).__name__}")
    logger.error(f"Сообщение исключения: {str(exc)}")
    logger.error(f"Заголовки запроса: {dict(request.headers)}")
    
    # Логируем тело запроса если есть
    try:
        body = await request.body()
        if body:
            logger.error(f"Тело запроса: {body.decode('utf-8')}")
    except Exception as e:
        logger.error(f"Не удалось прочитать тело запроса: {e}")
    
    # Логируем полный traceback
    logger.error(f"Полный traceback:", exc_info=True)
    
    # Логируем исключение
    logger.error(
        f"Ошибка при обработке запроса {request.method} {request.url}: {exc}",
        extra={
            "request_method": request.method,
            "request_url": str(request.url),
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "traceback": traceback.format_exc()
        }
    )
    
    # Обрабатываем пользовательские исключения
    if isinstance(exc, DictionaryAPIException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.message,
                "details": exc.details,
                "status_code": exc.status_code
            }
        )
    
    # Обрабатываем ошибки валидации FastAPI
    if isinstance(exc, RequestValidationError):
        logger.error(f"=== ОШИБКА ВАЛИДАЦИИ ДАННЫХ ===")
        logger.error(f"Ошибки валидации:")
        for error in exc.errors():
            logger.error(f"  - Поле: {'.'.join(str(loc) for loc in error['loc'])}")
            logger.error(f"    Тип: {error['type']}")
            logger.error(f"    Сообщение: {error['msg']}")
            if 'input' in error:
                logger.error(f"    Входные данные: {error['input']}")
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "Ошибка валидации данных",
                "details": {
                    "validation_errors": exc.errors()
                },
                "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY
            }
        )
    
    # Обрабатываем ошибки базы данных
    if isinstance(exc, SQLAlchemyError):
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": "Ошибка базы данных",
                "details": {
                    "message": "Временная ошибка сервиса"
                },
                "status_code": status.HTTP_503_SERVICE_UNAVAILABLE
            }
        )
    
    # Обрабатываем остальные исключения
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Внутренняя ошибка сервера",
            "details": {
                "message": "Произошла непредвиденная ошибка"
            },
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR
        }
    )


def create_error_response(
    message: str,
    status_code: int = 500,
    details: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Создание стандартного ответа с ошибкой
    
    Args:
        message: Сообщение об ошибке
        status_code: HTTP статус код
        details: Дополнительные детали
        
    Returns:
        Dict: Словарь с ошибкой
    """
    return {
        "error": message,
        "status_code": status_code,
        "details": details or {}
    } 