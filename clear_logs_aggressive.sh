#!/bin/bash

# Агрессивный скрипт для полного удаления всех логов в проекте Dictionary Management System
# ⚠️  ВНИМАНИЕ: Этот скрипт УДАЛЯЕТ файлы логов полностью!
# Автор: AI Assistant
# Дата создания: 2025-01-15

echo "⚠️  АГРЕССИВНАЯ ОЧИСТКА ЛОГОВ - ФАЙЛЫ БУДУТ УДАЛЕНЫ ПОЛНОСТЬЮ!"
echo "=================================================================="
echo ""
echo "🔴 ВНИМАНИЕ: Этот скрипт удаляет файлы логов полностью!"
echo "🔴 Убедитесь, что у вас есть резервные копии важных логов!"
echo ""

# Запрос подтверждения
read -p "Вы уверены, что хотите продолжить? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Операция отменена пользователем"
    exit 0
fi

echo ""
echo "🧹 Начинаю агрессивную очистку логов..."
echo "======================================"

# Функция для удаления логов в указанной директории
remove_logs_in_dir() {
    local dir="$1"
    local dir_name="$2"
    
    if [ -d "$dir" ]; then
        echo "📁 Удаляю логи в директории: $dir_name"
        
        # Находим все файлы логов
        local log_files=$(find "$dir" -name "*.log" -type f 2>/dev/null)
        
        if [ -n "$log_files" ]; then
            # Удаляем файлы логов
            for log_file in $log_files; do
                echo "   🗑️  Удаляю: $(basename "$log_file")"
                rm -f "$log_file"
            done
            echo "   ✅ Удалено файлов: $(echo "$log_files" | wc -w)"
        else
            echo "   ℹ️  Файлы логов не найдены"
        fi
        
        # Находим и удаляем архивы логов (backup файлы)
        local backup_files=$(find "$dir" -name "*.log.*" -type f 2>/dev/null)
        if [ -n "$backup_files" ]; then
            echo "   🗑️  Удаляю архивные файлы логов:"
            for backup_file in $backup_files; do
                echo "      - $(basename "$back_file")"
                rm -f "$backup_file"
            done
            echo "   ✅ Удалено архивных файлов: $(echo "$backup_files" | wc -w)"
        fi
        
    else
        echo "   ⚠️  Директория не найдена: $dir"
    fi
}

# Основные директории проекта
echo ""
echo "🔍 Поиск и удаление логов..."

# Frontend логи
remove_logs_in_dir "frontend/logs" "Frontend"

# Backend логи
remove_logs_in_dir "backend/logs" "Backend"

# Корневые логи (если есть)
remove_logs_in_dir "logs" "Root"

# Поиск логов в других возможных местах
echo ""
echo "🔍 Поиск логов в других директориях..."

# Ищем все .log файлы в проекте
all_log_files=$(find . -name "*.log" -type f 2>/dev/null | grep -v "venv" | grep -v ".git")

if [ -n "$all_log_files" ]; then
    echo "📋 Найдены дополнительные файлы логов:"
    for log_file in $all_log_files; do
        echo "   📄 $log_file"
        # Удаляем файл
        rm -f "$log_file"
        echo "      ✅ Удален"
    done
else
    echo "   ℹ️  Дополнительные файлы логов не найдены"
fi

# Очистка временных файлов
echo ""
echo "🧹 Очистка временных файлов..."

# Python кэш
if [ -d "__pycache__" ]; then
    echo "   🗑️  Удаляю Python кэш..."
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
    echo "      ✅ Python кэш очищен"
fi

# .pyc файлы
pyc_files=$(find . -name "*.pyc" -type f 2>/dev/null)
if [ -n "$pyc_files" ]; then
    echo "   🗑️  Удаляю .pyc файлы..."
    find . -name "*.pyc" -delete 2>/dev/null
    echo "      ✅ .pyc файлы удалены"
fi

# Создание пустых файлов логов для сохранения структуры
echo ""
echo "📝 Создание пустых файлов логов для сохранения структуры..."

# Создаем пустые файлы логов в основных директориях
mkdir -p frontend/logs backend/logs logs

# Frontend логи
touch frontend/logs/belstat.log
touch frontend/logs/errors.log
touch frontend/logs/auth.log
touch frontend/logs/django_requests.log

# Backend логи
touch backend/logs/backend.log
touch backend/logs/errors.log

# Root логи
touch logs/backend.log
touch logs/frontend.log

echo "   ✅ Созданы пустые файлы логов"

# Статистика
echo ""
echo "📊 Статистика очистки:"
echo "======================"

# Подсчет файлов логов
frontend_logs=$(find frontend/logs -name "*.log" -type f 2>/dev/null | wc -l)
backend_logs=$(find backend/logs -name "*.log" -type f 2>/dev/null | wc -l)
root_logs=$(find logs -name "*.log" -type f 2>/dev/null | wc -l)
total_logs=$((frontend_logs + backend_logs + root_logs))

echo "   📁 Frontend логов: $frontend_logs"
echo "   📁 Backend логов: $backend_logs"
echo "   📁 Root логов: $root_logs"
echo "   📊 Всего файлов логов: $total_logs"

echo ""
echo "✅ Агрессивная очистка логов завершена успешно!"
echo ""
echo "💡 Совет: Для автоматической очистки логов можно добавить этот скрипт в cron:"
echo "   0 2 * * 0 /path/to/project/clear_logs_aggressive.sh  # Каждое воскресенье в 2:00"
echo ""
echo "🔒 Примечание: Скрипт удаляет файлы логов полностью и создает новые пустые файлы"
echo "   для сохранения структуры директорий и прав доступа."
