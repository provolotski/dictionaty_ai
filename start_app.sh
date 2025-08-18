#!/bin/bash

# Скрипт для запуска бэкенда и фронтенда
# Автор: AI Assistant
# Дата: $(date)

set -e  # Остановка при ошибке

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

# Проверка наличия Python
if ! command -v python3 &> /dev/null; then
    print_error "Python3 не найден. Установите Python3."
    exit 1
fi

# Проверка наличия pip
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 не найден. Установите pip3."
    exit 1
fi

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

# Обработка сигналов для корректного завершения
trap cleanup SIGINT SIGTERM

# Создание лог-директорий
mkdir -p logs

print_status "Запуск приложения Dictionary AI..."

# Установка зависимостей для бэкенда
print_status "Установка зависимостей для бэкенда..."
cd backend
if [ ! -d "venv" ]; then
    print_status "Создание виртуального окружения для бэкенда..."
    python3 -m venv venv
fi

source venv/bin/activate

# Установка setuptools и wheel для решения проблем с distutils
print_status "Обновление базовых пакетов..."
pip install --upgrade pip setuptools wheel

# Установка зависимостей с обработкой ошибок
print_status "Установка зависимостей бэкенда..."
if pip install -r requirements.txt; then
    print_success "Зависимости бэкенда установлены"
else
    print_warning "Возникли проблемы при установке зависимостей бэкенда"
    print_status "Попытка установки с игнорированием ошибок..."
    pip install -r requirements.txt --no-deps || true
    pip install -r requirements.txt --force-reinstall --no-deps || true
fi

# Создание .env файла если его нет
if [ ! -f ".env" ]; then
    print_status "Создание .env файла..."
    cp env.example .env
fi

# Запуск бэкенда
print_status "Запуск бэкенда (FastAPI)..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
print_success "Бэкенд запущен (PID: $BACKEND_PID) на http://localhost:8000"
print_status "Документация API: http://localhost:8000/docs"

# Возврат в корневую директорию
cd ..

# Установка зависимостей для фронтенда
print_status "Установка зависимостей для фронтенда..."
cd frontend
if [ ! -d "venv" ]; then
    print_status "Создание виртуального окружения для фронтенда..."
    python3 -m venv venv
fi

source venv/bin/activate

# Установка setuptools и wheel для решения проблем с distutils
print_status "Обновление базовых пакетов..."
pip install --upgrade pip setuptools wheel

# Установка зависимостей с обработкой ошибок
print_status "Установка зависимостей фронтенда..."
if pip install -r requirements.txt; then
    print_success "Зависимости фронтенда установлены"
else
    print_warning "Возникли проблемы при установке зависимостей фронтенда"
    print_status "Попытка установки с игнорированием ошибок..."
    pip install -r requirements.txt --no-deps || true
    pip install -r requirements.txt --force-reinstall --no-deps || true
fi

# Применение миграций Django
print_status "Применение миграций Django..."
python manage.py migrate --noinput

# Запуск фронтенда
print_status "Запуск фронтенда (Django)..."
python manage.py runserver 0.0.0.0:8001 > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
print_success "Фронтенд запущен (PID: $FRONTEND_PID) на http://localhost:8001"

# Возврат в корневую директорию
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

# Ожидание завершения
wait
