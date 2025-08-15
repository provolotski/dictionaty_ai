#!/usr/bin/env python3
"""
Детальный тест API аутентификации с разными форматами данных
"""

import requests
import json
import sys

# Настройки API
API_BASE = 'http://172.16.251.170:9090/api/v1/auth'
TIMEOUT = 10

def test_different_formats():
    """Тестирование разных форматов данных"""
    print("🔍 Тестирование разных форматов данных для /login...")
    
    test_cases = [
        {
            'name': 'Стандартный формат',
            'data': {
                'username': 'test_user',
                'password': 'test_password',
                'domain': 'default'
            }
        },
        {
            'name': 'Формат без домена',
            'data': {
                'username': 'test_user',
                'password': 'test_password'
            }
        },
        {
            'name': 'Формат с email',
            'data': {
                'email': 'test@example.com',
                'password': 'test_password'
            }
        },
        {
            'name': 'Формат с grant_type',
            'data': {
                'username': 'test_user',
                'password': 'test_password',
                'grant_type': 'password'
            }
        },
        {
            'name': 'Формат OAuth2',
            'data': {
                'grant_type': 'password',
                'username': 'test_user',
                'password': 'test_password',
                'client_id': 'test_client'
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📝 Тест: {test_case['name']}")
        print(f"   Данные: {json.dumps(test_case['data'], ensure_ascii=False)}")
        
        try:
            response = requests.post(
                f"{API_BASE}/login",
                json=test_case['data'],
                headers={'Content-Type': 'application/json'},
                timeout=TIMEOUT
            )
            
            print(f"   Статус: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ Успех!")
                try:
                    data = response.json()
                    print(f"   Ответ: {json.dumps(data, indent=2, ensure_ascii=False)}")
                except:
                    print("   Ответ не JSON")
            elif response.status_code == 401:
                print("   ✅ Ожидаемая ошибка 401 (неверные учетные данные)")
            elif response.status_code == 400:
                print("   ⚠️  Ошибка 400 (неверный формат)")
                try:
                    error_data = response.json()
                    print(f"   Детали ошибки: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
                except:
                    print("   Детали ошибки не доступны")
            else:
                print(f"   ❓ Неожиданный статус: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Ошибка запроса: {e}")

def test_api_documentation():
    """Попытка получить документацию API"""
    print("\n🔍 Поиск документации API...")
    
    doc_endpoints = [
        '/docs',
        '/redoc',
        '/openapi.json',
        '/swagger.json',
        '/api-docs',
        '/'
    ]
    
    for endpoint in doc_endpoints:
        try:
            response = requests.get(f"{API_BASE}{endpoint}", timeout=TIMEOUT)
            print(f"   {endpoint}: {response.status_code}")
            if response.status_code == 200:
                print(f"   ✅ Документация найдена: {API_BASE}{endpoint}")
        except:
            print(f"   {endpoint}: недоступен")

def test_available_endpoints():
    """Тестирование доступных эндпоинтов"""
    print("\n🔍 Поиск доступных эндпоинтов...")
    
    endpoints = [
        '/login',
        '/auth/login',
        '/token',
        '/auth/token',
        '/user/login',
        '/signin',
        '/authenticate'
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.post(
                f"{API_BASE}{endpoint}",
                json={'test': 'data'},
                headers={'Content-Type': 'application/json'},
                timeout=TIMEOUT
            )
            print(f"   {endpoint}: {response.status_code}")
        except:
            print(f"   {endpoint}: недоступен")

def main():
    """Основная функция"""
    print("🚀 Детальное тестирование API аутентификации")
    print("=" * 60)
    
    # Тест разных форматов
    test_different_formats()
    
    # Поиск документации
    test_api_documentation()
    
    # Поиск эндпоинтов
    test_available_endpoints()
    
    print("\n✅ Тестирование завершено")
    print("\n💡 Следующие шаги:")
    print("   - Проверьте документацию API")
    print("   - Уточните правильный формат данных")
    print("   - Проверьте правильность URL эндпоинта")

if __name__ == "__main__":
    main()


