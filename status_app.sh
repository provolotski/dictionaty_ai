#!/bin/bash

# Скрипт для проверки статуса бэкенда и фронтенда
# Автор: AI Assistant

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода с цветом
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "=========================================="
echo "  Статус приложений Dictionary AI"
echo "=========================================="
echo ""

# Проверка бэкенда
print_status "Проверка бэкенда (FastAPI)..."
BACKEND_PIDS=$(pgrep -f "uvicorn.*main:app" || true)
if [ ! -z "$BACKEND_PIDS" ]; then
    print_success "Бэкенд запущен (PID: $BACKEND_PIDS)"
    
    # Проверка доступности API
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        print_success "API доступен на http://localhost:8000"
    else
        print_warning "API недоступен на http://localhost:8000"
    fi
    
    # Проверка документации
    if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
        print_success "Документация доступна на http://localhost:8000/docs"
    else
        print_warning "Документация недоступна"
    fi
else
    print_error "Бэкенд не запущен"
fi

echo ""

# Проверка фронтенда
print_status "Проверка фронтенда (Django)..."
FRONTEND_PIDS=$(pgrep -f "manage.py runserver" || true)
if [ ! -z "$FRONTEND_PIDS" ]; then
    print_success "Фронтенд запущен (PID: $FRONTEND_PIDS)"
    
    # Проверка доступности фронтенда
    if curl -s http://localhost:8001 > /dev/null 2>&1; then
        print_success "Фронтенд доступен на http://localhost:8001"
    else
        print_warning "Фронтенд недоступен на http://localhost:8001"
    fi
else
    print_error "Фронтенд не запущен"
fi

echo ""

# Проверка портов
print_status "Проверка портов..."
if lsof -i :8000 > /dev/null 2>&1; then
    print_success "Порт 8000 занят (бэкенд)"
else
    print_warning "Порт 8000 свободен"
fi

if lsof -i :8001 > /dev/null 2>&1; then
    print_success "Порт 8001 занят (фронтенд)"
else
    print_warning "Порт 8001 свободен"
fi

echo ""

# Проверка лог-файлов
print_status "Проверка лог-файлов..."
if [ -f "logs/backend.log" ]; then
    BACKEND_LOG_SIZE=$(du -h logs/backend.log | cut -f1)
    print_success "Лог бэкенда: logs/backend.log ($BACKEND_LOG_SIZE)"
else
    print_warning "Лог бэкенда не найден"
fi

if [ -f "logs/frontend.log" ]; then
    FRONTEND_LOG_SIZE=$(du -h logs/frontend.log | cut -f1)
    print_success "Лог фронтенда: logs/frontend.log ($FRONTEND_LOG_SIZE)"
else
    print_warning "Лог фронтенда не найден"
fi

echo ""
echo "=========================================="
