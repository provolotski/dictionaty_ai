#!/usr/bin/env python3
"""
Скрипт для тестирования аутентификации с реальными учетными данными
"""

import requests
import json
import getpass
import sys

# Настройки API
API_BASE = 'http://172.16.251.170:9090/api/v1/auth'
TIMEOUT = 10

def test_real_login():
    """Тестирование с реальными учетными данными"""
    print("🔐 Тестирование аутентификации с реальными данными")
    print("=" * 50)
    
    # Запрос учетных данных
    username = input("Введите имя пользователя: ").strip()
    if not username:
        print("❌ Имя пользователя не может быть пустым")
        return False
    
    password = getpass.getpass("Введите пароль: ").strip()
    if not password:
        print("❌ Пароль не может быть пустым")
        return False
    
    domain = input("Введите домен (или нажмите Enter для 'default'): ").strip()
    if not domain:
        domain = 'default'
    
    # Подготовка данных
    login_data = {
        'username': username,
        'password': password,
        'domain': domain
    }
    
    print(f"\n📤 Отправка данных на {API_BASE}/login")
    print(f"   Пользователь: {username}")
    print(f"   Домен: {domain}")
    
    try:
        response = requests.post(
            f"{API_BASE}/login",
            json=login_data,
            headers={'Content-Type': 'application/json'},
            timeout=TIMEOUT
        )
        
        print(f"\n📥 Ответ от сервера:")
        print(f"   Статус: {response.status_code}")
        print(f"   Заголовки: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ Аутентификация успешна!")
            try:
                data = response.json()
                print(f"   Access Token: {data.get('access_token', 'Нет')[:20]}...")
                print(f"   Refresh Token: {data.get('refresh_token', 'Нет')[:20]}...")
                print(f"   Полный ответ: {json.dumps(data, indent=2, ensure_ascii=False)}")
                return True
            except Exception as e:
                print(f"   Ошибка парсинга JSON: {e}")
                print(f"   Сырой ответ: {response.text}")
                return False
        else:
            print("❌ Аутентификация не удалась")
            try:
                error_data = response.json()
                print(f"   Ошибка: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                print(f"   Сырой ответ: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Ошибка подключения к API")
        return False
    except requests.exceptions.Timeout:
        print("❌ Таймаут подключения к API")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False

def test_token_validation(access_token):
    """Тестирование валидации токена"""
    print(f"\n🔍 Тестирование валидации токена...")
    
    try:
        response = requests.get(
            f"{API_BASE}/validate",
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=TIMEOUT
        )
        
        print(f"   Статус: {response.status_code}")
        if response.status_code == 200:
            print("✅ Токен валиден")
            return True
        else:
            print("❌ Токен невалиден")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка валидации токена: {e}")
        return False

def main():
    """Основная функция"""
    print("🚀 Тестирование реальной аутентификации")
    print("=" * 60)
    
    # Тест логина
    if test_real_login():
        print("\n✅ Тест аутентификации прошел успешно!")
        print("\n💡 Следующие шаги:")
        print("   - Проверьте форму логина в браузере")
        print("   - Убедитесь, что токены сохраняются в сессии")
        print("   - Проверьте работу защищенных страниц")
    else:
        print("\n❌ Тест аутентификации не прошел")
        print("\n🔧 Возможные решения:")
        print("   - Проверьте правильность учетных данных")
        print("   - Убедитесь, что API сервер работает")
        print("   - Проверьте настройки сети")

if __name__ == "__main__":
    main()



