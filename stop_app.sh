#!/bin/bash

# Скрипт для остановки бэкенда и фронтенда
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

print_status "Остановка приложений Dictionary AI..."

# Поиск и остановка процессов uvicorn (бэкенд)
BACKEND_PIDS=$(pgrep -f "uvicorn.*main:app" || true)
if [ ! -z "$BACKEND_PIDS" ]; then
    print_status "Остановка бэкенда (PID: $BACKEND_PIDS)..."
    echo $BACKEND_PIDS | xargs kill -TERM
    sleep 2
    # Принудительная остановка, если процесс не завершился
    REMAINING_PIDS=$(pgrep -f "uvicorn.*main:app" || true)
    if [ ! -z "$REMAINING_PIDS" ]; then
        print_warning "Принудительная остановка бэкенда..."
        echo $REMAINING_PIDS | xargs kill -KILL
    fi
    print_success "Бэкенд остановлен"
else
    print_warning "Процессы бэкенда не найдены"
fi

# Поиск и остановка процессов Django (фронтенд)
FRONTEND_PIDS=$(pgrep -f "manage.py runserver" || true)
if [ ! -z "$FRONTEND_PIDS" ]; then
    print_status "Остановка фронтенда (PID: $FRONTEND_PIDS)..."
    echo $FRONTEND_PIDS | xargs kill -TERM
    sleep 2
    # Принудительная остановка, если процесс не завершился
    REMAINING_PIDS=$(pgrep -f "manage.py runserver" || true)
    if [ ! -z "$REMAINING_PIDS" ]; then
        print_warning "Принудительная остановка фронтенда..."
        echo $REMAINING_PIDS | xargs kill -KILL
    fi
    print_success "Фронтенд остановлен"
else
    print_warning "Процессы фронтенда не найдены"
fi

# Проверка, что порты освобождены
sleep 1
if lsof -i :8000 > /dev/null 2>&1; then
    print_warning "Порт 8000 все еще занят"
else
    print_success "Порт 8000 освобожден"
fi

if lsof -i :8001 > /dev/null 2>&1; then
    print_warning "Порт 8001 все еще занят"
else
    print_success "Порт 8001 освобожден"
fi

print_success "Все приложения остановлены!"
