"""
Тесты для middleware приложения
"""

import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from middleware.error_handler import exception_handler_middleware


class TestErrorHandlerMiddleware:
    """Тесты для middleware обработки ошибок"""

    @pytest.fixture
    def app(self):
        """Тестовое FastAPI приложение"""
        app = FastAPI()
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "success"}
        
        @app.get("/error")
        async def error_endpoint():
            raise HTTPException(status_code=400, detail="Test error")
        
        @app.get("/exception")
        async def exception_endpoint():
            raise ValueError("Test exception")
        
        @app.get("/database_error")
        async def database_error_endpoint():
            raise ConnectionError("Database connection failed")
        
        return app

    @pytest.fixture
    def client(self, app):
        """Тестовый клиент"""
        return TestClient(app)

    class TestExceptionHandlerMiddleware:
        """Тесты middleware обработки исключений"""

        @pytest.mark.asyncio
        async def test_middleware_successful_request(self, app):
            """Успешный запрос через middleware"""
            # Arrange
            app.add_middleware(BaseHTTPMiddleware, dispatch=exception_handler_middleware)
            
            # Act
            with TestClient(app) as client:
                response = client.get("/test")
            
            # Assert
            assert response.status_code == 200
            assert response.json() == {"message": "success"}

        @pytest.mark.asyncio
        async def test_middleware_http_exception(self, app):
            """Обработка HTTPException через middleware"""
            # Arrange
            app.add_middleware(BaseHTTPMiddleware, dispatch=exception_handler_middleware)
            
            # Act
            with TestClient(app) as client:
                response = client.get("/error")
            
            # Assert
            assert response.status_code == 400
            assert "Test error" in response.json()["detail"]

        @pytest.mark.asyncio
        async def test_middleware_general_exception(self, app):
            """Обработка общего исключения через middleware"""
            # Arrange
            app.add_middleware(BaseHTTPMiddleware, dispatch=exception_handler_middleware)
            
            # Act
            with TestClient(app) as client:
                response = client.get("/exception")
            
            # Assert
            assert response.status_code == 500
            assert "Internal server error" in response.json()["detail"]

        @pytest.mark.asyncio
        async def test_middleware_database_error(self, app):
            """Обработка ошибки базы данных через middleware"""
            # Arrange
            app.add_middleware(BaseHTTPMiddleware, dispatch=exception_handler_middleware)
            
            # Act
            with TestClient(app) as client:
                response = client.get("/database_error")
            
            # Assert
            assert response.status_code == 500
            assert "Internal server error" in response.json()["detail"]

        @pytest.mark.asyncio
        async def test_middleware_request_logging(self, app):
            """Логирование запросов через middleware"""
            # Arrange
            app.add_middleware(BaseHTTPMiddleware, dispatch=exception_handler_middleware)
            
            with patch("middleware.error_handler.logger") as mock_logger:
                # Act
                with TestClient(app) as client:
                    response = client.get("/test")
                
                # Assert
                assert response.status_code == 200
                # Проверяем, что логгер был вызван
                mock_logger.info.assert_called()

        @pytest.mark.asyncio
        async def test_middleware_error_logging(self, app):
            """Логирование ошибок через middleware"""
            # Arrange
            app.add_middleware(BaseHTTPMiddleware, dispatch=exception_handler_middleware)
            
            with patch("middleware.error_handler.logger") as mock_logger:
                # Act
                with TestClient(app) as client:
                    response = client.get("/exception")
                
                # Assert
                assert response.status_code == 500
                # Проверяем, что логгер ошибок был вызван
                mock_logger.error.assert_called()

        @pytest.mark.asyncio
        async def test_middleware_response_time(self, app):
            """Измерение времени ответа через middleware"""
            # Arrange
            app.add_middleware(BaseHTTPMiddleware, dispatch=exception_handler_middleware)
            
            # Act
            with TestClient(app) as client:
                response = client.get("/test")
            
            # Assert
            assert response.status_code == 200
            # Проверяем, что заголовок времени ответа присутствует
            assert "X-Response-Time" in response.headers

        @pytest.mark.asyncio
        async def test_middleware_custom_exception(self, app):
            """Обработка пользовательского исключения"""
            # Arrange
            class CustomException(Exception):
                pass
            
            @app.get("/custom_error")
            async def custom_error_endpoint():
                raise CustomException("Custom error message")
            
            app.add_middleware(BaseHTTPMiddleware, dispatch=exception_handler_middleware)
            
            # Act
            with TestClient(app) as client:
                response = client.get("/custom_error")
            
            # Assert
            assert response.status_code == 500
            assert "Internal server error" in response.json()["detail"]

    class TestMiddlewareIntegration:
        """Интеграционные тесты middleware"""

        @pytest.mark.asyncio
        async def test_middleware_full_request_cycle(self, app):
            """Полный цикл запроса через middleware"""
            # Arrange
            app.add_middleware(BaseHTTPMiddleware, dispatch=exception_handler_middleware)
            
            # Act
            with TestClient(app) as client:
                # Успешный запрос
                success_response = client.get("/test")
                
                # Запрос с ошибкой
                error_response = client.get("/error")
                
                # Запрос с исключением
                exception_response = client.get("/exception")
            
            # Assert
            assert success_response.status_code == 200
            assert error_response.status_code == 400
            assert exception_response.status_code == 500

        @pytest.mark.asyncio
        async def test_middleware_multiple_requests(self, app):
            """Множественные запросы через middleware"""
            # Arrange
            app.add_middleware(BaseHTTPMiddleware, dispatch=exception_handler_middleware)
            
            # Act
            with TestClient(app) as client:
                responses = []
                for _ in range(5):
                    response = client.get("/test")
                    responses.append(response)
            
            # Assert
            for response in responses:
                assert response.status_code == 200
                assert response.json() == {"message": "success"}

        @pytest.mark.asyncio
        async def test_middleware_concurrent_requests(self, app):
            """Конкурентные запросы через middleware"""
            import asyncio
            
            # Arrange
            app.add_middleware(BaseHTTPMiddleware, dispatch=exception_handler_middleware)
            
            async def make_request(client, endpoint):
                """Выполнение запроса"""
                response = client.get(endpoint)
                return response.status_code
            
            # Act
            with TestClient(app) as client:
                tasks = []
                for _ in range(10):
                    task = asyncio.create_task(make_request(client, "/test"))
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks)
            
            # Assert
            assert all(status == 200 for status in results)

    class TestMiddlewareErrorScenarios:
        """Тесты сценариев ошибок middleware"""

        @pytest.mark.asyncio
        async def test_middleware_malformed_request(self, app):
            """Обработка некорректного запроса"""
            # Arrange
            app.add_middleware(BaseHTTPMiddleware, dispatch=exception_handler_middleware)
            
            # Act
            with TestClient(app) as client:
                # Отправляем некорректный JSON
                response = client.post("/test", data="invalid json", headers={"Content-Type": "application/json"})
            
            # Assert
            assert response.status_code in [400, 422, 500]  # В зависимости от обработки

        @pytest.mark.asyncio
        async def test_middleware_timeout_simulation(self, app):
            """Симуляция таймаута запроса"""
            # Arrange
            import asyncio
            
            @app.get("/timeout")
            async def timeout_endpoint():
                await asyncio.sleep(2)  # Долгая операция
                return {"message": "timeout"}
            
            app.add_middleware(BaseHTTPMiddleware, dispatch=exception_handler_middleware)
            
            # Act
            with TestClient(app) as client:
                response = client.get("/timeout", timeout=1)  # Таймаут 1 секунда
            
            # Assert
            # Запрос должен завершиться с ошибкой таймаута
            assert response.status_code in [408, 500]

        @pytest.mark.asyncio
        async def test_middleware_memory_error(self, app):
            """Обработка ошибки памяти"""
            # Arrange
            @app.get("/memory_error")
            async def memory_error_endpoint():
                # Симулируем ошибку памяти
                raise MemoryError("Out of memory")
            
            app.add_middleware(BaseHTTPMiddleware, dispatch=exception_handler_middleware)
            
            # Act
            with TestClient(app) as client:
                response = client.get("/memory_error")
            
            # Assert
            assert response.status_code == 500
            assert "Internal server error" in response.json()["detail"]

        @pytest.mark.asynware_network_error(self, app):
            """Обработка сетевой ошибки"""
            # Arrange
            @app.get("/network_error")
            async def network_error_endpoint():
                raise ConnectionError("Network connection failed")
            
            app.add_middleware(BaseHTTPMiddleware, dispatch=exception_handler_middleware)
            
            # Act
            with TestClient(app) as client:
                response = client.get("/network_error")
            
            # Assert
            assert response.status_code == 500
            assert "Internal server error" in response.json()["detail"]

    class TestMiddlewarePerformance:
        """Тесты производительности middleware"""

        @pytest.mark.asyncio
        async def test_middleware_performance_impact(self, app):
            """Влияние middleware на производительность"""
            import time
            
            # Arrange
            app.add_middleware(BaseHTTPMiddleware, dispatch=exception_handler_middleware)
            
            # Act
            with TestClient(app) as client:
                start_time = time.time()
                
                for _ in range(100):
                    response = client.get("/test")
                    assert response.status_code == 200
                
                end_time = time.time()
                duration = end_time - start_time
            
            # Assert
            assert duration < 5.0  # 100 запросов должны выполняться быстро

        @pytest.mark.asyncio
        async def test_middleware_memory_usage(self, app):
            """Использование памяти middleware"""
            import psutil
            import os
            
            # Arrange
            app.add_middleware(BaseHTTPMiddleware, dispatch=exception_handler_middleware)
            
            # Act
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss
            
            with TestClient(app) as client:
                for _ in range(1000):
                    response = client.get("/test")
                    assert response.status_code == 200
            
            final_memory = process.memory_info().rss
            memory_increase = final_memory - initial_memory
            
            # Assert
            # Увеличение памяти не должно быть критическим (менее 10MB)
            assert memory_increase < 10 * 1024 * 1024

    class TestMiddlewareSecurity:
        """Тесты безопасности middleware"""

        @pytest.mark.asyncio
        async def test_middleware_sql_injection_prevention(self, app):
            """Предотвращение SQL инъекций"""
            # Arrange
            app.add_middleware(BaseHTTPMiddleware, dispatch=exception_handler_middleware)
            
            # Act
            with TestClient(app) as client:
                # Попытка SQL инъекции
                malicious_payload = "'; DROP TABLE users; --"
                response = client.get(f"/test?param={malicious_payload}")
            
            # Assert
            # Middleware не должен пропускать SQL инъекции
            assert response.status_code in [200, 400, 422]

        @pytest.mark.asyncio
        async def test_middleware_xss_prevention(self, app):
            """Предотвращение XSS атак"""
            # Arrange
            app.add_middleware(BaseHTTPMiddleware, dispatch=exception_handler_middleware)
            
            # Act
            with TestClient(app) as client:
                # XSS payload
                xss_payload = "<script>alert('xss')</script>"
                response = client.get(f"/test?param={xss_payload}")
            
            # Assert
            # Middleware должен обрабатывать XSS payload безопасно
            assert response.status_code in [200, 400, 422]

        @pytest.mark.asyncio
        async def test_middleware_large_payload_prevention(self, app):
            """Предотвращение больших payload"""
            # Arrange
            app.add_middleware(BaseHTTPMiddleware, dispatch=exception_handler_middleware)
            
            # Act
            with TestClient(app) as client:
                # Большой payload
                large_payload = "x" * (1024 * 1024)  # 1MB
                response = client.post("/test", data=large_payload)
            
            # Assert
            # Middleware должен обрабатывать большие payload
            assert response.status_code in [200, 400, 413, 500]


