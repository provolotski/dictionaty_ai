#!/usr/bin/env python3
"""
Простой тест для проверки работы системы авторизации
Запуск: python test_auth.py
"""

import os
import sys
import django

# Добавляем путь к проекту Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Настраиваем Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DictionaryFront.settings')
django.setup()

from django.conf import settings
from auth_manager import auth_manager


def test_auth_config():
    """Тест конфигурации авторизации"""
    print("=== Тест конфигурации авторизации ===")
    
    auth_config = getattr(settings, 'AUTH_CONFIG', {})
    print(f"Конфигурация загружена: {bool(auth_config)}")
    
    if auth_config:
        print(f"USE_EXTERNAL_API: {auth_config.get('USE_EXTERNAL_API', 'Не задано')}")
        print(f"EXTERNAL_API.ENABLED: {auth_config.get('EXTERNAL_API', {}).get('ENABLED', 'Не задано')}")
        print(f"LOCAL_AUTH.ENABLED: {auth_config.get('LOCAL_AUTH', {}).get('ENABLED', 'Не задано')}")
        print(f"LOCAL_AUTH.FALLBACK: {auth_config.get('LOCAL_AUTH', {}).get('FALLBACK', 'Не задано')}")
    
    print()


def test_auth_manager():
    """Тест менеджера авторизации"""
    print("=== Тест менеджера авторизации ===")
    
    print(f"Внешний API включен: {auth_manager.external_api_enabled}")
    print(f"Внешний API настроен: {auth_manager.external_api_config.get('ENABLED', False)}")
    print(f"Локальная авторизация: {auth_manager.local_auth_config.get('ENABLED', False)}")
    print(f"Fallback включен: {auth_manager.local_auth_config.get('FALLBACK', False)}")
    
    if auth_manager.external_api_config.get('BASE_URL'):
        print(f"URL внешнего API: {auth_manager.external_api_config['BASE_URL']}")
    
    print()


def test_external_api_availability():
    """Тест доступности внешнего API"""
    print("=== Тест доступности внешнего API ===")
    
    if auth_manager.external_api_enabled and auth_manager.external_api_config.get('ENABLED', False):
        try:
            available = auth_manager.is_external_api_available()
            print(f"Внешний API доступен: {available}")
        except Exception as e:
            print(f"Ошибка при проверке доступности: {e}")
    else:
        print("Внешний API отключен")
    
    print()


def test_local_auth():
    """Тест локальной авторизации"""
    print("=== Тест локальной авторизации ===")
    
    if auth_manager.local_auth_config.get('ENABLED', False):
        print("Локальная авторизация включена")
        
        # Проверяем, есть ли пользователи в базе
        from django.contrib.auth.models import User
        user_count = User.objects.count()
        print(f"Пользователей в базе: {user_count}")
        
        if user_count > 0:
            # Показываем первого пользователя
            first_user = User.objects.first()
            print(f"Первый пользователь: {first_user.username} (ID: {first_user.id})")
    else:
        print("Локальная авторизация отключена")
    
    print()


def main():
    """Основная функция тестирования"""
    print("Тестирование системы авторизации\n")
    
    try:
        test_auth_config()
        test_auth_manager()
        test_external_api_availability()
        test_local_auth()
        
        print("=== Рекомендации ===")
        auth_config = getattr(settings, 'AUTH_CONFIG', {})
        
        if not auth_config:
            print("❌ AUTH_CONFIG не настроен. Добавьте настройки в settings.py")
        else:
            if auth_config.get('USE_EXTERNAL_API', False):
                print("✅ Внешний API включен")
                if not auth_config.get('LOCAL_AUTH', {}).get('FALLBACK', False):
                    print("⚠️  Рекомендуется включить fallback на локальную авторизацию")
            else:
                print("✅ Локальная авторизация включена")
            
            if auth_config.get('LOCAL_AUTH', {}).get('ENABLED', False):
                print("✅ Локальная авторизация настроена")
            else:
                print("⚠️  Локальная авторизация отключена")
        
        print("\nТестирование завершено")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
