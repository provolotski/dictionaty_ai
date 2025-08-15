#!/bin/bash

# Простой скрипт для запуска бэкенда и фронтенда
# Без установки системных зависимостей
# Автор: AI Assistant

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Функция для остановки процессов
cleanup() {
    print_status "Остановка процессов..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        print_status "Бэкенд остановлен"
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
        print_status "Фронтенд остановлен"
    fi
    exit 0
}

trap cleanup SIGINT SIGTERM

mkdir -p logs

print_status "Запуск приложения Dictionary AI (простой метод)..."

# Бэкенд
print_status "Настройка бэкенда..."
cd backend

# Удаление старого виртуального окружения если есть проблемы
if [ -d "venv" ]; then
    print_warning "Удаление старого виртуального окружения..."
    rm -rf venv
fi

print_status "Создание виртуального окружения для бэкенда..."
python3 -m venv venv
source venv/bin/activate

# Обновление базовых пакетов
print_status "Обновление базовых пакетов..."
pip install --upgrade pip setuptools wheel

# Установка зависимостей с игнорированием проблемных пакетов
print_status "Установка зависимостей бэкенда..."
while IFS= read -r line; do
    # Пропускаем комментарии и пустые строки
    [[ $line =~ ^[[:space:]]*# ]] && continue
    [[ -z "${line// }" ]] && continue
    
    print_status "Установка: $line"
    
    # Попытка установки с различными флагами
    if ! pip install "$line"; then
        print_warning "Проблема с $line, попытка альтернативного метода..."
        if ! pip install "$line" --no-deps; then
            print_warning "Пропускаем $line"
        fi
    fi
done < requirements.txt

print_success "Зависимости бэкенда установлены"

# Запуск бэкенда
print_status "Запуск бэкенда (FastAPI)..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
print_success "Бэкенд запущен (PID: $BACKEND_PID) на http://localhost:8000"

cd ..

# Фронтенд
print_status "Настройка фронтенда..."
cd frontend

# Удаление старого виртуального окружения если есть проблемы
if [ -d "venv" ]; then
    print_warning "Удаление старого виртуального окружения..."
    rm -rf venv
fi

print_status "Создание виртуального окружения для фронтенда..."
python3 -m venv venv
source venv/bin/activate

# Обновление базовых пакетов
print_status "Обновление базовых пакетов..."
pip install --upgrade pip setuptools wheel

# Установка зависимостей с игнорированием проблемных пакетов
print_status "Установка зависимостей фронтенда..."
while IFS= read -r line; do
    # Пропускаем комментарии и пустые строки
    [[ $line =~ ^[[:space:]]*# ]] && continue
    [[ -z "${line// }" ]] && continue
    
    print_status "Установка: $line"
    
    # Попытка установки с различными флагами
    if ! pip install "$line"; then
        print_warning "Проблема с $line, попытка альтернативного метода..."
        if ! pip install "$line" --no-deps; then
            print_warning "Пропускаем $line"
        fi
    fi
done < requirements.txt

print_success "Зависимости фронтенда установлены"

# Применение миграций Django
print_status "Применение миграций Django..."
python manage.py migrate --noinput

# Запуск фронтенда
print_status "Запуск фронтенда (Django)..."
python manage.py runserver 0.0.0.0:8001 > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
print_success "Фронтенд запущен (PID: $FRONTEND_PID) на http://localhost:8001"

cd ..

print_success "Приложение успешно запущено!"
echo ""
echo "Доступные URL:"
echo "  - Фронтенд: http://localhost:8001"
echo "  - Бэкенд API: http://localhost:8000"
echo "  - API Документация: http://localhost:8000/docs"
echo "  - ReDoc: http://localhost:8000/redoc"
echo ""
echo "Логи:"
echo "  - Бэкенд: logs/backend.log"
echo "  - Фронтенд: logs/frontend.log"
echo ""
echo "Для остановки нажмите Ctrl+C"

wait
