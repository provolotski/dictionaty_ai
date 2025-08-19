#!/bin/bash

# Скрипт для запуска тестов проекта Dictionary AI

echo "🚀 Запуск тестов проекта Dictionary AI"
echo "======================================"

# Проверяем наличие pytest
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest не найден. Установите pytest:"
    echo "   pip install pytest pytest-asyncio pytest-cov pytest-django httpx"
    exit 1
fi

# Функция для запуска backend тестов
run_backend_tests() {
    echo ""
    echo "🔧 Запуск Backend тестов..."
    cd backend
    
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    echo "📊 Тесты авторизации и пользователей..."
    pytest tests/test_auth_and_users.py -v --tb=short
    
    echo "📊 Тесты справочников..."
    pytest tests/test_dictionary_router.py -v --tb=short
    
    echo "📊 Тесты сервисов..."
    pytest tests/test_dictionary_service.py -v --tb=short
    
    echo "📊 Интеграционные тесты..."
    pytest tests/test_integration.py -v --tb=short
    
    echo "📊 Все backend тесты..."
    pytest tests/ -v --tb=short --cov=. --cov-report=term-missing
    
    cd ..
}

# Функция для запуска frontend тестов
run_frontend_tests() {
    echo ""
    echo "🌐 Запуск Frontend тестов..."
    cd frontend
    
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    echo "📊 Тесты API views..."
    pytest tests/test_api_views.py -v --tb=short
    
    echo "📊 Тесты Django views..."
    pytest tests/test_views.py -v --tb=short
    
    echo "📊 Все frontend тесты..."
    pytest tests/ -v --tb=short --cov=. --cov-report=term-missing
    
    cd ..
}

# Функция для запуска всех тестов
run_all_tests() {
    echo ""
    echo "🎯 Запуск всех тестов..."
    
    # Backend тесты
    run_backend_tests
    
    # Frontend тесты
    run_frontend_tests
    
    echo ""
    echo "📈 Общая статистика покрытия..."
    pytest --cov=. --cov-report=html --cov-report=term-missing
}

# Функция для запуска тестов по категориям
run_tests_by_category() {
    local category=$1
    
    case $category in
        "auth")
            echo "🔐 Запуск тестов авторизации..."
            pytest -m auth -v --tb=short
            ;;
        "users")
            echo "👥 Запуск тестов пользователей..."
            pytest -m users -v --tb=short
            ;;
        "dictionaries")
            echo "📚 Запуск тестов справочников..."
            pytest -m dictionaries -v --tb=short
            ;;
        "api")
            echo "🔌 Запуск тестов API..."
            pytest -m api -v --tb=short
            ;;
        "views")
            echo "👁️ Запуск тестов views..."
            pytest -m views -v --tb=short
            ;;
        "backend")
            echo "🔧 Запуск backend тестов..."
            pytest -m backend -v --tb=short
            ;;
        "frontend")
            echo "🌐 Запуск frontend тестов..."
            pytest -m frontend -v --tb=short
            ;;
        "integration")
            echo "🔗 Запуск интеграционных тестов..."
            pytest -m integration -v --tb=short
            ;;
        "unit")
            echo "🧪 Запуск unit тестов..."
            pytest -m unit -v --tb=short
            ;;
        *)
            echo "❌ Неизвестная категория: $category"
            echo "Доступные категории: auth, users, dictionaries, api, views, backend, frontend, integration, unit"
            exit 1
            ;;
    esac
}

# Функция для показа справки
show_help() {
    echo "Использование: $0 [опции]"
    echo ""
    echo "Опции:"
    echo "  -h, --help           Показать эту справку"
    echo "  -a, --all            Запустить все тесты"
    echo "  -b, --backend        Запустить только backend тесты"
    echo "  -f, --frontend       Запустить только frontend тесты"
    echo "  -c, --category CAT   Запустить тесты по категории"
    echo "  -v, --verbose        Подробный вывод"
    echo ""
    echo "Категории тестов:"
    echo "  auth         - Тесты авторизации"
    echo "  users        - Тесты управления пользователями"
    echo "  dictionaries - Тесты справочников"
    echo "  api          - Тесты API"
    echo "  views        - Тесты Django views"
    echo "  backend      - Backend тесты"
    echo "  frontend     - Frontend тесты"
    echo "  integration  - Интеграционные тесты"
    echo "  unit         - Unit тесты"
    echo ""
    echo "Примеры:"
    echo "  $0 --all                    # Все тесты"
    echo "  $0 --backend                # Только backend"
    echo "  $0 --category auth          # Только авторизация"
    echo "  $0 --category dictionaries  # Только справочники"
}

# Основная логика
case "${1:-}" in
    -h|--help)
        show_help
        ;;
    -a|--all)
        run_all_tests
        ;;
    -b|--backend)
        run_backend_tests
        ;;
    -f|--frontend)
        run_frontend_tests
        ;;
    -c|--category)
        if [ -z "$2" ]; then
            echo "❌ Укажите категорию тестов"
            exit 1
        fi
        run_tests_by_category "$2"
        ;;
    -v|--verbose)
        export PYTEST_ADDOPTS="-v -s --tb=long"
        run_all_tests
        ;;
    "")
        echo "Выберите опцию:"
        echo "  1) Все тесты"
        echo "  2) Только backend"
        echo "  3) Только frontend"
        echo "  4) По категории"
        echo "  5) Справка"
        echo ""
        read -p "Введите номер (1-5): " choice
        
        case $choice in
            1) run_all_tests ;;
            2) run_backend_tests ;;
            3) run_frontend_tests ;;
            4)
                echo "Доступные категории: auth, users, dictionaries, api, views, backend, frontend, integration, unit"
                read -p "Введите категорию: " category
                run_tests_by_category "$category"
                ;;
            5) show_help ;;
            *) echo "❌ Неверный выбор" ;;
        esac
        ;;
    *)
        echo "❌ Неизвестная опция: $1"
        show_help
        exit 1
        ;;
esac

echo ""
echo "✅ Тестирование завершено!"