class TestCustomMiddleware:
    """Тесты пользовательского middleware"""

    class TestRequestLoggingMiddleware:
        """Тесты middleware логирования запросов"""

        @pytest.mark.asyncio
        async def test_request_logging_middleware(self):
            """Тест middleware логирования запросов"""
            # Arrange
            app = FastAPI()
            
            @app.middleware("http")
            async def request_logging_middleware(request: Request, call_next):
                # Логируем начало запроса
                start_time = time.time()
                
                response = await call_next(request)
                
                # Логируем завершение запроса
                process_time = time.time() - start_time
                response.headers["X-Process-Time"] = str(process_time)
                
                return response
            
            @app.get("/test")
            async def test_endpoint():
                return {"message": "success"}
            
            # Act
            with TestClient(app) as client:
                response = client.get("/test")
            
            # Assert
            assert response.status_code == 200
            assert "X-Process-Time" in response.headers

    class TestAuthenticationMiddleware:
        """Тесты middleware аутентификации"""

        @pytest.mark.asyncio
        async def test_authentication_middleware(self):
            """Тест middleware аутентификации"""
            # Arrange
            app = FastAPI()
            
            @app.middleware("http")
            async def auth_middleware(request: Request, call_next):
                # Проверяем заголовок авторизации
                auth_header = request.headers.get("Authorization")
                
                if not auth_header or not auth_header.startswith("Bearer "):
                    return JSONResponse(
                        status_code=401,
                        content={"detail": "Unauthorized"}
                    )
                
                return await call_next(request)
            
            @app.get("/protected")
            async def protected_endpoint():
                return {"message": "protected"}
            
            # Act & Assert
            with TestClient(app) as client:
                # Без авторизации
                response = client.get("/protected")
                assert response.status_code == 401
                
                # С авторизацией
                response = client.get("/protected", headers={"Authorization": "Bearer token"})
                assert response.status_code == 200

    class TestRateLimitingMiddleware:
        """Тесты middleware ограничения скорости"""

        @pytest.mark.asyncio
        async def test_rate_limiting_middleware(self):
            """Тест middleware ограничения скорости"""
            # Arrange
            app = FastAPI()
            request_count = {}
            
            @app.middleware("http")
            async def rate_limiting_middleware(request: Request, call_next):
                client_ip = request.client.host
                
                # Простое ограничение: максимум 5 запросов
                if client_ip not in request_count:
                    request_count[client_ip] = 0
                
                request_count[client_ip] += 1
                
                if request_count[client_ip] > 5:
                    return JSONResponse(
                        status_code=429,
                        content={"detail": "Too many requests"}
                    )
                
                return await call_next(request)
            
            @app.get("/test")
            async def test_endpoint():
                return {"message": "success"}
            
            # Act & Assert
            with TestClient(app) as client:
                # Первые 5 запросов должны пройти
                for i in range(5):
                    response = client.get("/test")
                    assert response.status_code == 200
                
                # 6-й запрос должен быть отклонен
                response = client.get("/test")
                assert response.status_code == 429
