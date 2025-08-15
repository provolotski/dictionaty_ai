.PHONY: help install test lint format clean run docker-build docker-run docker-compose-up docker-compose-down

# Переменные
PYTHON = python3
PIP = pip3
DOCKER = docker
DOCKER_COMPOSE = docker-compose

# Цвета для вывода
GREEN = \033[0;32m
YELLOW = \033[1;33m
RED = \033[0;31m
NC = \033[0m # No Color

help: ## Показать справку
	@echo "$(GREEN)Доступные команды:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'

install: ## Установить зависимости
	@echo "$(GREEN)Установка зависимостей...$(NC)"
	$(PIP) install -r requirements.txt

install-dev: ## Установить зависимости для разработки
	@echo "$(GREEN)Установка зависимостей для разработки...$(NC)"
	$(PIP) install -r requirements.txt
	$(PIP) install pytest-cov black flake8 mypy

test: ## Запустить тесты
	@echo "$(GREEN)Запуск тестов...$(NC)"
	pytest

test-cov: ## Запустить тесты с покрытием
	@echo "$(GREEN)Запуск тестов с покрытием...$(NC)"
	pytest --cov=. --cov-report=html --cov-report=term-missing

test-watch: ## Запустить тесты в режиме наблюдения
	@echo "$(GREEN)Запуск тестов в режиме наблюдения...$(NC)"
	pytest-watch

lint: ## Проверить код линтером
	@echo "$(GREEN)Проверка кода линтером...$(NC)"
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

format: ## Форматировать код
	@echo "$(GREEN)Форматирование кода...$(NC)"
	black .

type-check: ## Проверить типы
	@echo "$(GREEN)Проверка типов...$(NC)"
	mypy .

clean: ## Очистить временные файлы
	@echo "$(GREEN)Очистка временных файлов...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf dist
	rm -rf build

run: ## Запустить приложение локально
	@echo "$(GREEN)Запуск приложения...$(NC)"
	$(PYTHON) main.py

run-dev: ## Запустить приложение в режиме разработки
	@echo "$(GREEN)Запуск приложения в режиме разработки...$(NC)"
	uvicorn main:app --host 0.0.0.0 --port 9092 --reload

docker-build: ## Собрать Docker образ
	@echo "$(GREEN)Сборка Docker образа...$(NC)"
	$(DOCKER) build -t dictionary-api .

docker-run: ## Запустить Docker контейнер
	@echo "$(GREEN)Запуск Docker контейнера...$(NC)"
	$(DOCKER) run -p 9092:9092 --env-file .env dictionary-api

docker-compose-up: ## Запустить все сервисы через Docker Compose
	@echo "$(GREEN)Запуск сервисов через Docker Compose...$(NC)"
	$(DOCKER_COMPOSE) up -d

docker-compose-down: ## Остановить все сервисы Docker Compose
	@echo "$(GREEN)Остановка сервисов Docker Compose...$(NC)"
	$(DOCKER_COMPOSE) down

docker-compose-logs: ## Показать логи Docker Compose
	@echo "$(GREEN)Логи Docker Compose:$(NC)"
	$(DOCKER_COMPOSE) logs -f

setup: install-dev ## Настройка проекта для разработки
	@echo "$(GREEN)Настройка проекта завершена!$(NC)"
	@echo "$(YELLOW)Не забудьте создать файл .env на основе env.example$(NC)"

check: lint type-check test ## Полная проверка проекта
	@echo "$(GREEN)Все проверки пройдены!$(NC)"

# Команды для CI/CD
ci-install: ## Установка для CI
	$(PIP) install -r requirements.txt

ci-test: ## Тесты для CI
	pytest --cov=. --cov-report=xml

ci-lint: ## Линтинг для CI
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

ci-format-check: ## Проверка форматирования для CI
	black --check .

# Команды для продакшена
prod-build: ## Сборка для продакшена
	$(DOCKER) build -t dictionary-api:latest .

prod-deploy: ## Деплой в продакшен
	@echo "$(GREEN)Деплой в продакшен...$(NC)"
	# Добавьте здесь команды для деплоя

# Команды для мониторинга
health-check: ## Проверка состояния приложения
	@echo "$(GREEN)Проверка состояния приложения...$(NC)"
	curl -f http://localhost:9092/health || echo "$(RED)Приложение недоступно$(NC)"

logs: ## Показать логи приложения
	@echo "$(GREEN)Логи приложения:$(NC)"
	tail -f logs/dictionaryAPI.log 