#!/usr/bin/env python3
"""
Скрипт для проверки конфигурации API
Запуск: python check_config.py
"""

import os
import sys

# Добавляем путь к Django проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DictionaryFront.settings')

try:
    import django
    django.setup()
    
    from django.conf import settings
    
    print("=== Проверка конфигурации API ===\n")
    
    # Проверяем API_DICT
    print("API_DICT:")
    if hasattr(settings, 'API_DICT'):
        base_url = settings.API_DICT.get('BASE_URL', 'Не задан')
        print(f"  BASE_URL: {base_url}")
        
        # Извлекаем хост и порт
        if base_url != 'Не задан':
            if base_url.endswith('/api/v2'):
                backend_url = base_url[:-len('/api/v2')]
            elif base_url.endswith('/api/v1'):
                backend_url = base_url[:-len('/api/v1')]
            else:
                backend_url = base_url
            
            print(f"  Backend URL (без /api/v2): {backend_url}")
    else:
        print("  Не найден в настройках")
    
    print()
    
    # Проверяем API_OATH
    print("API_OATH:")
    if hasattr(settings, 'API_OATH'):
        base_url = settings.API_OATH.get('BASE_URL', 'Не задан')
        print(f"  BASE_URL: {base_url}")
    else:
        print("  Не найден в настройках")
    
    print()
    
    # Проверяем переменные окружения
    print("Переменные окружения:")
    backend_env = os.environ.get('BACKEND_API_URL', 'Не задана')
    auth_env = os.environ.get('AUTH_API_URL', 'Не задана')
    
    print(f"  BACKEND_API_URL: {backend_env}")
    print(f"  AUTH_API_URL: {auth_env}")
    
    print()
    
    # Проверяем context processor
    print("Context Processor:")
    try:
        from DictionaryFront.context_processors import backend_api_url
        
        # Создаем mock request
        class MockRequest:
            pass
        
        request = MockRequest()
        context = backend_api_url(request)
        
        print(f"  backend_api_url: {context.get('backend_api_url', 'Не найден')}")
        
    except Exception as e:
        print(f"  Ошибка: {e}")
    
    print("\n=== Проверка завершена ===")
    
except ImportError as e:
    print(f"Ошибка импорта: {e}")
    print("Убедитесь, что вы находитесь в правильной директории и Django установлен")
except Exception as e:
    print(f"Ошибка: {e}")
