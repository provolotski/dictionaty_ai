#!/usr/bin/env python3
"""
Тестовый скрипт для проверки подключения к API аутентификации
"""

import requests
import json
import sys

# Настройки API
API_BASE = 'http://172.16.251.170:9090/api/v1/auth'
TIMEOUT = 10

def test_api_connection():
    """Тестирование подключения к API"""
    print("🔍 Тестирование подключения к API аутентификации...")
    print(f"   URL: {API_BASE}")
    
    try:
        # Простой GET запрос для проверки доступности
        response = requests.get(f"{API_BASE}/health", timeout=TIMEOUT)
        print(f"✅ API доступен. Статус: {response.status_code}")
        return True
    except requests.exceptions.ConnectionError:
        print("❌ Ошибка подключения к API")
        return False
    except requests.exceptions.Timeout:
        print("❌ Таймаут подключения к API")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False

def test_login_endpoint():
    """Тестирование эндпоинта логина"""
    print("\n🔍 Тестирование эндпоинта /login...")
    
    # Тестовые данные
    test_data = {
        'username': 'test_user',
        'password': 'test_password',
        'domain': 'default'
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/login",
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=TIMEOUT
        )
        
        print(f"   Статус ответа: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Эндпоинт /login работает")
            try:
                data = response.json()
                print(f"   Получен ответ: {json.dumps(data, indent=2, ensure_ascii=False)}")
            except:
                print("   Ответ не является JSON")
        elif response.status_code == 401:
            print("✅ Эндпоинт /login работает (ожидаемая ошибка 401 для тестовых данных)")
        elif response.status_code == 404:
            print("❌ Эндпоинт /login не найден")
            return False
        else:
            print(f"⚠️  Неожиданный статус: {response.status_code}")
            
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка запроса: {e}")
        return False

def test_api_structure():
    """Тестирование структуры API"""
    print("\n🔍 Проверка структуры API...")
    
    endpoints = [
        '/login',
        '/refresh_token',
        '/logout'
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.options(
                f"{API_BASE}{endpoint}",
                timeout=TIMEOUT
            )
            print(f"   {endpoint}: {response.status_code}")
        except:
            print(f"   {endpoint}: недоступен")

def main():
    """Основная функция тестирования"""
    print("🚀 Тестирование API аутентификации")
    print("=" * 50)
    
    # Тест подключения
    if not test_api_connection():
        print("\n❌ API недоступен. Проверьте:")
        print("   - Доступность сервера 172.16.251.170:9090")
        print("   - Сетевое подключение")
        print("   - Настройки файрвола")
        sys.exit(1)
    
    # Тест эндпоинта логина
    if not test_login_endpoint():
        print("\n❌ Проблемы с эндпоинтом логина")
        sys.exit(1)
    
    # Тест структуры API
    test_api_structure()
    
    print("\n✅ Тестирование завершено")
    print("\n📋 Рекомендации:")
    print("   - Убедитесь, что API сервер запущен")
    print("   - Проверьте правильность URL в настройках")
    print("   - Убедитесь, что домен настроен правильно")

if __name__ == "__main__":
    main()
