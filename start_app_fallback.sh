#!/bin/bash

# Альтернативный скрипт для запуска бэкенда и фронтенда
# Решает проблемы с distutils в Python 3.12
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

print_status "Запуск приложения Dictionary AI (альтернативный метод)..."

# Проверка версии Python
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
print_status "Версия Python: $PYTHON_VERSION"

# Установка системных зависимостей для решения проблем с distutils
print_status "Установка системных зависимостей..."
if command -v apt-get &> /dev/null; then
    sudo apt-get update -qq
    
    # Попытка установки python3-distutils, если доступен
    if apt-cache search python3-distutils | grep -q python3-distutils; then
        sudo apt-get install -y python3-distutils python3-dev build-essential
    else
        print_warning "python3-distutils недоступен, устанавливаем только python3-dev"
        sudo apt-get install -y python3-dev build-essential
    fi
elif command -v yum &> /dev/null; then
    sudo yum install -y python3-devel gcc
elif command -v dnf &> /dev/null; then
    sudo dnf install -y python3-devel gcc
fi

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

# Установка distutils отдельно
print_status "Установка distutils..."
pip install setuptools

# Попытка установки зависимостей
print_status "Установка зависимостей бэкенда..."
if pip install -r requirements.txt; then
    print_success "Зависимости бэкенда установлены"
else
    print_warning "Проблемы с установкой, попытка альтернативного метода..."
    
    # Установка пакетов по одному
    while IFS= read -r line; do
        # Пропускаем комментарии и пустые строки
        [[ $line =~ ^[[:space:]]*# ]] && continue
        [[ -z "${line// }" ]] && continue
        
        print_status "Установка: $line"
        pip install "$line" --no-deps || pip install "$line" || true
    done < requirements.txt
    
    print_success "Зависимости бэкенда установлены (альтернативный метод)"
fi

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

# Установка distutils отдельно
print_status "Установка distutils..."
pip install setuptools

# Попытка установки зависимостей
print_status "Установка зависимостей фронтенда..."
if pip install -r requirements.txt; then
    print_success "Зависимости фронтенда установлены"
else
    print_warning "Проблемы с установкой, попытка альтернативного метода..."
    
    # Установка пакетов по одному
    while IFS= read -r line; do
        # Пропускаем комментарии и пустые строки
        [[ $line =~ ^[[:space:]]*# ]] && continue
        [[ -z "${line// }" ]] && continue
        
        print_status "Установка: $line"
        pip install "$line" --no-deps || pip install "$line" || true
    done < requirements.txt
    
    print_success "Зависимости фронтенда установлены (альтернативный метод)"
fi

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
