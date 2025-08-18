#!/usr/bin/env python3
"""
Тестовый скрипт для проверки формы логина с полем домена
"""

import requests
import json
import sys

# Настройки API
API_BASE = 'http://172.16.251.170:9090/api/v1/auth'
TIMEOUT = 10

def test_form_with_domain():
    """Тестирование формы с полем домена"""
    print("🔍 Тестирование формы логина с полем домена")
    print("=" * 60)
    
    test_cases = [
        {
            'name': 'Стандартный домен',
            'data': {
                'username': 'test_user',
                'password': 'test_password',
                'domain': 'default'
            }
        },
        {
            'name': 'Кастомный домен',
            'data': {
                'username': 'test_user',
                'password': 'test_password',
                'domain': 'belstat.local'
            }
        },
        {
            'name': 'Пустой домен',
            'data': {
                'username': 'test_user',
                'password': 'test_password',
                'domain': ''
            }
        },
        {
            'name': 'Домен с пробелами',
            'data': {
                'username': 'test_user',
                'password': 'test_password',
                'domain': '  default  '
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
            elif response.status_code == 422:
                print("   ⚠️  Ошибка 422 (неверные данные)")
                try:
                    error_data = response.json()
                    print(f"   Детали ошибки: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
                except:
                    print("   Детали ошибки не доступны")
            else:
                print(f"   ❓ Неожиданный статус: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Ошибка запроса: {e}")

def test_django_form():
    """Тестирование Django формы"""
    print("\n🔍 Тестирование Django формы")
    print("=" * 40)
    
    # Имитируем данные Django формы
    form_data = {
        'username': 'test_user',
        'password': 'test_password',
        'domain': 'default',
        'remember_me': 'on',
        'csrfmiddlewaretoken': 'test_token'
    }
    
    print(f"Данные формы: {json.dumps(form_data, ensure_ascii=False)}")
    print("✅ Django форма готова к тестированию")

def main():
    """Основная функция"""
    print("🚀 Тестирование формы логина с полем домена")
    print("=" * 70)
    
    # Тест API с доменом
    test_form_with_domain()
    
    # Тест Django формы
    test_django_form()
    
    print("\n✅ Тестирование завершено")
    print("\n📋 Проверьте в браузере:")
    print("   - http://localhost:8001/accounts/login/")
    print("   - Поле домена должно быть видимым")
    print("   - Значение по умолчанию: 'default'")
    print("   - Валидация должна работать")

if __name__ == "__main__":
    main()




