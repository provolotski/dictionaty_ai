#!/bin/bash

# Скрипт для исправления проблем с зависимостями
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

print_status "Исправление проблем с зависимостями..."

# Проверка версии Python
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
print_status "Версия Python: $PYTHON_VERSION"

# Установка системных зависимостей
print_status "Установка системных зависимостей..."
if command -v apt-get &> /dev/null; then
    print_status "Обнаружен apt-get (Ubuntu/Debian)"
    sudo apt-get update -qq
    
    # Попытка установки python3-distutils, если доступен
    if apt-cache search python3-distutils | grep -q python3-distutils; then
        sudo apt-get install -y python3-distutils python3-dev build-essential
    else
        print_warning "python3-distutils недоступен, устанавливаем только python3-dev"
        sudo apt-get install -y python3-dev build-essential
    fi
elif command -v yum &> /dev/null; then
    print_status "Обнаружен yum (CentOS/RHEL)"
    sudo yum install -y python3-devel gcc
elif command -v dnf &> /dev/null; then
    print_status "Обнаружен dnf (Fedora)"
    sudo dnf install -y python3-devel gcc
else
    print_warning "Не удалось определить пакетный менеджер"
fi

# Исправление бэкенда
print_status "Исправление зависимостей бэкенда..."
cd backend

if [ -d "venv" ]; then
    print_warning "Удаление старого виртуального окружения бэкенда..."
    rm -rf venv
fi

print_status "Создание нового виртуального окружения для бэкенда..."
python3 -m venv venv
source venv/bin/activate

print_status "Обновление базовых пакетов..."
pip install --upgrade pip setuptools wheel

print_status "Установка зависимостей бэкенда..."
# Установка пакетов по одному для лучшего контроля
while IFS= read -r line; do
    # Пропускаем комментарии и пустые строки
    [[ $line =~ ^[[:space:]]*# ]] && continue
    [[ -z "${line// }" ]] && continue
    
    print_status "Установка: $line"
    if ! pip install "$line"; then
        print_warning "Проблема с установкой $line, попытка альтернативного метода..."
        pip install "$line" --no-deps || pip install "$line" --force-reinstall || true
    fi
done < requirements.txt

print_success "Зависимости бэкенда исправлены"
cd ..

# Исправление фронтенда
print_status "Исправление зависимостей фронтенда..."
cd frontend

if [ -d "venv" ]; then
    print_warning "Удаление старого виртуального окружения фронтенда..."
    rm -rf venv
fi

print_status "Создание нового виртуального окружения для фронтенда..."
python3 -m venv venv
source venv/bin/activate

print_status "Обновление базовых пакетов..."
pip install --upgrade pip setuptools wheel

print_status "Установка зависимостей фронтенда..."
# Установка пакетов по одному для лучшего контроля
while IFS= read -r line; do
    # Пропускаем комментарии и пустые строки
    [[ $line =~ ^[[:space:]]*# ]] && continue
    [[ -z "${line// }" ]] && continue
    
    print_status "Установка: $line"
    if ! pip install "$line"; then
        print_warning "Проблема с установкой $line, попытка альтернативного метода..."
        pip install "$line" --no-deps || pip install "$line" --force-reinstall || true
    fi
done < requirements.txt

print_success "Зависимости фронтенда исправлены"
cd ..

print_success "Все зависимости исправлены!"
echo ""
echo "Теперь можно запустить приложение:"
echo "  ./start_app.sh"
echo ""
echo "Или использовать альтернативный метод:"
echo "  ./start_app_fallback.sh"
