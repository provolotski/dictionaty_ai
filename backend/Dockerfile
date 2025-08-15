# Multi-stage build для оптимизации размера образа
FROM python:3.12-slim as builder

# Установка системных зависимостей для сборки
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Создание виртуального окружения
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Копирование и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Финальный образ
FROM python:3.12-slim

# Метаданные образа
LABEL maintainer="ViachaslauProvolocki"
LABEL description="API сервис справочников ЕИСГС"
LABEL version="2.0.0"

# Создание пользователя для безопасности
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Установка рабочей директории
WORKDIR /app

# Копирование виртуального окружения из builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Копирование кода приложения
COPY . .

# Создание директории для логов
RUN mkdir -p logs && chown -R appuser:appuser /app

# Переключение на непривилегированного пользователя
USER appuser

# Переменные окружения
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:9092/health')" || exit 1

# Экспорт порта
EXPOSE 9092

# Команда запуска
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9092"]