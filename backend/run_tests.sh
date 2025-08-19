#!/bin/bash

# Скрипт для запуска тестов системы справочников
# Использование: ./run_tests.sh [опции]

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
print_message() {
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

# Функция для показа справки
show_help() {
    echo "Использование: $0 [опции]"
    echo ""
    echo "Опции:"
    echo "  -h, --help              Показать эту справку"
    echo "  -a, --all               Запустить все тесты"
    echo "  -c, --coverage          Запустить тесты с покрытием кода"
    echo "  -f, --fast              Запустить только быстрые тесты"
    echo "  -v, --verbose           Подробный вывод"
    echo "  -x, --stop-on-failure  Остановиться на первой ошибке"
    echo "  -k, --keep-going        Продолжить после ошибок"
    echo "  --auth                  Только тесты авторизации"
    echo "  --users                 Только тесты пользователей"
    echo "  --dictionaries          Только тесты справочников"
    echo "  --roles                 Только тесты ролевой модели"
    echo "  --audit                 Только тесты аудита"
    echo "  --integration           Только интеграционные тесты"
    echo "  --performance           Только тесты производительности"
    echo "  --security              Только тесты безопасности"
    echo "  --clean                 Очистить кэш и временные файлы"
    echo "  --install-deps          Установить зависимости для тестов"
    echo ""
    echo "Примеры:"
    echo "  $0 --all                # Запустить все тесты"
    echo "  $0 --auth --coverage    # Тесты авторизации с покрытием"
    echo "  $0 --roles --verbose    # Тесты ролей с подробным выводом"
}

# Функция для проверки зависимостей
check_dependencies() {
    print_message "Проверка зависимостей..."
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 не найден"
        exit 1
    fi
    
    if ! command -v pip3 &> /dev/null; then
        print_error "pip3 не найден"
        exit 1
    fi
    
    print_success "Зависимости проверены"
}

# Функция для установки зависимостей тестов
install_test_dependencies() {
    print_message "Установка зависимостей для тестов..."
    
    pip3 install pytest pytest-asyncio pytest-cov pytest-xdist httpx fastapi[testing] || {
        print_error "Ошибка установки зависимостей"
        exit 1
    }
    
    print_success "Зависимости установлены"
}

# Функция для очистки кэша и временных файлов
clean_cache() {
    print_message "Очистка кэша и временных файлов..."
    
    # Удаление кэша pytest
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    
    # Удаление отчетов о покрытии
    rm -rf htmlcov/ coverage.xml .coverage 2>/dev/null || true
    
    # Удаление временных файлов pytest
    rm -rf .pytest_cache/ 2>/dev/null || true
    
    print_success "Кэш очищен"
}

# Функция для запуска тестов
run_tests() {
    local test_path="tests/"
    local pytest_args=()
    
    # Добавление базовых аргументов
    pytest_args+=("-v")
    
    # Обработка опций
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -a|--all)
                test_path="tests/"
                shift
                ;;
            -c|--coverage)
                pytest_args+=("--cov=." "--cov-report=html" "--cov-report=term-missing" "--cov-report=xml")
                shift
                ;;
            -f|--fast)
                pytest_args+=("-m" "not slow")
                shift
                ;;
            -v|--verbose)
                pytest_args+=("-s" "--tb=long")
                shift
                ;;
            -x|--stop-on-failure)
                pytest_args+=("-x")
                shift
                ;;
            -k|--keep-going)
                pytest_args+=("--tb=short")
                shift
                ;;
            --auth)
                pytest_args+=("-m" "auth")
                shift
                ;;
            --users)
                pytest_args+=("-m" "users")
                shift
                ;;
            --dictionaries)
                pytest_args+=("-m" "dictionaries")
                shift
                ;;
            --roles)
                pytest_args+=("-m" "roles")
                shift
                ;;
            --audit)
                pytest_args+=("-m" "audit")
                shift
                ;;
            --integration)
                pytest_args+=("-m" "integration")
                shift
                ;;
            --performance)
                pytest_args+=("-m" "performance")
                shift
                ;;
            --security)
                pytest_args+=("-m" "security")
                shift
                ;;
            --clean)
                clean_cache
                shift
                ;;
            --install-deps)
                install_test_dependencies
                shift
                ;;
            *)
                print_error "Неизвестная опция: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Проверка существования директории тестов
    if [[ ! -d "$test_path" ]]; then
        print_error "Директория тестов не найдена: $test_path"
        exit 1
    fi
    
    # Запуск тестов
    print_message "Запуск тестов..."
    print_message "Путь: $test_path"
    print_message "Аргументы pytest: ${pytest_args[*]}"
    
    if python3 -m pytest "$test_path" "${pytest_args[@]}"; then
        print_success "Тесты выполнены успешно"
        
        # Показать отчет о покрытии если он был создан
        if [[ -f "htmlcov/index.html" ]]; then
            print_message "Отчет о покрытии создан: htmlcov/index.html"
        fi
        
        if [[ -f "coverage.xml" ]]; then
            print_message "XML отчет о покрытии создан: coverage.xml"
        fi
    else
        print_error "Тесты завершились с ошибками"
        exit 1
    fi
}

# Основная логика
main() {
    print_message "Запуск тестов системы справочников"
    
    # Проверка зависимостей
    check_dependencies
    
    # Если нет аргументов, показать справку
    if [[ $# -eq 0 ]]; then
        show_help
        exit 0
    fi
    
    # Запуск тестов
    run_tests "$@"
}

# Запуск основной функции
main "$@"
