#!/usr/bin/env python3
"""
Тест веб-формы авторизации
"""

import requests
import json
import time


def test_web_auth():
    """Тест веб-формы авторизации"""
    print("=== ТЕСТ ВЕБ-ФОРМЫ АВТОРИЗАЦИИ ===")
    
    base_url = "http://localhost:8001"
    
    # Тест 1: Проверка доступности страницы логина
    print("\n1. Проверка страницы логина...")
    try:
        response = requests.get(f"{base_url}/accounts/login/", timeout=10)
        print(f"   Статус: {response.status_code}")
        print(f"   Размер: {len(response.content)} байт")
        
        if response.status_code == 200:
            print("   ✅ Страница логина доступна")
        else:
            print(f"   ❌ Страница логина недоступна: {response.status_code}")
            return
    except Exception as e:
        print(f"   ❌ Ошибка доступа к странице логина: {e}")
        return
    
    # Тест 2: Попытка авторизации с реальными учетными данными
    print("\n2. Тест авторизации с реальными учетными данными...")
    
    login_data = {
        'username': 'admin_db_app',
        'password': '47khTCzG',
        'domain': 'belstat',
        'csrfmiddlewaretoken': 'test_token'  # В реальном тесте нужно получить CSRF токен
    }
    
    try:
        # Сначала получаем CSRF токен
        session = requests.Session()
        response = session.get(f"{base_url}/accounts/login/")
        
        # Извлекаем CSRF токен из HTML (упрощенно)
        csrf_token = None
        if 'csrfmiddlewaretoken' in response.text:
            import re
            match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', response.text)
            if match:
                csrf_token = match.group(1)
                print(f"   CSRF токен получен: {csrf_token[:20]}...")
        
        if csrf_token:
            login_data['csrfmiddlewaretoken'] = csrf_token
        
        # Отправляем POST запрос на авторизацию
        response = session.post(
            f"{base_url}/accounts/login/",
            data=login_data,
            headers={'Referer': f"{base_url}/accounts/login/"},
            allow_redirects=False,
            timeout=30
        )
        
        print(f"   Статус ответа: {response.status_code}")
        print(f"   Заголовки: {dict(response.headers)}")
        
        if response.status_code == 302:  # Редирект при успешной авторизации
            redirect_url = response.headers.get('Location', '')
            print(f"   ✅ Успешная авторизация, редирект на: {redirect_url}")
            
            # Проверяем, что в сессии есть токены
            if 'access' in session.cookies or 'access_token' in session.cookies:
                print("   ✅ Токены сохранены в сессии")
            else:
                print("   ⚠️  Токены не найдены в сессии")
                
        elif response.status_code == 200:
            # Проверяем содержимое ответа на наличие ошибок
            if 'error' in response.text.lower() or 'неверные учетные данные' in response.text.lower():
                print("   ❌ Ошибка авторизации (неверные учетные данные)")
            else:
                print("   ⚠️  Неожиданный ответ (статус 200)")
                
        else:
            print(f"   ❌ Неожиданный статус: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Ошибка при тестировании авторизации: {e}")
        import traceback
        traceback.print_exc()
    
    # Тест 3: Проверка с неверными учетными данными
    print("\n3. Тест с неверными учетными данными...")
    
    wrong_login_data = {
        'username': 'wrong_user',
        'password': 'wrong_password',
        'domain': 'wrong_domain',
        'csrfmiddlewaretoken': csrf_token if 'csrf_token' in locals() else 'test_token'
    }
    
    try:
        response = session.post(
            f"{base_url}/accounts/login/",
            data=wrong_login_data,
            headers={'Referer': f"{base_url}/accounts/login/"},
            allow_redirects=False,
            timeout=30
        )
        
        print(f"   Статус ответа: {response.status_code}")
        
        if response.status_code == 200:
            if 'error' in response.text.lower() or 'неверные учетные данные' in response.text.lower():
                print("   ✅ Ожидаемая ошибка авторизации получена")
            else:
                print("   ⚠️  Неожиданный ответ при неверных учетных данных")
        else:
            print(f"   ⚠️  Неожиданный статус: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Ошибка при тестировании с неверными данными: {e}")
    
    print("\n=== ТЕСТИРОВАНИЕ ЗАВЕРШЕНО ===")


if __name__ == '__main__':
    test_web_auth()
